import asyncio
import json
import math
import random
import signal
import time
from datetime import datetime, timedelta
from netifaces import interfaces, ifaddresses, AF_INET
import socket
import traceback

import simpleDali

class SendMyIP:
    def __init__(self):
        self.net = "XX"
        self.sta = self.getLocalHostname()[0:5].upper()
        print("set station code to {}".format(self.sta))

        self.interval = 10 # sleep in seconds

        self.host = "129.252.35.36"
        self.port = 15003
        self.uri = "ws://www.seis.sc.edu/dragracews/datalink"

        self.programname="sendMyIP"
        self.username="dragrace"
        self.processid=0
        self.architecture="python"

        self.daliUpload = None
        self.keepGoing = True

    def getLocalHostname(self):
        hostname = socket.gethostname().split('.')[0]
        return hostname.strip()


    def exceptionHandler(self, loop, context):
        if self.daliUpload is not None:
            self.daliUpload.close()
        self.daliUpload = None
        print("oh noooooo,   {}".format(context['message']));

    async def initConnections(self, daliUpload):
        if self.daliUpload is None:
            # create a separate upload datalink
            self.daliUpload = simpleDali.SocketDataLink(self.host, self.port)
            #daliUpload = simpleDali.WebSocketDataLink(self.uri)
        else:
            self.daliUpload.reconnect()
        #daliUpload.verbose = True
        serverId = await self.daliUpload.id(self.programname, self.username, self.processid, self.architecture)
        print("Connect Upload: {}".format(serverId))
        return self.daliUpload

    def getIPAddr(self):
        for interf in interfaces():
            if AF_INET in ifaddresses(interf):
                for interCon in ifaddresses(interf)[AF_INET]:
                    if 'addr' in interCon:
                        ip = interCon.get('addr')
                        if ip != "127.0.0.1":
                            #print("bla {} {} {}".format(interf, AF_INET, ip))
                            return ip
        raise Exception("No interface has a public IPv4 address")

    def run(self):
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self.exceptionHandler)

        repeatException = False
        while self.keepGoing:
            try:
                if self.daliUpload is None or self.daliUpload.isClosed():
                    initTask = loop.create_task(self.initConnections(self.daliUpload))
                    loop.run_until_complete(initTask)
                    if initTask.exception() is not None:
                        raise initTask.exception()
                    self.daliUpload = initTask.result()
                myIPaddr = self.getIPAddr()
                starttime = simpleDali.utcnowWithTz()
                jsonMessage = {
                    "station": self.sta,
                    "time": starttime.isoformat(),
                    "ip": myIPaddr
                }
                streamid = "{}.{}/IP".format(self.net, self.sta)
                hpdatastart = simpleDali.datetimeToHPTime(starttime)
                hpdataend = simpleDali.datetimeToHPTime(starttime)
                jsonSendTask = loop.create_task(self.daliUpload.writeJSON(streamid, hpdatastart, hpdataend, jsonMessage))
                loop.run_until_complete(jsonSendTask)
                if jsonSendTask.exception() is not None:
                    self.daliUpload.close()
                    print("Exception sending json: {}".format( jsonSendTask.exception()))
                else:
                    ack = jsonSendTask.result()
                    print("send ip as {} ip = {} as json, {}".format(streamid, myIPaddr, ack))
                    #keepGoing = False
                if repeatException:
                    print("Recovered from repeat exception")
                    repeatException = False
            except Exception:
                if self.daliUpload is None:
                    self.close()
                if not repeatException:
                    print(traceback.format_exc())
                    repeatException = True
            for tempSleep in range(self.interval):
                # sleep for interval seconds, but check to see if we should
                # quit once a second
                if self.keepGoing:
                    time.sleep(1)


        loop.run_until_complete(loop.create_task(self.daliUpload.close()))
        loop.close()
        # end run()

if __name__ == "__main__":
    # execute only if run as a script
    sendMyIP = SendMyIP()

    def handleSignal(sigNum, stackFrame):
        print("############ handleSignal {} ############".format(sigNum))
        global sendMyIP
        if sendMyIP.keepGoing:
            sendMyIP.keepGoing = False
        else:
            sys.exit(0)

    signal.signal(signal.SIGINT, handleSignal)
    signal.signal(signal.SIGTERM, handleSignal)
    sendMyIP.run()
