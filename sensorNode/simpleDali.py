import asyncio

class DataLink:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    @asyncio.coroutine
    def createDaliConnection(self):
        self.close()
        connect = asyncio.open_connection(self.host, self.port)
        self.reader, self.writer = yield from connect

    @asyncio.coroutine
    def send(self, header, data):
        h = header.encode()
        pre = "DL{:d}".format(len(h))
        if self.reader is None or self.writer is None:
            yield from self.createDaliConnection()
        self.writer.write(pre.encode())
        print("send pre {}".format(pre))
        self.writer.write(h)
        print("send head {}".format(header))
        if(data):
            self.writer.write(data)
            print("send data of size {:d}".format(len(data)))
        yield from self.writer.drain()
        print("drained")

    @asyncio.coroutine
    def parseResponse(self):
        pre = yield from self.reader.readexactly(3)
        if pre[0] == b'D' and pre[1] == b'L':
            hSize = pre[2]
        else:
            print("did not receive DL from read pre")
            self.close()
            raise Exception("did not receive DL from read pre")
        h = yield from self.reader.readexactly(hSize).decode("utf-8")
        type=None
        value=None
        message=None
        if (h.startswith("OK ") or h.startswith("ERROR ")):
            s = h.split(" ")
            type = s[0]
            value = s[1]
            dSize = int(s[2])
            message = yield from self.reader.readexactly(dSize)
        return DaliResponse(type, value, message)

    def write(self, streamid, hpdatastart, hpdataend, flags, data):
        header = "WRITE {} {:d} {:d} {} {:d}".format(streamid, hpdatastart, hpdataend, flags, len(data))
        self.send(header, data)
        return self.parseResponse()

    def writeAck(self, streamid, hpdatastart, hpdataend, data):
        self.write(streamid, hpdatastart, hpdataend, 'A', data)
        return self.parseResponse()

    def writeMSeed(self, msr):
        streamid = "{}/MSEED".format(msr.codes())
        hpdatastart = long(msr.starttime().timestamp() * 1000000)
        hpdataend = long(msr.endtime().timestamp() * 1000000)
        return self.writeAck(streamid, hpdatastart, hpdataend, msr.pack())

    def id(self, programname, username, processid, architecture):
        header = "ID {}:{}:{}:{}".format(programname, username, processid, architecture)
        yield from self.send(header, None)
        id = yield from self.parseResponse()
        return id

    def close(self):
        if self.writer is not None:
            self.writer.close()
            self.writer = None
        if self.reader is not None:
            self.reader.close()
            self.reader = None

    def reconnect(self):
        self.close()
        self.createDaliConnection(host, port)

class DaliResponse:

    def __init__(self, type, value, message):
        self.type = type
        self.value=value
        self.message = message

    def toString():
        return "type={} value={} message={}".format(self.type, self.value, self.message)
