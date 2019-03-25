#!/usr/bin/python3

# Replay old miniseed data to a ringserver, updating time to look like
# it is realtime
# Author: Philip Crotwell
import time
import struct
import queue
from threading import Thread
from datetime import datetime, timedelta
import sys, os, signal
import socket
from pathlib import Path
import asyncio
import traceback
import faulthandler
import json

import simpleMiniseed
import simpleDali

faulthandler.enable()
keepGoing = True
verbose = False

def handleSignal(sigNum, stackFrame):
    print("############ handleSignal {} ############".format(sigNum))
    global keepGoing
    if keepGoing:
        keepGoing = False
    else:
        sys.exit(0)

signal.signal(signal.SIGINT, handleSignal)
signal.signal(signal.SIGTERM, handleSignal)

class OpenMiniseedFile:
    def __init__(self, path):
        global verbose
        self.path = path
        self.openFile = open(self.path, 'rb+')
        self.msr = self.nextRecord()
        if verbose:
            print("open file: {}".format(self.path))
    def recordsBefore(self, time, limit=100):
        out = []
        while self.msr is not None and self.msr.endtime() < time and len(out)<limit:
            out.append(self.msr)
            self.msr = self.nextRecord()
        return out

    def nextRecord(self):
        rawBytes = self.openFile.read(512)
        msr = None
        if len(rawBytes) < 512:
            print("Done {:d}".format(len(rawBytes)))
            self.openFile.close()
            self.openFile = None
        else:
            msr = simpleMiniseed.unpackMiniseedRecord(rawBytes)
        return msr

class MiniseedReplay:
    def __init__(self, daliUpload, dataDir, netGlob, staGlob, locGlob, chanGlob, startTime, duration=None):
        self.dali = daliUpload
        self.dataDir=dataDir
        self.netGlob = netGlob
        self.staGlob = staGlob
        self.locGlob = locGlob
        self.chanGlob = chanGlob
        self.duration = duration
        self.initTime = datetime.utcnow()
        self.startTime = startTime
        self.deltaTime = self.initTime - self.startTime
        #self.pattern = "{net}/{sta}/{year}/{yday}/{net}.{sta}.{loc}.{chan}.{year}.{yday}.{hour}"
        self.pattern = "Day_{yday}/{sta}.{chan}_{yday}_{hour}.mseed"
        self.openFiles = []
        self.prevSend = None

    def findHourFiles(self, hourTime):
        globPattern = self.pattern.format(net=self.netGlob,
                                        sta=self.staGlob,
                                        loc=self.locGlob,
                                        chan=self.chanGlob,
                                        year=hourTime.strftime("%Y"),
                                        yday=hourTime.strftime("%j"),
                                        hour=hourTime.strftime("%H"))
        p = Path(self.dataDir)
        hourFiles = []
        for f in p.glob(globPattern):
            hourFiles.append(OpenMiniseedFile(f))
        if len(hourFiles) == 0:
            print("no files: datadir={} glob={}  file={}".format(self.dataDir, globPattern, list(p.glob(globPattern))))
        return hourFiles
    def modifyRecord(self, msr):
        msr.header.setStartTime(msr.starttime() + self.deltaTime)
        msr.header.network = "XX"

    def sendOldRecords(self):
        now = datetime.utcnow()
        loop = asyncio.get_event_loop()
        # check to see if time to start all over again
        if self.duration is not None and now - self.initTime > self.duration:
            if verbose:
                print("restart after duration {}".format(self.duration))
            self.initTime = now
            self.deltaTime = self.initTime - self.startTime
            for of in self.openFiles:
                if of.openFile is not None:
                    of.openFile.close()
            self.openFiles = []
            self.prevSend = None
            trigTask = loop.create_task(self.doDurationTrigger())
            loop.run_until_complete(trigTask)
        sendNow = now - self.deltaTime
        if self.prevSend is None or self.prevSend.hour != sendNow.hour:
            self.openFiles = self.openFiles + self.findHourFiles(sendNow)

        for msFile in self.openFiles:
            msrList = msFile.recordsBefore(sendNow)
            for msr in msrList:
                self.modifyRecord(msr)
                if verbose:
                    print("send {} {}".format(msr.codes(), msr.starttime()))
                sendTask = loop.create_task(self.dali.writeMSeed(msr))
                loop.run_until_complete(sendTask)
        self.prevSend = sendNow

    async def doDurationTrigger(self):
        dutyOfficer="Re"+str(self.duration)

        streamid = "REPLAY/MTRIG"
        hpdatastart = int(self.startTime.timestamp() * simpleDali.MICROS)
        hpdataend = int(self.startTime.timestamp() * simpleDali.MICROS)
        trigInfo= {
            "type": "manual",
            "dutyOfficer": dutyOfficer,
            "time": self.initTime.isoformat(),
            "creation": self.startTime.isoformat(),
            "override": {
                "modtime": datetime.utcnow().isoformat(),
                "value": "enable"
            }
        }
        trigBytes = json.dumps(trigInfo).encode('UTF-8')
        r = await self.dali.writeAck(streamid, hpdatastart, hpdataend, trigBytes)
        print("writem trigger resp {}".format(r));

def main(args):
    global keepGoing, verbose

    ############################################
    # values to change:
    dataDir="Track_Data"
    netGlob = "XX"
    staGlob = "*"
    locGlob = "00"
    chanGlob = "HN[XYZ]"
    # if need seconds add :%S
    startTime = datetime.strptime("2018-10-14T11:00Z", "%Y-%m-%dT%H:%MZ")
    duration = timedelta(hours=2)
    #duration = timedelta(seconds=20)
    repeat = True
    # end values to change
    ############################################

    host = "129.252.35.36"
    port = 15004
    uri = "ws://www.seis.sc.edu/dragracews/datalink"


    programname="miniseedReplay"
    username="dragrace"
    processid=0
    architecture="python"

    # -1 means run forever, otherwise stop after MAX_COUNT packets, for testing
    MAX_COUNT=-1

    # create a separate upload datalink
    if verbose:
        print("Init Datalink to {}:{}".format(host, port))
    dali = simpleDali.SocketDataLink(host, port)
    #dali = simpleDali.WebSocketDataLink(uri)
    loop = asyncio.get_event_loop()
    #daliUpload.verbose = True
    idTask = loop.create_task(daliUpload.id(programname, username, processid, architecture))
    loop.run_until_complete(idTask)
    serverId = idTask.result()
    print("Connect Upload: {}".format(serverId))
    infoTask = loop.create_task(daliUpload.info("STATUS"))
    loop.run_until_complete(infoTask)
    info = infoTask.result()
    print("Connect Upload: {}".format(info))


    replay = MiniseedReplay(daliUpload, dataDir, netGlob, staGlob, locGlob, chanGlob, startTime, duration=duration)
    trigTask = loop.create_task(replay.doDurationTrigger())
    loop.run_until_complete(trigTask)
    while keepGoing:
        replay.sendOldRecords()
        time.sleep(0.5)

if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv[1:])
