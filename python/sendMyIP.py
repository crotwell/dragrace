import asyncio
import json
import math
import random
import signal
import time
from datetime import datetime, timedelta
from netifaces import interfaces, ifaddresses, AF_INET

import simpleDali


def getLocalHostname():
    with open("/etc/hostname") as hF:
        hostname = hF.read()
    return hostname.strip()



net = "XX"
sta = getLocalHostname()[0:5].upper()
print("set station code to {}".format(sta))

interval = 10 # sleep in seconds

host = "129.252.35.36"
port = 15003

programname="sendMyIP"
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
    daliUpload = simpleDali.DataLink(host, port)
    #daliUpload.verbose = True
    serverId = await daliUpload.id(programname, username, processid, architecture)
    print("Connect Upload: {}".format(serverId))


loop = asyncio.get_event_loop()
initTask = loop.create_task(initConnections())
loop.run_until_complete(initTask)

while keepGoing:
    time.sleep(interval)
    myIPaddr = ifaddresses('eth0')[AF_INET][0].get('addr')
    starttime = datetime.utcnow()
    jsonMessage = {
        "station": sta,
        "time": starttime.isoformat(),
        "ip": myIPaddr
    }
    streamid = "{}.{}/IP".format(net, sta)
    hpdatastart = simpleDali.datetimeToHPTime(starttime.timestamp())
    hpdataend = simpleDali.datetimeToHPTime(starttime.timestamp())
    jsonSendTask = loop.create_task(daliUpload.writeJSON(streamid, hpdatastart, hpdataend, jsonMessage))
    loop.run_until_complete(jsonSendTask)
    ack = jsonSendTask.result()
    #print("send {} max = {:f} as json, {}".format(s, val, ack))

daliUpload.close()
loop.close()
