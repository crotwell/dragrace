import asyncio
import json
import math
import random
import signal
import time
from datetime import datetime, timedelta

import simpleDali

net = "XX"
interval = 10

host = "129.252.35.36"
port = 15003
uri = "ws://www.seis.sc.edu/dragracews/datalink"

programname="fakeConfig"
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

while keepGoing:
    time.sleep(interval)
    starttime = datetime.utcnow()
    jsonMessage = {
        "Location":{
           "PI01": "NO",
           "PI02": "FL",
           "PI03": "NO",
           "PI04": "NO",
           "PI05": "FR",
           "PI06": "NO",
           "PI07": "NO",
           "PI99": "FK"
       },
       "LocationDetails":{
           "FL":{
              "Theta": 0,
              "Name": "Far Left Wall"
           },
           "NL":{
              "Theta": 0,
              "Name": "Left Starters Area"
           },
           "CT":{
              "Theta": 0,
              "Name": "Center Wall End"
           },
           "NR":{
              "Theta": 0,
              "Name": "Right Starters Area"
           },
           "FR":{
              "Theta": 0,
              "Name": "Far Right Wall"
           },
           "FK":{
              "Theta": 45,
              "Name": "Fake Location for PI99"
           }
       }
    }
    streamid = "{}.{}/ZMAXCFG".format(net, 'ZMAX')
    hpdatastart = int(starttime.timestamp() * simpleDali.MICROS)
    hpdataend = int(starttime.timestamp() * simpleDali.MICROS)
    ack = writeJsonToDatalink(streamid, hpdatastart, hpdataend, jsonMessage)


daliUpload.close()
loop.close()
