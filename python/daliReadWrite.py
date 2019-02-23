import simpleDali
import simpleMiniseed
import asyncio
import logging
import signal
import sys
import json
from datetime import datetime, timedelta
from array import array

logging.basicConfig(level=logging.DEBUG)


host = "129.252.35.36"
port = 15003
#host = "129.252.35.20"
#host = "127.0.0.1"
#port = 6382

programname="triggerListen"
username="dragrace"
processid=0
architecture="python"

keepGoing = True


def handleSignal(sigNum, stackFrame):
    print("############ handleSignal {} ############".format(sigNum))
    global keepGoing
    if keepGoing:
        keepGoing = False
    else:
        sys.exit(0)

signal.signal(signal.SIGINT, handleSignal)
signal.signal(signal.SIGTERM, handleSignal)

dataBuffers = {}

# update this
outputSampleRate=1

def getDataBuffer(net, sta, loc, chan, outputSampleRate, outputDali):
    key = "{}.{}.{}.{}".format(net, sta, loc, chan)
    if not key in dataBuffers:
        dataBuffers[key] = DataBuffer(net, sta, loc, chan,
                     outputSampleRate, encoding=simpleMiniseed.ENC_SHORT,
                     dali=outputDali)
        dataBuffers[key].
    return dataBuffers[key]

@asyncio.coroutine
def doTest(loop):
    daliDownload = simpleDali.DataLink(host, port)
    daliDownload.verbose = True
    serverId = yield from daliDownload.id(programname, username, processid, architecture)
    print("Conect Download: {}".format(serverId))
    serverInfo = yield from daliDownload.info("STATUS")
    print("Info Statu: {} ".format(serverInfo.message))
    #serverInfo = yield from dali.info("STREAMS")
    #print("Info: {} ".format(serverInfo.message))
    #
    # match all MSEED streams
    #r = yield from dali.match(".*/MSEED")
    # or match just 3605 HNZ
    r = yield from daliDownload.match(".*3605.*HNZ/MSEED")
    print("match() Resonse {}".format(r))

    # create a separate upload datalink
    daliUpload = simpleDali.DataLink(host, port)
    daliUpload.verbose = True
    serverId = yield from daliUpload.id(programname, username, processid, architecture)
    print("Connect Upload: {}".format(serverId))

    # Start data flowing
    r = yield from daliDownload.stream()
    while(keepGoing):
        dlPacket = yield from daliDownload.parseResponse()
        if dlPacket.streamId.endswith("MSEED"):
            # check in case we mess up and get non-miniseed packets
            mseedRecord = simpleMiniseed.unpackMiniseedRecord(dlPacket.data)
            # in data array as integers
            inData = mseedRecord.data
            starttime = mseedRecord.header.starttime
            outputSampleRate = mseedRecord.header.samprate
            net = mseedRecord.header.network
            sta = mseedRecord.header.station
            loc = mseedRecord.header.location
            # fake channel, but use orientation code
            chan = "TJ"+mseedRecord.header.channel[2]
            # do something with the integers
            # this just creates a new array with the same data
            # modify outputData if needed
            outputData = array('h', inData)
            for i in range(len(intDataArray)):
                outputData[i] = inData[i]
            # if data is ready to ship out, maybe
            dBuf = getDataBuffer(net, sta, loc, chan, outputSampleRate, daliUpload)
            dBuf.push(starttime, outputDataArray)
        print("parseResponse {} ".format(trig.type))
        print("Trigger: {}  {}".format(trig, json.dumps(json.loads(trig.data), indent=4)))
    for key, db in dataBuffers..items():
        db.flush() # just in case some data has not been sent
    daliDownload.close()
    daliUpload.close()


loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(doTest(loop))
loop.close()
