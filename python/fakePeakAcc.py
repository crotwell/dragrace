import asyncio
import json
import math
import random
import signal
import time
from datetime import datetime, timedelta

import simpleDali

net = "XX"
stations = [ 'PI10', 'PI11']
interval = 1

host = "129.252.35.36"
port = 15003
uri = "ws://www.seis.sc.edu/dragracews/datalink"

programname="fakePeakAccelerationTrace"
username="dragrace"
processid=0
architecture="python"

daliUpload = None
keepGoing = True

def handleSignal(sigNum, stackFrame):
    print("############ handleSignal {} ############".format(sigNum))
    global keepGoing
    if keepGoing:
        keepGoing = False
    else:
        sys.exit(0)

signal.signal(signal.SIGINT, handleSignal)
signal.signal(signal.SIGTERM, handleSignal)

async def initConnections():
    global daliUpload
    # create a separate upload datalink
    daliUpload = simpleDali.SocketDataLink(host, port)
    #daliUpload = simpleDali.WebSocketDataLink(uri)
    #daliUpload.verbose = True
    serverId = await daliUpload.id(programname, username, processid, architecture)
    print("Connect Upload: {}".format(serverId))


def writeJsonToDatalink(streamid, hpdatastart, hpdataend, jsonMessage):
    global daliUpload
    jsonAsByteArray = json.dumps(jsonMessage).encode('UTF-8')
    loop = asyncio.get_event_loop()
    jsonSendTask = loop.create_task(daliUpload.writeAck(streamid, hpdatastart, hpdataend, jsonAsByteArray))
    loop.run_until_complete(jsonSendTask)
    return jsonSendTask.result()


loop = asyncio.get_event_loop()
initTask = loop.create_task(initConnections())
loop.run_until_complete(initTask)
prevAcc = {}
for s in stations:
    prevAcc[s] = 0.1

while keepGoing:
    time.sleep(interval)
    starttime = datetime.utcnow()
    for s in stations:
        val = prevAcc[s] + 0.1*(2-random.randrange(5))
        if val > 2:
            val = 2
        elif val < 0:
            val = 0
        prevAcc[s] = val

        jsonMessage = {
            "station": s,
            "time": starttime.isoformat(),
            "accel": val
        }
        streamid = "{}.{}/MAXACC".format(net, s)
        hpdatastart = int(starttime.timestamp() * simpleDali.MICROS)
        hpdataend = int(starttime.timestamp() * simpleDali.MICROS)
        ack = writeJsonToDatalink(streamid, hpdatastart, hpdataend, jsonMessage)
        #print("send {} max = {:f} as json, {}".format(s, val, ack))

daliUpload.close()
loop.close()
