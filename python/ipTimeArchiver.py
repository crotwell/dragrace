import simpleDali
import simpleMiniseed
import asyncio
import logging
import signal
import sys
import json
from datetime import datetime, timedelta, timezone
import dateutil.parser
from array import array

logging.basicConfig(level=logging.DEBUG)

class IpTimeArchive:

    def __init__(self):
        self.host = "129.252.35.36"
        self.port = 15003
        self.uri = "ws://www.seis.sc.edu/dragracews/datalink"

        self.programname="triggerListen"
        self.username="dragrace"
        self.processid=0
        self.architecture="python"

        self.keepGoing = True
        self.ipTime = {}
        self.maxGap = timedelta(seconds=15)
        self.outFilename = "mseed/www/iptime.txt"
        self.gapFilename = "mseed/www/ipgaps.txt"
        self.lastFlushTime = None
        self.flushInterval = timedelta(seconds=300)

    def recordIPTime(self, sendIpJson):
        jsonTime = dateutil.parser.parse(sendIpJson['time']).replace(tzinfo=timezone.utc)
        if not sendIpJson['station'] in self.ipTime:
            self.ipTime[sendIpJson['station']] = {
                'start':jsonTime,
                'end':jsonTime
            }
        else:
            if self.ipTime[sendIpJson['station']]['end'] - jsonTime < self.maxGap:
                self.ipTime[sendIpJson['station']]['end'] = jsonTime
            else:
                self.writeToFile()
                self.ipTime[sendIpJson['station']] = {
                    'start':jsonTime,
                    'end':jsonTime
                }
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        if self.lastFlushTime is None or now - self.lastFlushTime > self.flushInterval:
            self.flushAll()

    def writeToFile(self, station):
        with open(self.gapFilename, 'a') as f:
            f.write('{} {} {}\n'.format(station, self.ipTime[station].start.isoformat(), self.ipTime[station].end.isoformat()))

    def flushAll(self):
        with open(self.outFilename, 'w') as f:
            for station, v in self.ipTime.items():
                f.write('{} {} {}\n'.format(station, v['start'].isoformat(), v['end'].isoformat()))
        self.lastFlushTime = datetime.utcnow().replace(tzinfo=timezone.utc)

    async def doLoop(self):
        dali = simpleDali.SocketDataLink(self.host, self.port)
        #dali = simpleDali.WebSocketDataLink(uri)
        #dali.verbose = True
        serverId = await dali.id(self.programname, self.username, self.processid, self.architecture)
        print("Resp: {}".format(serverId))
        serverInfo = await dali.info("STATUS")
        print("Info: {} ".format(serverInfo.message))
        #serverInfo = yield from dali.info("STREAMS")
        #print("Info: {} ".format(serverInfo.message))
        r = await dali.match(".*/IP")
        print("match() Resonse {}".format(r))

        if r.type.startswith("ERROR"):
            print("match() Resonse {}, ringserver might not know about these packets?".format(r))
        else:
            print("match() Resonse m={}".format(r.message))
        r = await dali.stream()
        print("stream response: {}".format(r))
        while(self.keepGoing):
            trig = await dali.parseResponse()
            if not trig.type == "PACKET":
                # might get an OK very first after stream
                print("parseResponse not a PACKET {} ".format(trig))
            else:
                ipJson = json.loads(trig.data)
                self.recordIPTime(ipJson)
                #print("IP: {}  {}".format(trig, json.dumps(json.loads(trig.data), indent=4)))

        self.flushAll()
        await dali.close()




if __name__ == "__main__":

    archiver = IpTimeArchive()

    def handleSignal(sigNum, stackFrame):
        print("############ handleSignal {} ############".format(sigNum))
        global keepGoing
        if archiver.keepGoing:
            archiver.keepGoing = False
        else:
            sys.exit(0)

    signal.signal(signal.SIGINT, handleSignal)
    signal.signal(signal.SIGTERM, handleSignal)

    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(archiver.doLoop())
    loop.close()
