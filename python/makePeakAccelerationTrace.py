import simpleDali
import simpleMiniseed
import dataBuffer
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

programname="makePeakAccelerationTrace"
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

# Stuff above here is from Philip, all I changed was the programname.
# Base code is dailReadWrite.py, which I did not test, just did a Save As...

dataBuffers = {}

def getDataBuffer(net, sta, loc, chan, outputSampleRate, outputDali):
    # changed all . in key to _, per recollection of class conversation
    key = "{}.{}.{}.{}".format(net, sta, loc, chan)
    if not key in dataBuffers:
        dataBuffers[key] = dataBuffer.DataBuffer(net, sta, loc, chan,
                     outputSampleRate, encoding=simpleMiniseed.ENC_SHORT,
                     dali=outputDali)
        # dataBuffers[key].
    return dataBuffers[key]

async def initConnections(matchPattern):
    global daliDownload
    global daliUpload
    daliDownload = simpleDali.DataLink(host, port)
    daliDownload.verbose = True
    serverId = await daliDownload.id(programname, username, processid, architecture)
    print("Connect Download: {}".format(serverId))
    serverInfo = await daliDownload.info("STATUS")
    print("Info STATUS: {} ".format(serverInfo.message))
    #serverInfo = await dali.info("STREAMS")
    #print("Info: {} ".format(serverInfo.message))
    #
    # match all MSEED streams
    #r = await dali.match(".*/MSEED")
    # or match just 3605 HNZ
    r = await daliDownload.match(matchPattern)
    print("match() Response {}".format(r))

    # create a separate upload datalink
    daliUpload = simpleDali.DataLink(host, port)
    daliUpload.verbose = True
    serverId = await daliUpload.id(programname, username, processid, architecture)
    print("Connect Upload: {}".format(serverId))
    # Start data flowing
    r = await daliDownload.stream()
    print("data is flowing")


def getNextPacket():
    loop = asyncio.get_event_loop()
    packetTask = loop.create_task(daliDownload.parseResponse())
    loop.run_until_complete(packetTask)
    dlPacket = packetTask.result()
    return dlPacket

def writeJsonToDatalink(streamid, hpdatastart, hpdataend, jsonMessage):
    jsonAsByteArray = json.dumps(jsonMessage).encode('UTF-8')
    loop = asyncio.get_event_loop()
    jsonSendTask = loop.create_task(daliUpload.writeAck(streamid, hpdatastart, hpdataend, jsonAsByteArray))
    loop.run_until_complete(jsonSendTask)
    return jsonSendTask.result()

def processDLPacket(dlPacket):
    global daliUpload
    print(dlPacket.streamId)
    if dlPacket.streamId.endswith("MSEED"):
        print("got a miniseed packet")
        # check in case we mess up and get non-miniseed packets
        mseedRecord = simpleMiniseed.unpackMiniseedRecord(dlPacket.data)
        print("got past the unpacking")
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
        maxValue = 0
        for i in range(len(inData)):
#                print("i= , data= {}".format(i,outputData[i]))
            outputData[i] = inData[i]
            if inData[i] > maxValue:
                maxValue = inData[i]
        # if data is ready to ship out, maybe
        dBuf = getDataBuffer(net, sta, loc, chan, outputSampleRate, daliUpload)
        dBuf.push(starttime, outputData)
        #
        # ...or, to send a non-miniseed datalink packet
        # although you probably want this to be max within a timewindow
        # like one second instead of max within the miniseed record
        #
        streamid = "{}.{}.{}.{}/MAX".format(net, sta, loc, chan)
        hpdatastart = int(starttime.timestamp() * simpleDali.MICROS)
        hpdataend = int(starttime.timestamp() * simpleDali.MICROS)
        jsonMessage= {
            "type": "minmax",
            "time": starttime.isoformat(),
            "creation": starttime.isoformat(),
            "maxValue": maxValue
        }
        ack = writeJsonToDatalink(streamid, hpdatastart, hpdataend, jsonMessage)
        print("send max = {:d} as json, {}".format(maxValue, ack))

def doTest():
    global keepGoing
    global daliDownload
    global daliUpload
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    initTask = loop.create_task(initConnections(".*PI04.*HNZ/MSEED"))
    loop.run_until_complete(initTask)

    packetCount=0
    while(keepGoing):
        print("inside keepGoing loop")
        dlPacket = getNextPacket()
        processDLPacket(dlPacket)
#        print("parseResponse {} ".format(trig.type))
#        print("Trigger: {}  {}".format(trig, json.dumps(json.loads(trig.data), indent=4)))
        packetCount+=1
        if packetCount>15:
            keepGoing=False
    for key, db in dataBuffers.items():
        # just in case some data has not been sent
        db.flush()
    daliDownload.close()
    daliUpload.close()
    loop.close()

# main
print("starting....")
doTest()
print("after doTest()")
