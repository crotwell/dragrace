import simpleDali
import simpleMiniseed
import asyncio
import logging
from datetime import datetime, timedelta
from array import array
import jwt

logging.basicConfig(level=logging.DEBUG)

host = "129.252.35.36"
port = 15003
port = 15005
#host = "129.252.35.20"
#port = 6383
uri = "wss://www.seis.sc.edu/dragracews/datalink"

programname="simpleDali"
username="dragrace"
processid=0
architecture="python"

def encode_auth_token(user_id, secretKey):
    """
    Generates the Auth Token
    :return: string
    """
    payload = {
        'exp': datetime.utcnow() + timedelta(days=0, seconds=5),
        'iat': datetime.utcnow(),
        'sub': user_id,
        'wpat': 'XX_.*/MSEED'
    }
    encoded = jwt.encode(
        payload,
        secretKey,
        algorithm='HS256'
    )
    decoded = jwt.decode(encoded, secretKey, algotithms='HS256')
    print("decode: {}".format(decoded))
    return encoded

def doTest(loop):
    dali = simpleDali.SocketDataLink(host, port)
    #dali = simpleDali.WebSocketDataLink(uri, verbose=True)
    idTask = loop.create_task(dali.id(programname, username, processid, architecture))
    loop.run_until_complete(idTask)
    serverId = idTask.result()
    #serverId = await dali.id(programname, username, processid, architecture)
    print("Resp: {}".format(serverId))
    #serverInfo = yield from dali.info("STATUS")
    #print("Info: {} ".format(serverInfo.message))
    #serverInfo = yield from dali.info("STREAMS")
    #print("Info: {} ".format(serverInfo.message))
    # hptime = "1551313181711158"
    # print("Position after: {}  {:d}".format(hptime, int(hptime)))
    # pafter = yield from dali.positionAfterHPTime(hptime)
    # print("PacketId after: {} {}".format(pafter.type, pafter.value))
    # nextPacket = yield from dali.read(pafter.value)
    # print("next after: {} {} {}".format(nextPacket.type, nextPacket.dataStartTime, nextPacket.dataEndTime))
    # print("hptime round trip: {} {}".format(hptime, simpleDali.datetimeToHPTime(simpleDali.hptimeToDatetime(int(hptime)))))
    # nowTime = datetime.utcnow()
    # print("hptime now: {} {}".format(hptime, simpleDali.datetimeToHPTime(simpleDali.hptimeToDatetime(int(hptime)))))

    # test auth
    secretKey = '234jkasdf342saf345h6'
    token = encode_auth_token(username, secretKey)
    print("token: {}".format(token))
    authTask = loop.create_task(dali.auth(token))
    loop.run_until_complete(authTask)
    print("Auth Resp: {}".format(authTask.result()))

    network = "XX"
    station = "TEST"
    location = "00"
    channel = "HNZ"
    starttime = datetime.utcnow()
    numsamples = 100
    samprate=200
    shortData = array("h") # shorts
    for i in range(numsamples):
        shortData.append(i)
    msh = simpleMiniseed.MiniseedHeader(network, station, location, channel, starttime, numsamples, samprate)
    msr = simpleMiniseed.MiniseedRecord(msh, shortData)
#    print("before writeMSeed")
#    sendTask = loop.create_task(dali.writeMSeed(msr))
#    loop.run_until_complete(sendTask)
#    print("writemseed resp {}".format(sendTask.result()))
    closeTask = loop.create_task(dali.close())
    loop.run_until_complete(closeTask)



loop = asyncio.get_event_loop()
loop.set_debug(True)

doTest(loop)
#pending_tasks = [
#        task for task in asyncio.Task.all_tasks() if not task.done()]
#loop.run_until_complete(asyncio.gather(*pending_tasks))
loop.close()
