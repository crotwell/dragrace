import argparse
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
    def __init__(self, intervalSecs, tokenFile):
        self.verbose = True
        self.token = None
        self.tokenFilename = None
        if tokenFile is not None:
            print("init tokenFile: {},   name: ".format(tokenFile, tokenFile.name))
            self.tokenFilename = tokenFile.name
            self.token = tokenFile.readline().strip()
        self.net = "XX"
        self.sta = self.getLocalHostname()[0:5].upper()
        if self.verbose:
            print("set station code to {}".format(self.sta))

        self.interval = intervalSecs # sleep in seconds

        #self.host = "129.252.35.36"
        #self.port = 15003
        self.host="74.207.233.105"
        self.port=6382
        #self.uri = "wss://www.seis.sc.edu/dragracews/datalink"
        self.uri = "wss://74.207.233.105/datalink"

        self.programname="sendMyIP"
        self.username="dragrace"
        self.processid=0
        self.architecture="python"

        self.daliUpload = None
        self.keepGoing = True

    def reloadToken(self):
        if self.tokenFilename is not None:
            with open(self.tokenFilename) as f:
                self.token = f.readline().strip()
        return self.token

    def getLocalHostname(self):
        hostname = socket.gethostname().split('.')[0]
        return hostname.strip()


    def exceptionHandler(self, loop, context):
        if self.daliUpload is not None:
            self.daliUpload.close()
        self.daliUpload = None
        print("oh noooooo,   {}".format(context['message']));

    async def authorize(self):
        if self.token:
            authResp = await self.daliUpload.auth(self.token)
            if self.verbose:
                print("auth: {}".format(authResp))
            if authResp.type == 'ERROR':
                print("AUTHORIZATION failed, quiting...")
                self.keepGoing = False
                raise Exception("AUTHORIZATION failed, {} {}".format(authResp.type, authResp.message))

    async def initConnections(self, daliUpload):
        if self.verbose:
            print("initConnections...{}".format(daliUpload is not None))
        if self.daliUpload is None:
            # create a separate upload datalink
            #self.daliUpload = simpleDali.SocketDataLink(self.host, self.port)
            self.daliUpload = simpleDali.WebSocketDataLink(self.uri)
            self.daliUpload.verbose = False
            await self.authorize()
        else:
            await self.daliUpload.reconnect()
        serverId = await self.daliUpload.id(self.programname, self.username, self.processid, self.architecture)
        if self.verbose:
            print("Connect Upload: {}".format(serverId))
            serverInfo = await self.daliUpload.info("STATUS")
            print("Server Info: {}".format(serverInfo));
            infoDict = self.daliUpload.parseInfoStatus(serverInfo)
            for k,v in infoDict.items():
                if isinstance(v,dict):
                    print(k)
                    for k,v in v.items():
                        print("   {} = {}".format(k,v))
                else:
                    print("   {} = {}".format(k,v))
        return self.daliUpload

    def getIPAddr(self):
        for interf in interfaces():
            if AF_INET in ifaddresses(interf):
                for interCon in ifaddresses(interf)[AF_INET]:
                    if 'addr' in interCon:
                        ip = interCon.get('addr')
                        if ip != "127.0.0.1":
                            return ip
        raise Exception("No interface has a public IPv4 address")

    async def doSingleLapAroundTheTrack(self):
        if self.token is not None and simpleDali.timeUntilExpireToken(self.token) < timedelta(0):
            # maybe someone gave us a new one?
            if self.verbose:
                print("token expired, reloading")
            self.reloadToken()
            if self.token is not None and simpleDali.timeUntilExpireToken(self.token) < timedelta(0):
                raise Exception("Expired token in {}...".format(self.tokenFilename))

        if self.daliUpload is None:
            # first time or maybe something bad happened
            print("  sendMyIP while loop  {}   closed={}".format(self.daliUpload is not None, self.daliUpload is not None and self.daliUpload.isClosed()))
            self.daliUpload = await self.initConnections(self.daliUpload)
        myIPaddr = self.getIPAddr()
        starttime = simpleDali.utcnowWithTz()
        jsonMessage = {
            "station": self.sta,
            "time": starttime.isoformat(),
            "ip": myIPaddr
        }
        streamid = "{}_{}/IP".format(self.net, self.sta)
        hpdatastart = simpleDali.datetimeToHPTime(starttime)
        hpdataend = simpleDali.datetimeToHPTime(starttime)
        response = await self.daliUpload.writeJSON(streamid, hpdatastart, hpdataend, jsonMessage)
        if self.verbose:
            print("send ip as {} ip = {} as json, {}".format(streamid, myIPaddr, response))
        if response.type == 'ERROR' and response.message.startswith(simpleDali.NO_SOUP):
            print("AUTHORIZATION failed, quiting...")
            self.keepGoing = False
        #keepGoing = False

    def run(self):
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self.exceptionHandler)

        repeatException = False
        while self.keepGoing:
            try:
                doItTask = loop.create_task(self.doSingleLapAroundTheTrack())
                loop.run_until_complete(doItTask)
                if doItTask.exception() is not None:
                    raise doItTask.exception()

                if repeatException:
                    if self.verbose:
                        print("Recovered from repeat exception")
                    repeatException = False
            except Exception:
                if self.daliUpload is not None:
                    closeTask = loop.create_task(self.daliUpload.close())
                    loop.run_until_complete(closeTask)
                if not repeatException:
                    print(traceback.format_exc())
                    repeatException = True
            except:
                # bail out
                if self.daliUpload is not None:
                    closeTask = loop.create_task(self.daliUpload.close())
                    loop.run_until_complete(closeTask)
                self.keepGoing = False
                print(traceback.format_exc())
                raise
            for tempSleep in range(self.interval):
                # sleep for interval seconds, but check to see if we should
                # quit once a second
                if self.keepGoing:
                    time.sleep(1)


        loop.run_until_complete(loop.create_task(self.daliUpload.close()))
        loop.close()
        # end run()



def handleSignal(sigNum, stackFrame):
    print("############ handleSignal {} ############".format(sigNum))
    global sendMyIP
    if sendMyIP is not None and sendMyIP.keepGoing:
        sendMyIP.keepGoing = False
    else:
        sys.exit(0)

if __name__ == "__main__":
    # execute only if run as a script
    parser = argparse.ArgumentParser()
    parser.add_argument("-t",
                        dest="tokenFile",
                        type=argparse.FileType('r'),
                        help="tokenfile, encoded on first line")
    parser.add_argument("-i",
                        dest="interval",
                        type=int,
                        default=10,
                        help="send time interval in seconds")
    args = parser.parse_args()
    sendMyIP = SendMyIP(args.interval, args.tokenFile)

    signal.signal(signal.SIGINT, handleSignal)
    signal.signal(signal.SIGTERM, handleSignal)
    sendMyIP.run()
