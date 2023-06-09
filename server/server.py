#utils
from concurrent import futures

#rpc protobuf
import grpc
import truco_pb2
import truco_pb2_grpc
from google.protobuf.json_format import MessageToJson

from game import TrucoServer

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
            raise Exception("DuplicatedName")
            # return truco_pb2.QueryReply(status = False)

        #criar mesa
        table = TrucoServer(request.tablename)
        self.activeTables[request.tablename] = table
        return truco_pb2.QueryReply(status = True)
    #end createnewtable

    # ------------------------------------------------
    def joinTable(self, request, context):
        table = self.activeTables.get(request.tablename)

        #checar se existe uma mesa com tablename
        if not table:
            raise Exception("NotFound")
        
        #checar se há vagas
        status = table.join(request.nickname, request.team)

        if not status[0]:            
            raise Exception(status[1])
        
        return truco_pb2.QueryReply(status=True, cmdQueue=status[1][0], cliQueue=status[1][1])         
    #end jointable

    # ------------------------------------------------
    def exitTable(self, request, context):
        table = self.activeTables.get(request.tablename)

        #checar se existe uma mesa com tablename
        if not table:
            return truco_pb2.QueryReply(status = False)
        
        #checar se há vagas
        status = table.exit(request.nickname)
        if status == 'delete':
            obj = self.activeTables[request.tablename]
            del obj
        return truco_pb2.QueryReply(status = True if status else False)   
    #end functions

    # ==================================================
    #start auxiliaries
    def tableToProtobuf(self, table):
        t = truco_pb2.Table()
        tt = table.abstract()
        print(tt)
        t.name = tt['name']
        t.init = tt['init']
        t.team_A.extend(tt['TeamA'])
        t.team_B.extend(tt['TeamB'])
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