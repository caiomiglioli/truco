import asyncio
import grpc
import truco_pb2 as proto
import truco_pb2_grpc as rpc

from game import TrucoClient

async def showTables(stub):
    q = proto.Query()
    tables = stub.showTables(q)

    async for table in tables:
        print('=============================== table')
        print(table)
    
    print('end')
#end join lobby

async def createTable(stub, tablename):
    q = proto.Query(tablename = tablename)
    qReply = await stub.createNewTable(q)
    print(qReply.status)
#end create

async def joinTable(stub, tablename, nickname, team):
    q = proto.Query(tablename=tablename, nickname=nickname, team=team)
    qReply = await stub.joinTable(q)
    if qReply.status:
        return (qReply.cmdQueue, qReply.cliQueue)
    return None
#end join

async def exitTable(stub, tablename, nickname):
    q = proto.Query(tablename=tablename, nickname=nickname)
    qReply = await stub.exitTable(q)
    print(qReply.status)
#end join

# ------------------------------------------------------------------------
async def main():
    nickname = 'p1'
    team = 'A'

    async with grpc.aio.insecure_channel('localhost:7777') as channel:
        stub = rpc.TrucoStub(channel)

        print("-------------- createTable --------------")
        await createTable(stub, 'Teste')

        print("-------------- showTables --------------")
        await showTables(stub)

        print("-------------- joinTable --------------")
        queues = await joinTable(stub, 'Teste', nickname, team)

    print("-------------- Play --------------")
    client = TrucoClient(queues, nickname, team)

        # print("-------------- exitTable --------------")
        # await exitTable(stub, 'Teste', 'player1')
    #end with
#end main

if __name__ == '__main__':
    asyncio.run(main())