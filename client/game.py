import pika
import json

import threading

class TrucoClient:
    def __init__(self, queues, nickname, team):
        self.queues = queues
        self.nickname = nickname
        self.myTeam = team
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
        queue_name = result.method.queue                                                # Cria uma fila exclusiva para cada cliente
        self.channel.queue_bind(exchange=self.queues[1], queue=queue_name)              # Vincula a fila à troca do tipo "fanout"
        
        #manda o checkin pro servidor
        print('publicando checkin:', self.queues[0])
        self.channel.basic_publish(exchange='', routing_key=self.queues[0], body=json.dumps({'cmd': 'checkin', 'nickname': nickname}))
        
        print('lendo:', queue_name)
        self.channel.basic_consume(queue_name, self.gameCoordinator) #, no_ack=True) ### se usar auto_ack=true nao precisa do ack dentro do classify
        self.channel.start_consuming()
    #end play

    def publish(self, msg):
        print('DEBUG pub: ', msg)
        self.channel.basic_publish(exchange='', routing_key=self.queues[0], body=json.dumps(msg))
    #end

    def play(self):
        #pode jogar uma carta, pedir truco, aumentar, aceitar, correr
        print(f'SUA VEZ! Digite sua jogada:')
        print(' * Cartas:' + ' '.join([f'({i}){card}' for i, card in enumerate(self.mycards)]) + f' - Vira: [{self.vira}]')
        print(' * Opções: <carta (index)> / ')

        while(True):
            jogada = input().split(' ')

            if jogada[0] == 'carta':
                if len(jogada) < 2:
                    print("-- Erro: Tente: 'carta <index>'")
                    continue
                index = int(jogada[1]) if int(jogada[1]) >= 0 and int(jogada[1]) < len(self.mycards) else -1
                self.publish({ 'cmd': 'play', 'type': 'card', 'nickname': self.nickname, 'cardindex': index})
                self.mycards.pop(index)
                break
            
            else:
                print('-- Erro: Jogada incorreta')

        print(' * Jogada concluída')
        #end

    def gameCoordinator(self, ch, method_frame, header_frame, body):
        msg = json.loads(body)
        print('DEBUG read: ', msg)

        match msg['cmd']:
            case 'checkin':
                print(f"{msg['nickname']} ({msg['checkin-total']}/4) check-in")

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
                    self.play()
            
            case 'play':
                print(f" ~ Mesa: {msg['cardsInPlay']} -- {msg['nickname']} jogou [{msg['card']}]")
                if msg['nextplayer'] == self.nickname:
                    self.play()
            
            case 'result-mao':
                print(f"MÃO FINALIZADA: Vencedor: Time {msg['winnerTeam']} com a carta {msg['winnerPlayer']} / Set {msg['maowinners']}")
#end game