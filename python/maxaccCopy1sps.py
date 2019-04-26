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

class MaxAccCopy:

    def __init__(self):
        self.verbose = False
        self.host = "129.252.35.36"
        self.port = 15003
        self.uploadPort = 15009
        self.uri = "ws://www.seis.sc.edu/dragracews/datalink"

        self.dali = None
        self.uploadDali = None
        self.programname="triggerListen"
        self.username="dragrace"
        self.processid=0
        self.architecture="python"


        self.staList= ['FL', 'NL', 'CT', 'NR', 'FR']
        self.net = "XX"
        self.loc = "00"
        self.chan = 'HNM'
        self.sps = 1.0

        self.maxWindow = timedelta(seconds=1)
        self.lastTime = dict()

        self.keepGoing = True


    async def initDali(self):

        if self.uploadDali is not None:
            await self.uploadDali.close()
        if self.dali is not None:
            await self.dali.close()

        self.uploadDali = simpleDali.SocketDataLink(self.host, self.uploadPort)
        serverId = await self.uploadDali.id(self.programname, self.username, self.processid, self.architecture)
        print("Upload Id: {}".format(serverId))


        self.dali = simpleDali.SocketDataLink(self.host, self.port)
        #self.dali = simpleDali.WebSocketDataLink(uri)
        #self.dali.verbose = True
        serverId = await self.dali.id(self.programname, self.username, self.processid, self.architecture)
        print("Resp: {}".format(serverId))
        serverInfo = await self.dali.info("STATUS")
        print("Info: {} ".format(serverInfo.message))
        #serverInfo = yield from self.dali.info("STREAMS")
        #print("Info: {} ".format(serverInfo.message))
        r = await self.dali.match(".*/(MAXACC)|(MTRIG)")
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
                    if dlPacket.streamId.endswith("MAXACC"):
                        prevTime = None
                        currTime = simpleDali.hptimeToDatetime(dlPacket.dataStartTime)
                        if dlPacket.streamId in self.lastTime:
                            prevTime = self.lastTime[dlPacket.streamId]
                            if currTime - prevTime > self.maxWindow:
                                self.lastTime[dlPacket.streamId] = currTime
                                await self.uploadDali.writeAck(dlPacket.streamId, int(dlPacket.dataStartTime), int(dlPacket.dataEndTime), dlPacket.data)
                                print("copy {}  {}".format(dlPacket.streamId, currTime))
                        else:
                            self.lastTime[dlPacket.streamId] = currTime
                            await self.uploadDali.writeAck(dlPacket.streamId, int(dlPacket.dataStartTime), int(dlPacket.dataEndTime), dlPacket.data)
                    else:
                        # forward everything else
                        await self.uploadDali.writeAck(dlPacket.streamId, int(dlPacket.dataStartTime), int(dlPacket.dataEndTime), dlPacket.data)

            except Exception:
                print(traceback.format_exc())

                await self.initDali()
        if self.dali is not None:
            await self.dali.close()
        if self.uploadDali is not None:
            await self.uploadDali.close()


if __name__ == "__main__":

    def handleSignal(sigNum, stackFrame):
        print("############ handleSignal {} ############".format(sigNum))
        if archiver.keepGoing:
            archiver.keepGoing = False
        else:
            sys.exit(0)


    archiver = MaxAccCopy()

    signal.signal(signal.SIGINT, handleSignal)
    signal.signal(signal.SIGTERM, handleSignal)

    loop = asyncio.get_event_loop()
    #loop.set_debug(True)
    loop.run_until_complete(archiver.doLoop())
    loop.close()
