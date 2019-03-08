import asyncio
import json
from datetime import datetime, timedelta

MICROS = 1000000

class DataLink:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.verbose = False

    async def createDaliConnection(self):
        self.close()
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send(self, header, data):
        h = header.encode('UTF-8')
        pre = "DL"
        if self.reader is None or self.writer is None:
             await self.createDaliConnection()
        self.writer.write(pre.encode('UTF-8'))
        lenByte = len(h).to_bytes(1, byteorder='big', signed=False)
        self.writer.write(lenByte)
        if self.verbose: print("send pre {} as {}{:d}".format(pre, pre.encode('UTF-8'),lenByte[0]))
        self.writer.write(h)
        if self.verbose: print("send head {}".format(header))
        if(data):
            self.writer.write(data)
            if self.verbose: print("send data of size {:d}".format(len(data)))
        out = await self.writer.drain()
        if self.verbose: print("drained")
        return out

    async def parseResponse(self):
        pre = await self.reader.readexactly(3)
        # D ==> 68, L ==> 76
        if pre[0] == 68 and pre[1] == 76:
            hSize = pre[2]
        else:
            if self.verbose: print("did not receive DL from read pre {:d}{:d}{:d}".format(pre[0],pre[1],pre[2]))
            self.close()
            raise Exception("did not receive DL from read pre")
        h = await self.reader.readexactly(hSize)
        header = h.decode("utf-8")
        type=None
        value=None
        message=None
        #if self.verbose: print("parseRespone header: {}".format(h))
        if header.startswith("PACKET "):
            s = header.split(" ")
            type = s[0]
            streamId = s[1]
            packetId = s[2]
            packetTime = s[3]
            dataStartTime = s[4]
            dataEndTime = s[5]
            dSize = int(s[6])
            data = await self.reader.readexactly(dSize)
            return DaliPacket(type, streamId, packetId, packetTime, dataStartTime, dataEndTime, dSize, data)
        elif header.startswith("ID "):
            s = header.split(" ")
            type = s[0]
            value = ""
            message = header[3:]
            return DaliResponse(type, value, message)
        elif (header.startswith("INFO ") or header.startswith("OK ") or header.startswith("ERROR ")):
            s = header.split(" ")
            type = s[0]
            value = s[1]
            dSize = int(s[2])
            m = await self.reader.readexactly(dSize)
            message = m.decode("utf-8")
            return DaliResponse(type, value, message)
        else:
            raise Exception("Header does not start with INFO, ID, PACKET, OK or ERROR: {}".format(header))
        return DaliResponse(type, value, message)

    async def write(self, streamid, hpdatastart, hpdataend, flags, data):
        header = "WRITE {} {:d} {:d} {} {:d}".format(streamid, hpdatastart, hpdataend, flags, len(data))
        r = await self.send(header, data)
        return r

    async def writeAck(self, streamid, hpdatastart, hpdataend, data):
        await self.write(streamid, hpdatastart, hpdataend, 'A', data)
        r = await  self.parseResponse()
        return r

    async def writeMSeed(self, msr):
        streamid = "{}/MSEED".format(msr.codes())
        hpdatastart = int(msr.starttime().timestamp() * MICROS)
        hpdataend = int(msr.endtime().timestamp() * MICROS)
        if self.verbose: print("simpleDali.writeMSeed {} {} {}".format(streamid, hpdatastart, hpdataend))
        r = await self.writeAck(streamid, hpdatastart, hpdataend, msr.pack())
        return r


    async def writeJSON(self, streamid, hpdatastart, hpdataend, jsonMessage):
        if self.verbose: print("simpleDali.writeMSeed {} {} {}".format(streamid, hpdatastart, hpdataend))
        jsonAsByteArray = json.dumps(jsonMessage).encode('UTF-8')
        r = await self.writeAck(streamid, hpdatastart, hpdataend, jsonAsByteArray)
        return r

    async def writeCommand(self, command, dataString=None):
        if self.verbose: print("writeCommand: cmd: {} dataStr: {}".format(command, dataString))
        dataBytes = None
        if (dataString):
            dataBytes = dataString.encode('UTF-8')
            header = "{} {}".format(command, len(dataBytes))
        else:
            header = command
        await self.send(header, dataBytes)
        r = await  self.parseResponse()
        return r

    async def id(self, programname, username, processid, architecture):
        header = "ID {}:{}:{}:{}".format(programname, username, processid, architecture)
        r = await self.writeCommand(header, None)
        return r

    async def info(self, type):
        header = "INFO {}".format(type)
        r = await self.writeCommand(header, None)
        return r

    async def positionAfter(self, time):
        hpdatastart = int(time.timestamp() * MICROS)
        r = await self.positionAfterHPTime(hpdatastart)
        return r

    async def positionAfterHPTime(self, hpdatastart):
        r = await self.writeCommand("POSITION AFTER {}".format(hpdatastart), None)
        return r

    async def match(self, pattern):
        r = await self.writeCommand("MATCH", pattern)
        return r

    async def reject(self, pattern):
        r = await self.writeCommand("REJECT", pattern)
        return r

    async def read(self, packetId):
        r = await self.writeCommand("READ {}".format(packetId), None)
        return r

    async def stream(self):
        header = "STREAM"
        await self.send(header, None)

    async def endStream(self):
        header = "ENDSTREAM"
        await self.send(header, None)

    def isClosed(self):
        return self.writer is None

    def close(self):
        if self.writer is not None:
            self.writer.close()
            self.writer = None
            self.reader = None

    async def reconnect(self):
        self.close()
        self.createDaliConnection(host, port)

class DaliResponse:

    def __init__(self, type, value, message):
        self.type = type
        self.value=value
        self.message = message

    def __str__(self):
        return "type={} value={} message={}".format(self.type, self.value, self.message)

class DaliPacket:
    def __init__(self,
                 type,
                 streamId,
                 packetId,
                 packetTime,
                 dataStartTime,
                 dataEndTime,
                 dSize,
                 data):
        self.type = type
        self.streamId = streamId
        self.packetId = packetId
        self.packetTime = packetTime
        self.dataStartTime = dataStartTime
        self.dataEndTime = dataEndTime
        self.dSize = dSize
        self.data = data

    def __str__(self):
        return "{} {} {} {} {} {} {}".format(self.type, self.streamId, self.packetId, self.packetTime, self.dataStartTime, self.dataEndTime, self.dSize)

def datetimeToHPTime(time):
    hptime = int(time.timestamp() * MICROS)
    return hptime

def hptimeToDatetime(hptime):
    dt = datetime.utcfromtimestamp( float(hptime) / MICROS)
    return dt
