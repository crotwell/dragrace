import dataBuffer
import simpleDali
import simpleMiniseed
import asyncio
import logging
import signal
import sys
import traceback
import json
import math
from datetime import datetime, timedelta, timezone
import dateutil.parser
from array import array

logging.basicConfig(level=logging.DEBUG)

class MaxAccArchive:

    def __init__(self):
        self.verbose = False
        self.host = "129.252.35.36"
        self.port = 15003
        self.uri = "ws://www.seis.sc.edu/dragracews/datalink"

        self.programname="triggerListen"
        self.username="dragrace"
        self.processid=0
        self.architecture="python"


        self.staList= ['FL', 'NL', 'CT', 'NR', 'FR']
        self.net = "XX"
        self.loc = "00"
        self.chan = 'HNM'
        self.sps = 4

        self.miniseedBuffers = dict()
        for s in self.staList:
            self.initBuffer(s, self.sps)

        self.keepGoing = True

    def initBuffer(self, station, sps):
        if station in self.miniseedBuffers and self.miniseedBuffers[station] is not None:
            self.miniseedBuffers[station].close()
        self.miniseedBuffers[station] = dataBuffer.DataBuffer(self.net, station, self.loc, self.chan,
                 sps, archive=True,
                 encoding=simpleMiniseed.ENC_SHORT, dali=None,
                 continuityFactor=2, verbose=self.verbose)

    def calcSps(self, maxJson):
        dbuf = self.miniseedBuffers[maxJson['station']]
        if dbuf.numpts == 0:
            return self.sps
        else:
            sampTime = dateutil.parser.parse(maxJson['start_time']).replace(tzinfo=timezone.utc)
            count = dbuf.numpts
            bufBegin = dbuf.starttime
            sps = 1000000.0* count / ((sampTime - bufBegin) / timedelta(microseconds=1) )
            #print("calcSps {} {} sps={}".format(maxJson['station'], sampTime, sps))
            return sps

    async def initDali(self):
        self.dali = simpleDali.SocketDataLink(self.host, self.port)
        #self.dali = simpleDali.WebSocketDataLink(uri)
        #self.dali.verbose = True
        serverId = await self.dali.id(self.programname, self.username, self.processid, self.architecture)
        print("Resp: {}".format(serverId))
        serverInfo = await self.dali.info("STATUS")
        print("Info: {} ".format(serverInfo.message))
        #serverInfo = yield from self.dali.info("STREAMS")
        #print("Info: {} ".format(serverInfo.message))
        r = await self.dali.match(".*/MAXACC")
        print("match() Resonse {}".format(r))

        if r.type.startswith("ERROR"):
            print("match() Resonse {}, ringserver might not know about these packets?".format(r))
        else:
            print("match() Resonse m={}".format(r.message))
        r = await self.dali.stream()
        print("stream response: {}".format(r))

    async def doLoop(self):
        await self.initDali()
        while(self.keepGoing):
            try:
                dlPacket = await self.dali.parseResponse()
                if not dlPacket.type == "PACKET":
                    # might get an OK very first after stream
                    print("parseResponse not a PACKET {} ".format(trig))
                else:
                    maxJson=json.loads(dlPacket.data)
                    sps = self.calcSps(maxJson)
                    bufSps = self.miniseedBuffers[maxJson['station']].sampleRate
                    if abs(sps-bufSps) > 1 :
                        self.initBuffer(maxJson['station'], sps)
                    start = dateutil.parser.parse(maxJson['start_time']).replace(tzinfo=timezone.utc)
                    zData =  math.trunc( maxJson['maxacc'] * 4096 ) # back to counts
                    self.miniseedBuffers[maxJson['station']].push(start, [ zData ])
            except Exception:
                print(traceback.format_exc())
                if self.dali is not None:
                    await self.dali.close()
                await self.initDali()
        # flush all
        for s, db in self.miniseedBuffers.items():
            db.close()


if __name__ == "__main__":

    def handleSignal(sigNum, stackFrame):
        print("############ handleSignal {} ############".format(sigNum))
        if archiver.keepGoing:
            archiver.keepGoing = False
        else:
            sys.exit(0)


    archiver = MaxAccArchive()

    signal.signal(signal.SIGINT, handleSignal)
    signal.signal(signal.SIGTERM, handleSignal)

    loop = asyncio.get_event_loop()
    #loop.set_debug(True)
    loop.run_until_complete(archiver.doLoop())
    loop.close()
