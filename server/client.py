import asyncio
import grpc
import truco_pb2 as proto
import truco_pb2_grpc as rpc

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
    print(qReply.status)
#end join

async def exitTable(stub, tablename, nickname):
    q = proto.Query(tablename=tablename, nickname=nickname)
    qReply = await stub.exitTable(q)
    print(qReply.status)
#end join


async def main():
    async with grpc.aio.insecure_channel('localhost:7777') as channel:
        stub = rpc.TrucoStub(channel)

        print("-------------- showTables --------------")
        await showTables(stub)

        print("-------------- createTable --------------")
        await createTable(stub, 'Teste')

        print("-------------- joinTable --------------")
        await joinTable(stub, 'Teste', 'player1', 'A')

        print("-------------- showTables --------------")
        await showTables(stub)

        print("-------------- exitTable --------------")
        await exitTable(stub, 'Teste', 'player1')

        print("-------------- showTables --------------")
        await showTables(stub)
    #end with
#end main

if __name__ == '__main__':
    asyncio.run(main())