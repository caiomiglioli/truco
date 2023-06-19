import pika
import threading

class Truco:
    def __init__(self, tablename):
        self.name = tablename
        self.players = {'A': [], 'B': []}

        # Game
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', '5672'))
        channel = self.connection.channel()
        channel.queue_declare(queue=tablename+'-commands') #coordinator vai ler e os clientes vão publicar
        channel.queue_declare(queue=tablename+'-clients') #coordinator vai publicar e os clientes vão ler
        # channel.queue_delete(queue='hello')
        thread = threading.Thread(target=self.gameCoordinator)
        thread.start()
    #end init
    
    def abstract(self):
        return { 'name': self.name, 'TeamA': self.players['A'], 'TeamB': self.players['B']}
    
    def join(self, nickname, team):
        #se o time ja tem jogadores o suficiente
        if len(self.players[team]) >= 2:
            return False
        
        #se ja tem um jogador com esse nickname na partida
        if nickname in (self.players['A'] + self.players['B']):
            return False
        
        #adicionar jogadores na partida
        self.players[team].append(nickname)
        return True

    def exit(self, nickname):
        if nickname in self.players['A']: self.players['A'].remove(nickname)
        elif nickname in self.players['B']: self.players['B'].remove(nickname)
        else: return False
        return True


    def coordenate(self, ch, method_frame, header_frame, body):
        pass

    def gameCoordinator(self):
        self.placar = [0, 0]
        # self.truco = False
        self.colector.basic_consume(self.name+'-commands', self.coordenate, auto_ack=True) ### se usar auto_ack=true nao precisa do ack dentro do classify
        self.colector.start_consuming()
