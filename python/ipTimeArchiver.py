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
        self.flushInterval = timedelta(seconds=60)
        self.flushAll()
        with open(self.gapFilename, 'a') as f:
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            f.write('# Flush ip gaps at {}\n'.format(now.isoformat()))

    def recordIPTime(self, sendIpJson):
        jsonTime = dateutil.parser.parse(sendIpJson['time']).replace(tzinfo=timezone.utc)
        if not sendIpJson['station'] in self.ipTime:
            self.ipTime[sendIpJson['station']] = {
                'start':jsonTime,
                'end':jsonTime
            }
        else:
            if jsonTime - self.ipTime[sendIpJson['station']]['end']  < self.maxGap:
                self.ipTime[sendIpJson['station']]['end'] = jsonTime
            else:
                self.writeToFile(sendIpJson['station'])
                self.ipTime[sendIpJson['station']] = {
                    'start':jsonTime,
                    'end':jsonTime
                }
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        if self.lastFlushTime is None or now - self.lastFlushTime > self.flushInterval:
            self.flushAll()

    def writeToFile(self, station):
        with open(self.gapFilename, 'a') as f:
            s = self.ipTime[station]['start']
            e = self.ipTime[station]['end']
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            nowDelta = now - e
            upInterval = e - s
            f.write('{} {} {} {} {}\n'.format(station, self.strfdelta(upInterval), s.strftime("%Y/%m/%dT%H:%M:%S"), e.strftime("%Y/%m/%dT%H:%M:%S"), self.strfdelta(nowDelta)))

    def flushAll(self):
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        with open(self.outFilename, 'w') as f:
            f.write('# Flush ip at {}\n'.format(now.isoformat()))
            for station, v in self.ipTime.items():
                s = self.ipTime[station]['start']
                e = self.ipTime[station]['end']
                now = datetime.utcnow().replace(tzinfo=timezone.utc)
                nowDelta = now - e
                upInterval = e - s
                f.write('{} {} {} {} {}\n'.format(station, self.strfdelta(upInterval), s.strftime("%Y/%m/%dT%H:%M:%S"), e.strftime("%Y/%m/%dT%H:%M:%S"), self.strfdelta(nowDelta)))
        self.lastFlushTime = datetime.utcnow().replace(tzinfo=timezone.utc)

    def strfdelta(self, tdelta):
        hours, rem = divmod(tdelta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        hours = hours + tdelta.days*24
        hoursZero = ''
        minutesZero = ''
        if hours < 10:
            hoursZero = '0'
        if minutes < 10:
            minutesZero = '0'
        return "{}{}:{}{}".format(hoursZero, hours, minutesZero, minutes)

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
    #loop.set_debug(True)
    loop.run_until_complete(archiver.doLoop())
    loop.close()
