import pika
import json
from time import sleep
import threading

class TrucoClient:
    def __init__(self, queues, nickname):
        self.queues = queues
        self.nickname = nickname
        self.myTeam = None
        self.timeA = None
        self.timeB = None
        self.mycards = None
        self.vira = None

        #cria a conexão
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', '5672'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queues[0]) #coordinator vai ler e os clientes vão publicar
        self.channel.queue_declare(queue=self.queues[1]) #coordinator vai ler e os clientes vão publicar
    
        #listener
        # self.channel.exchange_declare(exchange=self.queues[1], exchange_type='fanout')
        # self.channel.queue_declare(queue=self.queues[1]) #coordinator vai publicar e os clientes vão ler

        # listener fanout
        self.channel.exchange_declare(exchange=self.queues[1], exchange_type='fanout')  # Declara uma nova troca do tipo "fanout"
        result = self.channel.queue_declare(queue='', exclusive=True)                   # Cria uma fila exclusiva para cada cliente
        self.bindedQueue = queue_name = result.method.queue                                                # Cria uma fila exclusiva para cada cliente
        self.channel.queue_bind(exchange=self.queues[1], queue=self.bindedQueue)              # Vincula a fila à troca do tipo "fanout"
        
        #manda o checkin pro servidor
        # print('publicando checkin:', self.queues[0])
        self.channel.basic_publish(exchange='', routing_key=self.queues[0], body=json.dumps({'cmd': 'checkin', 'nickname': nickname}))
            
        try:
            # print('lendo:', queue_name)
            print('=============================== Iniciando Mesa')
            self.channel.basic_consume(queue_name, self.gameCoordinator) #, no_ack=True) ### se usar auto_ack=true nao precisa do ack dentro do classify
            self.channel.start_consuming()
        except:
            self.channel.stop_consuming()
            self.channel.queue_unbind(exchange=self.queues[1], queue=self.bindedQueue)
            self.connection.close()
            print('Saindo...')
    #end play

    def publish(self, msg):
        # print('DEBUG pub: ', msg)
        self.channel.basic_publish(exchange='', routing_key=self.queues[0], body=json.dumps(msg))
    #end

    def play(self, msg, trucoRes=False):
        #pode jogar uma carta, pedir truco, aumentar, aceitar, correr
        print(f'\nSUA VEZ! Digite sua jogada:')
        print(' * Cartas:' + ' '.join([f'({i}){card}' for i, card in enumerate(self.mycards)]) + f' - Vira: [{self.vira}]')
        
        #opções
        options = ''

        if trucoRes == 0: # se nao for resposta
            options += 'carta <index> / '

            if msg['truco'] == 0: #se nao tiver trucado
                options += 'truco / '
            
            if msg['truco'] < 6 and msg['trucoTeam'] != self.myTeam:
                options += 'seis / '


        if trucoRes == 1: # se for resposta de um truco
            options += 'aceitar / seis / '
        
        if trucoRes == 2: # se for resposta de um seis
            options += 'aceitar / '
        
        #caso tiver trucado, aparecer aviso
        if msg['truco'] != 0:            
            print(f" * TRUCADO: {msg['truco']}")

        print(f' * Opções: {options}correr')

        #comandos
        while(True):
            jogada = input('> ').split(' ')

            #correr é sempre uma opção
            if jogada[0] == 'correr':
                self.publish({'cmd': 'play', 'type': 'withdraw', 'nickname': self.nickname})
                break
            
            #carta somente quando nao for resposta de truco
            elif not trucoRes and jogada[0] == 'carta':
                if len(jogada) < 2:
                    print("-- Erro: Tente: 'carta <index>'")
                    continue
                index = int(jogada[1]) % len(self.mycards)
                self.publish({ 'cmd': 'play', 'type': 'card', 'nickname': self.nickname, 'cardindex': index})
                self.mycards.pop(index)
                break
            
            #truco somente quando não está trucado
            elif not msg['truco'] and jogada[0] == 'truco':
                self.publish({'cmd': 'play', 'type': 'truco', 'nickname': self.nickname})
                break
            
            #aceitar somente quando é uma resposta de um truco ou seis
            elif trucoRes and jogada[0] == 'aceitar':
                self.publish({'cmd': 'play', 'type': 'accept', 'nickname': self.nickname, 'direction': msg['direction']})
                break
            
            # #seis somente quando está trucado, menor que 6(2)e não foi meu time que trucou
            elif msg['truco'] < 6 and msg['trucoTeam'] != self.myTeam and jogada[0] == 'seis':
            #     direction = 'tras' if trucoRes == 1 else 'frente'
                self.publish({'cmd': 'play', 'type': 'seis', 'inResponse': trucoRes, 'nickname': self.nickname})
                break

            else:
                print('-- Erro: Jogada incorreta')

        print(' * Jogada concluída')
        #end

    def gameCoordinator(self, ch, method_frame, header_frame, body):
        msg = json.loads(body)
        # print('DEBUG read: ', msg)

        match msg['cmd']:
            case 'checkin':
                if msg['nickname'] == self.nickname:
                    self.myTeam = msg['team']
                print(f"{msg['nickname']} (Team {msg['team']}) ({msg['checkin-total']}/4) check-in")

            case 'start-game':
                self.timeA = msg['timeA']
                self.timeB = msg['timeB']
                print(f"JOGO INICIANDO: {self.timeA} {msg['scoreboard'][0]} x {msg['scoreboard'][1]} {self.timeB}")

            case 'start-round':
                print('\n=================================================')
                print(f"ROUND INICIANDO: {self.timeA} {msg['scoreboard'][0]} x {msg['scoreboard'][1]} {self.timeB}")
                print(f"VIRA: {msg['vira']}")
                self.vira = msg['vira']

            case 'draw':
                if msg['nickname'] == self.nickname:
                    self.mycards = msg['cards']
                    print(f"MINHAS CARTAS: {self.mycards}")
            
            case 'start-mao':
                print('-------------------------------------------------')
                print(f"MÃO INICIANDO: Ordem de jogadas {msg['order']} / Set {msg['maowinners']}")
                if msg['nextplayer'] == self.nickname:
                    self.play(msg)
            
            case 'play':
                if msg['type'] == 'card':
                    print(f" ~ Mesa: {msg['cardsInPlay']} -- {msg['nickname']} jogou [{msg['card']}]")
                    if msg['nextplayer'] == self.nickname:
                        self.play(msg)
                
                elif msg['type'] == 'withdraw':
                    print(f" ~ {msg['nickname']} correu!")

                elif msg['type'] == 'truco':
                    print(f" ~ {msg['nickname']}: TRUUCOOO!")
                    if msg['nextplayer'] == self.nickname:
                        self.play(msg, trucoRes=1)

                elif msg['type'] == 'accept':
                    print(f" ~ {msg['nickname']}: DEESCEEE!")
                    if msg['nextplayer'] == self.nickname:
                        self.play(msg)

                elif msg['type'] == 'seis':
                    print(f" ~ {msg['nickname']}: SEEIISSS!")
                    if msg['nextplayer'] == self.nickname:
                        self.play(msg, trucoRes=2)
            
            case 'result-mao':
                print(f"\nMÃO FINALIZADA: Vencedor: Time {msg['winnerTeam']} com a carta {msg['winnerPlayer']} / Set {msg['maowinners']}")
            
            case 'result-round':
                print(f"\nROUND FINALIZADO: Vencedor: Time {msg['winnerTeam']}!!!")

            case 'result-game':
                print(f"\nJOGO FINALIZADO! VENCEDOR: TIME {msg['winnerTeam']} / PLACAR: {msg['scoreboard'][0]} x {msg['scoreboard'][1]}")
                if msg['winnerTeam'] == self.myTeam:
                    print('PARABÉNS!!! VOCÊ GANHOU!')
                else:
                    print("Você perdeu :(")

            case 'end-game':
                print('Finalizando sessão...')
                self.channel.stop_consuming()
            
            case 'exit':
                if msg['nickname'] == self.nickname:
                    self.myTeam = msg['team']
                print(f"{msg['nickname']} (Team {msg['team']}) deixou a mesa.")
#end game