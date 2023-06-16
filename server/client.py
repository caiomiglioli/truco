
import asyncio
import grpc
import truco_pb2 as proto
import truco_pb2_grpc as rpc

async def showTables(stub):
    tables = stub.showTables()

    async for table in tables:
        print('=============================== table')
        print(table)
    
    print('end')
#end join lobby


async def main():
    async with grpc.aio.insecure_channel('localhost:7777') as channel:
        stub = rpc.TrucoStub(channel)

        print("-------------- showTables --------------")
        await showTables(stub)
    #end with
#end main

if __name__ == '__main__':
    asyncio.run(main())