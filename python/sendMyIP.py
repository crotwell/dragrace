import asyncio
import json
import math
import random
import signal
import time
from datetime import datetime, timedelta
from netifaces import interfaces, ifaddresses, AF_INET
import socket

import simpleDali


def getLocalHostname():
    hostname = socket.gethostname().split('.')[0]
    return hostname.strip()



net = "XX"
sta = getLocalHostname()[0:5].upper()
print("set station code to {}".format(sta))

interval = 10 # sleep in seconds

host = "129.252.35.36"
port = 15003
uri = "ws://www.seis.sc.edu/dragracews/datalink"

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

def exceptionHandler(lopp, context):
    global daliUpload
    daliUpload = None
    print("oh noooooo,   {}".format(context['message']));

async def initConnections():
    global daliUpload
    # create a separate upload datalink
    daliUpload = simpleDali.SocketDataLink(host, port)
    #daliUpload = simpleDali.WebSocketDataLink(uri)
    #daliUpload.verbose = True
    serverId = await daliUpload.id(programname, username, processid, architecture)
    print("Connect Upload: {}".format(serverId))

def getIPAddr():
    for interf in interfaces():
        if ifaddresses(interf)[AF_INET] is not None:
            return ifaddresses(interf)[AF_INET][0].get('addr')
    raise Exception("No interface has an IPv4 address")

loop = asyncio.get_event_loop()
loop.set_exception_handler(exceptionHandler)

while keepGoing:
    if daliUpload is None:
        initTask = loop.create_task(initConnections())
        loop.run_until_complete(initTask)
    myIPaddr = getIPAddr()
    starttime = datetime.utcnow()
    jsonMessage = {
        "station": sta,
        "time": starttime.isoformat(),
        "ip": myIPaddr
    }
    streamid = "{}.{}/IP".format(net, sta)
    hpdatastart = simpleDali.datetimeToHPTime(starttime)
    hpdataend = simpleDali.datetimeToHPTime(starttime)
    jsonSendTask = loop.create_task(daliUpload.writeJSON(streamid, hpdatastart, hpdataend, jsonMessage))
    loop.run_until_complete(jsonSendTask)
    ack = jsonSendTask.result()
    print("send ip as {} ip = {} as json, {}".format(streamid, myIPaddr, ack))
    #keepGoing = False
    if keepGoing:
        time.sleep(interval)


loop.run_until_complete(loop.create_task(daliUpload.close()))
loop.close()
