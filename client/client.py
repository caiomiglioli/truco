import asyncio
import grpc
import truco_pb2 as proto
import truco_pb2_grpc as rpc

from game import TrucoClient

async def showTables(stub):
    q = proto.Query()
    tables = stub.showTables(q)

    print('=============================== Mesas')
    async for t in tables:
        print(f'{t.name} ({t.init}): {t.team_A} {t.scoreboard[0]} x {t.scoreboard[1]} {t.team_B}')
    print()
#end join lobby

async def createTable(stub, tablename):
    try:
        q = proto.Query(tablename = tablename)
        qReply = await stub.createNewTable(q)
        if qReply.status:
            print(f"Mesa '{tablename}' criada com sucesso!")
    except Exception as e:
        erro = e.details().split(' ')[-1]  # Detalhes do erro
        if erro == 'DuplicatedName':
            erro = 'Nome duplicado.'

        print(f'Não foi possível criar a mesa {tablename}: {erro}')        
#end create

async def joinTable(stub, tablename, nickname, team):
    try:
        q = proto.Query(tablename=tablename, nickname=nickname, team=team)
        qReply = await stub.joinTable(q)
        return (qReply.cmdQueue, qReply.cliQueue)
    except Exception as e:
        erro = e.details().split(' ')[-1]  # Detalhes do erro
        if erro == 'DuplicatedName':    erro = 'Nome duplicado.'
        elif erro == 'NotFound':        erro = 'Mesa não encontrada.'
        elif erro == 'FullTeam':        erro = 'Time já completo.'
        elif erro == 'GameInitiated':   erro = 'Jogo já inicializado.'

        print(f'Não foi possível entrar na mesa {tablename}: {erro}')  
#end join

async def exitTable(stub, tablename, nickname):
    q = proto.Query(tablename=tablename, nickname=nickname)
    qReply = await stub.exitTable(q)
    print(qReply.status)
#end join


def comandosDisponiveis():
    print(' * meunome <nome>')
    print(' * mesas')
    print(' * criar <nome-da-mesa>')
    print(' * entrar <nome-da-mesa> <A ou B>')
    print(' * sair')
#end cmds

# ------------------------------------------------------------------------
async def main():
    # nickname = 'p1'
    # team = 'A'

    async with grpc.aio.insecure_channel('localhost:7777') as channel:
        stub = rpc.TrucoStub(channel)
        nickname = None

        print('~~~~~~~~ TRUCO ~~~~~~~~')
        print('Comandos disponíveis:')
        comandosDisponiveis()
        
        while True:
            cmd = input(f'({nickname}) > ').split(' ')
            
            if cmd[0] == 'mesas':
                await showTables(stub)
            #end listar

            elif cmd[0] == 'criar':
                if len(cmd) < 1:
                    print('Comando incompleto! Tente "criar <nome-da-mesa>"')
                    continue
                await createTable(stub, cmd[1])
            #end criar

            elif cmd[0] == 'entrar':
                if len(cmd) < 2:
                    print('Comando incompleto! Tente "entrar <nome-da-mesa> <A ou B>"')
                    continue

                if cmd[2] != 'A' and cmd[2] != 'B':
                    print("Erro: O time deve ser 'A' ou 'B'!")
                    continue

                if not nickname:
                    print('Não é possível entrar em uma mesa sem inserir um nome! Insira seu nome usando: "meunome <nome>"')
                    continue

                queues = await joinTable(stub, cmd[1], nickname, cmd[2])
                if queues:
                    try:
                        client = TrucoClient(queues, nickname)
                    except:
                        print('Partida abandonada...')
                    finally:
                        await exitTable(stub, cmd[1], nickname)
            #end entrar

            elif cmd[0] == 'meunome':
                if len(cmd) < 1:
                    print('Comando incompleto! Tente "meunome <nome>"')
                    continue
                nickname = cmd[1]
            #end meunome
                
            elif cmd[0] == 'sair':
                break
                
            else:
                print('Comando inválido! Comandos disponíveis:')
                comandosDisponiveis()
        #end while
    #end with
#end main

if __name__ == '__main__':
    asyncio.run(main())