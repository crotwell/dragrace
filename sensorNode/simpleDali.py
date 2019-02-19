import asyncio

MICROS = 1000000

class DataLink:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    @asyncio.coroutine
    def createDaliConnection(self):
        self.close()
        self.reader, self.writer = yield from asyncio.open_connection(self.host, self.port)

    @asyncio.coroutine
    def send(self, header, data):
        h = header.encode('UTF-8')
        pre = "DL"
        if self.reader is None or self.writer is None:
             yield from self.createDaliConnection()
        self.writer.write(pre.encode('UTF-8'))
        lenByte = len(h).to_bytes(1, byteorder='big', signed=False)
        self.writer.write(lenByte)
        #print("send pre {} as {}{:d}".format(pre, pre.encode('UTF-8'),lenByte[0]))
        self.writer.write(h)
        #print("send head {}".format(header))
        if(data):
            self.writer.write(data)
            #print("send data of size {:d}".format(len(data)))
        out = yield from self.writer.drain()
        #print("drained")
        return out

    @asyncio.coroutine
    def parseResponse(self):
        pre = yield from self.reader.readexactly(3)
        # D ==> 68, L ==> 76
        if pre[0] == 68 and pre[1] == 76:
            hSize = pre[2]
        else:
            print("did not receive DL from read pre {:d}{:d}{:d}".format(pre[0],pre[1],pre[2]))
            self.close()
            raise Exception("did not receive DL from read pre")
        h = yield from self.reader.readexactly(hSize)
        header = h.decode("utf-8")
        type=None
        value=None
        message=None
        if header.startswith("ID "):
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
            m = yield from self.reader.readexactly(dSize)
            message = m.decode("utf-8")
            return DaliResponse(type, value, message)
        else:
            print("Header does not start with OK or ERROR: {}".format(header))
        return DaliResponse(type, value, message)

    @asyncio.coroutine
    def write(self, streamid, hpdatastart, hpdataend, flags, data):
        header = "WRITE {} {:d} {:d} {} {:d}".format(streamid, hpdatastart, hpdataend, flags, len(data))
        r = yield from self.send(header, data)
        return r

    @asyncio.coroutine
    def writeAck(self, streamid, hpdatastart, hpdataend, data):
        yield from self.write(streamid, hpdatastart, hpdataend, 'A', data)
        r = yield from  self.parseResponse()
        return r

    @asyncio.coroutine
    def writeMSeed(self, msr):
        #print("simpleDali.writeMSeed")
        streamid = "{}/MSEED".format(msr.codes())
        hpdatastart = int(msr.starttime().timestamp() * MICROS)
        hpdataend = int(msr.endtime().timestamp() * MICROS)
        r = yield from self.writeAck(streamid, hpdatastart, hpdataend, msr.pack())
        return r

    @asyncio.coroutine
    def id(self, programname, username, processid, architecture):
        header = "ID {}:{}:{}:{}".format(programname, username, processid, architecture)
        yield from self.send(header, None)
        r = yield from  self.parseResponse()
        return r

    @asyncio.coroutine
    def info(self, type):
        header = "INFO {}".format(type)
        yield from self.send(header, None)
        r = yield from  self.parseResponse()
        return r

    def close(self):
        if self.writer is not None:
            self.writer.close()
            self.writer = None
            self.reader = None

    @asyncio.coroutine
    def reconnect(self):
        self.close()
        return self.createDaliConnection(host, port)

class DaliResponse:

    def __init__(self, type, value, message):
        self.type = type
        self.value=value
        self.message = message

    def __str__(self):
        return "type={} value={} message={}".format(self.type, self.value, self.message)
