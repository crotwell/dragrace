import argparse
import asyncio
import json
import math
import random
import signal
import time
from datetime import datetime, timedelta
#from netifaces import interfaces, ifaddresses, AF_INET
import socket
import traceback
import configChecker
import filecmp
import shutil
import sys

import simpleDali

# #For Testing
# productionDirectory="./ConfigFiles"
# prepDir=productionDirectory + "/ConfigFileEdit"
# archiveDir=productionDirectory + "/ConfigFileArchive"
# deployDir=productionDirectory + "/Run/ConfigFile"

# For Production Run

productionDirectory="/home/geo/Production"
prepDir=productionDirectory + "/ConfigFileEdit"
archiveDir=productionDirectory + "/ConfigFileArchive"
deployDir=productionDirectory + "/Run/ConfigFile"

class SendConfig:
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

        self.host = "129.252.35.36"
        self.port = 15003
        self.uri = "ws://www.seis.sc.edu/dragracews/datalink"

        self.programname="sendConfig"
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
        if self.daliUpload is None:
            # create a separate upload datalink
            self.daliUpload = simpleDali.SocketDataLink(self.host, self.port)
            #self.daliUpload = simpleDali.WebSocketDataLink(self.uri)
        else:
            self.daliUpload.reconnect()
        #daliUpload.verbose = True
        await self.authorize()
        serverId = await self.daliUpload.id(self.programname, self.username, self.processid, self.architecture)
        if self.verbose:
            print("Connect Upload: {}".format(serverId))
        return self.daliUpload

    def run(self):
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self.exceptionHandler)

        repeatException = False
        while self.keepGoing:
            try:
                if self.token is not None and simpleDali.timeUntilExpireToken(self.token) < timedelta(0):
                    # maybe someone gave us a new one?
                    if self.verbose:
                        print("token expired, reloading")
                    self.reloadToken()
                    if self.token is not None and simpleDali.timeUntilExpireToken(self.token) < timedelta(0):
                        raise Exception("Expired token in {}...".format(self.tokenFilename))

                if self.daliUpload is None or self.daliUpload.isClosed():
                    # first time or maybe something bad happened
                    initTask = loop.create_task(self.initConnections(self.daliUpload))
                    loop.run_until_complete(initTask)
                    if initTask.exception() is not None:
                        raise initTask.exception()
                    self.daliUpload = initTask.result()
                starttime = simpleDali.utcnowWithTz()

                oldfile=deployDir+"/config_deployed"
                newfile=prepDir+"/config_new"
                archivefile=archiveDir+"/config_deployed"

                if(filecmp.cmp(oldfile,newfile)):
                # Files are the same, no action required
                   noChange=True
                   print("Config file has not changed, sending anyway")

                   json_file=open(oldfile,'r')
                   contents=json_file.read()
                   jsonMessage=json.loads(contents)
                   json_file.close()

                   streamid = "{}.{}/ZMAXCFG".format(self.net, 'ZMAX')
                   hpdatastart = simpleDali.datetimeToHPTime(starttime)
                   hpdataend = simpleDali.datetimeToHPTime(starttime)
                   jsonSendTask = loop.create_task(self.daliUpload.writeJSON(streamid, hpdatastart, hpdataend, jsonMessage))
                   loop.run_until_complete(jsonSendTask)
                   if jsonSendTask.exception() is not None:
                       self.daliUpload.close()
                       if self.verbose:
                           print("Exception sending json: {}".format( jsonSendTask.exception()))
                       raise jsonSendTask.exception()
                   else:
                       response = jsonSendTask.result()
                       if self.verbose:
                           print("send config as {} as json, {}".format(streamid, response))
                       if response.type == 'ERROR' and response.message.startswith(simpleDali.NO_SOUP):
                           print("AUTHORIZATION failed, quiting...")
                           self.keepGoing = False
                    #keepGoing = False
                   if repeatException:
                       if self.verbose:
                           print("Recovered from repeat exception")
                       repeatException = False

                else:
                # Files are different, process the new one
                   noChange=False
                   json_file=open(newfile,'r')
                   goodConfig=configChecker.configSanityCheck(json_file)
                   if(not goodConfig):
                      print("Config file fails")
                   else:
    #
    # OK, archive the old config and post the new once
    #
                       print("New Config File is OK ... making it official and posting to ringserver")
                       shutil.move(oldfile,archivefile+"_"+starttime.isoformat())
                       shutil.copy2(newfile,oldfile)
                       json_file.seek(0)
                       contents=json_file.read()
                       jsonMessage=json.loads(contents)

                       streamid = "{}.{}/ZMAXCFG".format(self.net, 'ZMAX')
                       hpdatastart = simpleDali.datetimeToHPTime(starttime)
                       hpdataend = simpleDali.datetimeToHPTime(starttime)
                       jsonSendTask = loop.create_task(self.daliUpload.writeJSON(streamid, hpdatastart, hpdataend, jsonMessage))
                       loop.run_until_complete(jsonSendTask)
                       if jsonSendTask.exception() is not None:
                           self.daliUpload.close()
                           if self.verbose:
                               print("Exception sending json: {}".format( jsonSendTask.exception()))
                           raise jsonSendTask.exception()
                       else:
                           response = jsonSendTask.result()
                           if self.verbose:
                               print("send config as {} as json, {}".format(streamid, response))
                           if response.type == 'ERROR' and response.message.startswith(simpleDali.NO_SOUP):
                               print("AUTHORIZATION failed, quiting...")
                               self.keepGoing = False
                        #keepGoing = False
                       if repeatException:
                           if self.verbose:
                               print("Recovered from repeat exception")
                           repeatException = False

            except Exception:
                   if self.daliUpload is not None:
                       self.daliUpload.close()
                   if not repeatException:
                       print(traceback.format_exc())
                       repeatException = True
            sys.stdout.flush()
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
    global sender
    if sender is not None and sender.keepGoing:
        sender.keepGoing = False
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
                        default=60,
                        help="send time interval in seconds")
    args = parser.parse_args()
    sender = SendConfig(args.interval, args.tokenFile)

    signal.signal(signal.SIGINT, handleSignal)
    signal.signal(signal.SIGTERM, handleSignal)
    sender.run()
