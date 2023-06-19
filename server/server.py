#utils
from concurrent import futures

#rpc protobuf
import grpc
import truco_pb2
import truco_pb2_grpc
from google.protobuf.json_format import MessageToJson

from game import Truco

class TrucoServicer(truco_pb2_grpc.TrucoServicer):
    def __init__(self):
        self.activeTables = dict()
    #end init

    # ------------------------------------------------
    def showTables(self, request, context):
        for _, table in self.activeTables.items():
            yield self.tableToProtobuf(table)
    #end showtables

    # ------------------------------------------------
    def createNewTable(self, request, context):
        #checar se ja existe uma mesa com tablename
        if self.activeTables.get(request.tablename):
            return truco_pb2.QueryReply(status = False)

        #criar mesa
        table = Truco(request.tablename)
        self.activeTables[request.tablename] = table
        return truco_pb2.QueryReply(status = True)
    #end createnewtable

    # ------------------------------------------------
    def joinTable(self, request, context):
        table = self.activeTables.get(request.tablename)

        #checar se existe uma mesa com tablename
        if not table:
            return truco_pb2.QueryReply(status = False)
        
        #checar se há vagas
        status = table.join(request.nickname, request.team)
        return truco_pb2.QueryReply(status = True if status else False)            
    #end jointable

    # ------------------------------------------------
    def exitTable(self, request, context):
        table = self.activeTables.get(request.tablename)

        #checar se existe uma mesa com tablename
        if not table:
            return truco_pb2.QueryReply(status = False)
        
        #checar se há vagas
        status = table.exit(request.nickname)
        return truco_pb2.QueryReply(status = True if status else False)   
    #end functions

    # ==================================================
    #start auxiliaries
    def tableToProtobuf(self, table):
        t = truco_pb2.Table()
        tt = table.abstract()
        print(tt)
        t.name = tt['name']
        t.team_A.extend(tt['TeamA'])
        t.team_B.extend(tt['TeamB'])
        # t.scoreboard.extend(table.scoreboard)
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