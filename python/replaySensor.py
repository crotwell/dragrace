import fakeSensor
from datetime import datetime, timedelta, timezone
import time
import struct
import queue
from threading import Thread
from datetime import datetime, timedelta, timezone
import sys, os, signal
import socket
from pathlib import Path
import asyncio
import traceback
import faulthandler
import json

import simpleMiniseed
import simpleDali


class ReplaySensor(fakeSensor.FakeSensor):
    def __init__(self, dataDir, netGlob, staGlob, locGlob, chanGlob, startTime, staRemap, duration=None):
        super().__init__()
        self.data_rate = self.adafruit_mma8451.DATARATE_50HZ  #  400Hz
        self.range = self.adafruit_mma8451.RANGE_2G  # +/- 2G
        self.msrBuffer = []
        self.dataDir=dataDir
        self.netGlob = netGlob
        self.staGlob = staGlob
        self.locGlob = locGlob
        self.chanGlob = chanGlob
        self.staRemap= staRemap
        self.duration = duration
        self.initTime = simpleDali.utcnowWithTz()
        self.startTime = startTime
        self.deltaTime = self.initTime - self.startTime
        #self.pattern = "{net}/{sta}/{year}/{yday}/{net}.{sta}.{loc}.{chan}.{year}.{yday}.{hour}"
        self.pattern = "Day_{yday}/{sta}.{chan}_{yday}_{hour}.mseed"
        self.openFiles = []
        self.prevSend = None

    def generateFakeData(self):
        sleepTime = 1
        while self.keepGoing:
            self.sendOldRecords()
            time.sleep(sleepTime)

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

    def modifyRecord(self, inMsr):
        msr = inMsr.clone()
        msr.header.setStartTime(inMsr.starttime() + self.deltaTime)
        msr.header.network = "XX"
        if msr.header.station in self.staRemap:
            msr.header.station = self.staRemap[msr.header.station]
        return msr

    def sendOldRecords(self):
        now = simpleDali.utcnowWithTz()
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
                modMsr = self.modifyRecord(msr)
                if self.verbose:
                    print("send {} {} -> {} {}".format(msr.codes(), msr.starttime(), modMsr.codes(), modMsr.starttime()))
                self.pushMSR(modMsr)
        self.prevSend = sendNow

    def pushMSR(self, msr):
        self.msrBuffer.append(msr)
        self.checkForThreeComp()

    def checkForThreeComp(self):
        if len(self.msrBuffer) < 3:
            return
        for f in range(0, len(self.msrBuffer)-2):
            first = self.msrBuffer[f]
            for s in range(f+1, len(self.msrBuffer)-1):
                second = self.msrBuffer[s]
                if self.areCompatible(first, second):
                    for t in range(s+1, len(self.msrBuffer)):
                        third = self.msrBuffer[t]
                        if self.areCompatible(first, third):
                            del self.msrBuffer[t]
                            del self.msrBuffer[s]
                            del self.msrBuffer[f]
                            self.doCallback(first, second, third)
        while len(self.msrBuffer) > 9:
            msr =  self.msrBuffer.pop(0)
            print("purge oldest {} {}".format(msr.codes(), msr.starttime))


    def doCallback(self, first, second, third):
        x,y,z = self.orderXYZ(first, second, third)
        now = first.endtime()
        status = 1
        samplesAvail = first.header.numsamples
        # just send a tuple of the data, then demux will be called
        # where we will break it up
        data = []
        for i in range(samplesAvail):
            data.append(x.data[i])
            data.append(y.data[i])
            data.append(z.data[i])
        self.callback(now, status, samplesAvail, data)

    def orderXYZ(self, a, b, c):
        out = {}
        out[a.header.channel[2]] = a
        out[b.header.channel[2]] = b
        out[c.header.channel[2]] = c
        return out['X'], out['Y'], out['Z']

    def areCompatible(self, msrA, msrB):
        hA = msrA.header
        hB = msrB.header
        return (hA.starttime == hB.starttime
          and hA.sampleRate == hB.sampleRate
          and hA.numsamples == hB.numsamples
          and hA.network == hB.network
          and hA.station == hB.station
          and hA.location == hB.location
          and hA.channel[0:1] == hB.channel[0:1]
          and hA.channel[2] != hB.channel[2])


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
                "modtime": simpleDali.utcnowWithTz().isoformat(),
                "value": "enable"
            }
        }
        trigBytes = json.dumps(trigInfo).encode('UTF-8')
        r = await self.dali.writeAck(streamid, hpdatastart, hpdataend, trigBytes)
        print("writem trigger resp {}".format(r));


class OpenMiniseedFile:
    def __init__(self, path, verbose=False):
        self.verbose = verbose
        self.path = path
        self.openFile = open(self.path, 'rb+')
        self.msr = self.nextRecord()
        if self.verbose:
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
            if self.verbose:
                print("Done {:d}".format(len(rawBytes)))
            self.openFile.close()
            self.openFile = None
        else:
            msr = simpleMiniseed.unpackMiniseedRecord(rawBytes)
        return msr


if __name__ == "__main__":
    ############################################
    # values to change:
    dataDir="Track_Data"
    netGlob = "XX"
    staGlob = "XB08"
    locGlob = "00"
    chanGlob = "HN[XYZ]"
    # if need seconds add :%S
    startTime = datetime.strptime("2018-10-14T11:00Z", "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
    duration = timedelta(hours=2)
    staRemap = {
        'XB02': 'PI02',
        'XB03': 'PI03',
        'XB05': 'PI05',
        'XB08': 'PI08',
        'XB10': 'PI10'
    }
    #elf.duration = timedelta(seconds=20)
    repeat = True
    # end values to change
    ############################################
    sensor = ReplaySensor(dataDir, netGlob, staGlob, locGlob, chanGlob, startTime, staRemap, duration=None)
    sensor.verbose = True
    def dummyCallback(now, status, samplesAvail, data):
        print("{} {} ".format(now, samplesAvail))
    sensor.enableFifoBuffer(100, 1, dummyCallback)
    sensor.sensorThread.join()
