import pika
import json
import random
import threading

class TrucoServer:
    def __init__(self, tablename):
        #table info
        self.tablename = tablename
        self.baralho = sum([[v+n for n in ['♣','♥','♠','♦']] for v in ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']], [])
        # self.playerHash = dict()

        #game info
        self.players = {'A': [], 'B': []}
        self.checkin = 0
        self.scoreboard = [0, 0]

        #round info
        self.vira = None
        
        #mao info
        self.truco = 0
        self.playOrder = None
        self.playCount = 0
        self.lastWinner = 0
        self.maoWinners = 0
        self.nextplayer = None
        self.cardsInPlay = None

        #Game Listener
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', '5672'))
        self.channel = self.connection.channel()
        self.channel.queue_delete(queue=tablename+'-commands')
        self.channel.queue_declare(queue=tablename+'-commands') #coordinator vai ler e os clientes vão publicar
        self.channel.queue_delete(queue=tablename+'-clients')
        # self.channel.queue_declare(queue=tablename+'-clients') #coordinator vai publicar e os clientes vão ler
        self.channel.exchange_declare(exchange=tablename+'-clients', exchange_type='fanout')

        # channel.queue_delete(queue='hello')
        thread = threading.Thread(target=self.listen)
        thread.start()
    #end init
    
    def abstract(self):
        return { 'name': self.tablename, 'TeamA': self.players['A'], 'TeamB': self.players['B']}
    #end abstract
    
    def join(self, nickname, team):
        #se o time ja tem jogadores o suficiente
        if len(self.players[team]) >= 2:
            return False
        
        #se ja tem um jogador com esse nickname na partida
        if nickname in (self.players['A'] + self.players['B']):
            return False
        
        #adicionar jogadores na partida
        self.players[team].append(nickname)
        return (self.tablename+'-commands', self.tablename+'-clients') #, hash)
    #end join

    def exit(self, nickname):
        if nickname in self.players['A']: self.players['A'].remove(nickname)
        elif nickname in self.players['B']: self.players['B'].remove(nickname)
        else: return False
        self.checkin -= 1
        return True
    #end exit

    # =================================================================

    def startGame(self):
        self.playOrder = [self.players['A'][0], self.players['B'][0], self.players['A'][1], self.players['B'][1]]
        self.cards = dict()
        self.scoreboard = [0, 0]
        self.lastWinner = 0
        self.truco = 0
        self.vira = None
        self.publish({'cmd': 'start-game', 'scoreboard': self.scoreboard, 'timeA': self.players['A'], 'timeB': self.players['B']})
    #end

    def startRound(self):
        # vira
        bar = self.baralho
        random.shuffle(bar)
        self.vira = bar.pop()
        
        #start round
        self.publish({ 'cmd': 'start-round', 'scoreboard': self.scoreboard, 'vira': self.vira})
        self.maoWinners = []

        #draw
        for name in (self.players['A'] + self.players['B']):
            cards = [bar.pop() for _ in range(3)]
            self.cards[name] = cards
            self.publish({'cmd': 'draw', 'nickname': name, 'cards': cards})
    #end

    def startMao(self):
        self.playOrder = self.playOrder[self.lastWinner:] + self.playOrder[:self.lastWinner]
        self.playCount = 0 #sempre vai ser 0, pois a ordem já é mudada no playorder --- Contador de cont
        self.nextplayer = self.playOrder[self.playCount]
        self.cardsInPlay = []
        self.publish({ 'cmd': 'start-mao', 'order': self.playOrder, 'maowinners': self.maoWinners, 'nextplayer': self.nextplayer})
    #end

    # --------------------------------------------------------------

    def throwCard(self, msg):
        card = self.cards[msg['nickname']].pop(msg['cardindex'])
        self.cardsInPlay.append((card, msg['nickname']))
        self.playCount += 1

        if self.playCount < 4:
            self.nextplayer = self.playOrder[self.playCount]
        else:
            self.nextplayer = 'finish'

        cip = [c[0] for c in self.cardsInPlay]
        self.publish({ 'cmd': 'play', 'type': 'card', 'nickname': msg['nickname'], 'card': card, 'nextplayer': self.nextplayer, 'cardsInPlay': cip})
    
        if self.nextplayer == 'finish':
            self.checkMaoWinner() #precisa ser o ultimo, se nao nao manda o print de cima na ordem certa
    #end

    def checkMaoWinner(self):
        ordemNum = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        ordemNaipe = ['♦','♠','♥', '♣']
        manilha = ordemNum.pop( (ordemNum.index(self.vira[0]) + 1) %  10 )
        ordemNum.append(manilha)

        #descobrir quem é o vencedor
        #index, quanto maior, mais forte
        idx, maiorNum, maiorNaipe = 0, 0, 0
        for i, c in enumerate(self.cardsInPlay):
            num, naipe = ordemNum.index(c[0][0]), ordemNaipe.index(c[0][1])
            #se a carta for maior
            if num > maiorNum:
                idx, maiorNum, maiorNaipe = i, num, naipe
            #se a carta for igual, entao olha o naipe
            elif num == maiorNum:
                if naipe > maiorNaipe:
                    idx, maiorNum, maiorNaipe = i, num, naipe

        
        #descobrir qual time é o winner:
        winnerPlayer = self.cardsInPlay[idx] # [0] = carta, [1] = nickname
        self.lastWinner = self.playOrder.index(winnerPlayer[1]) #last winner é o index do playorder que vai iniciar o proximo jogo

        winnerTeam = 'A' if winnerPlayer[1] in self.players['A'] else 'B'
        self.maoWinners.append(winnerTeam) #define a lista de winners pra saber quem ganha
       
        self.publish({'cmd': 'result-mao', 'winnerTeam': winnerTeam, 'winnerPlayer': winnerPlayer, 'maowinners': self.maoWinners})

        # checar se ganhou o round
        if len(self.maoWinners) >= 2:
            #add points to winner:
            # if winnerTeam == 'A':
            #     self.scoreboard[0] += 1
            # else:
            #     self.scoreboard[1] += 1
            pass
        else:
            self.startMao()
    #end check

    # =================================================================
    
    def publish(self, msg):
        self.channel.basic_publish(exchange=self.tablename+'-clients', routing_key=self.tablename+'-clients', body=json.dumps(msg))
    #end

    def gameCoordinator(self, ch, method_frame, header_frame, body):
        """
        body = {
            cmd: checkin / play / truco / accept / deny
            card: (carta)
            nickname: (nickname)
        }"""
        msg = json.loads(body)

        match msg['cmd']:
            case 'checkin':
                self.checkin += 1
                print(f'{self.tablename}: {msg["nickname"]} check-in ({self.checkin}/4)\n')
                self.publish({'cmd': 'checkin', 'nickname': msg['nickname'], 'checkin-total': self.checkin})

                if self.checkin == 4:
                    self.startGame()
                    self.startRound()
                    self.startMao()
            #end checkin

            case 'play':
                if msg['type'] == 'card':
                    self.throwCard(msg)
            #end play
    #end

    def listen(self):
        # self.truco = False
        self.channel.basic_consume(self.tablename+'-commands', self.gameCoordinator, auto_ack=True) ### se usar auto_ack=true nao precisa do ack dentro do classify
        self.channel.start_consuming()
