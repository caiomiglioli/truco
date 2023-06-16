#utils
from concurrent import futures

#rpc protobuf
import grpc
import truco_pb2
import truco_pb2_grpc
from google.protobuf.json_format import MessageToJson


class TrucoServicer(truco_pb2_grpc.TrucoServicer):
    def __init__(self):
        self.activeTables = []
    #end init
    
    # def signin(self, request, context):
    #     pass

    # def signout(self, request, context):
    #     pass

    def showTables(self, request, context):
        for table in self.activeTables:
            yield self.tableToProtobuf(table)

    def createNewTable(self, request, context):
        pass

    def joinTable(self, request, context):
        pass

    def exitTable(self, request, context):
        pass
    #end functions

    #start auxiliaries
    def tableToProtobuf(table):
        t = truco_pb2.Table()
        t.name = table.name
        t.teamA.extend(table.players[0:2])
        t.teamB.extend(table.players[2:4])
        t.scoreboard.extend(table.scoreboard)
        return t
    #end aux
#end server

def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    truco_pb2_grpc.add_TrucoServicer_to_server(TrucoServicer(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve('7777')