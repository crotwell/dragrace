import simpleDali
import simpleMiniseed
import dataBuffer
import asyncio
import logging
import signal
import sys
import json
import math
from datetime import datetime, timedelta
from array import array
import SeismogramTasks

#logging.basicConfig(level=logging.DEBUG)


host = "129.252.35.36"
port = 15003
#port = 15004

#host = "129.252.35.20"
#host = "127.0.0.1"
#port = 6382
uri = "ws://www.seis.sc.edu/dragracews/datalink"

STREAM_PATTERN = ".*PI.*/MSEED"

programname="makePeakAccelerationTrace"
username="dragrace"
#username="replayrace"
processid=0
architecture="python"

keepGoing = True
verbose = False

replay = False
if replay:
    STREAM_PATTERN = ".*PI.*/MSEED"
    port = 15004
    username="replayrace"

# -1 means run forever, otherwise stop after MAX_COUNT packets, for testing
MAX_COUNT=-1

COUNTS_PER_G=4096

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
    daliDownload = simpleDali.SocketDataLink(host, port)
    #daliDownload = simpleDali.WebSocketDataLink(uri)
    #daliDownload.verbose = True
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
    daliUpload = simpleDali.SocketDataLink(host, port)
    #daliUpload = simpleDali.WebSocketDataLink(uri)
    #daliUpload.verbose = True
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

def CompareHeaders(dlPacket1,dlPacket2):
    global daliUpload
#    print(dlPacket1.streamId)
    print(dlPacket2.streamId)
    if dlPacket1.streamId.endswith("MSEED"):
        if dlPacket2.streamId.endswith("MSEED"):
            mseedRecord1 = simpleMiniseed.unpackMiniseedRecord(dlPacket1.data)
            mseedRecord2 = simpleMiniseed.unpackMiniseedRecord(dlPacket2.data)
            if mseedRecord1.header.station == mseedRecord2.header.station:
                print("same station ", mseedRecord1.header.station)
                if mseedRecord1.header.channel != mseedRecord2.header.channel:
                    print("channels: ", mseedRecord1.header.channel, mseedRecord2.header.channel)
                    if mseedRecord1.header.starttime == mseedRecord2.header.starttime:
                        print("same start time ... keep them")
                        return True
                    else:
                        diff=mseedRecord2.header.starttime - mseedRecord1.header.starttime
                        print("Time difference: ", diff)
                        return False

def buildPacketKey(ThePacket,RootChan):
    mSeed = simpleMiniseed.unpackMiniseedRecord(ThePacket.data)
    StartTime = mSeed.header.starttime
    sampleRate = mSeed.header.sampleRate
    net = mSeed.header.network
    sta = mSeed.header.station
    loc = mSeed.header.location
    chan = mSeed.header.channel[0:2]
    Orient = mSeed.header.channel[2]
#    print("Orientation",Orient)
#    print("RootChannel",chan)
    if chan != RootChan:
        return "NotRootChan", Orient, StartTime
    key=net + "." + sta + "." + loc + "." + chan
#    print("KEY: ", key)
#    print("Start Time: ", StartTime)
    return key, Orient, StartTime, sta

def matchingPackets(ThePacket,orientation,starttime):
    mSeed = simpleMiniseed.unpackMiniseedRecord(ThePacket.data)
    if starttime == mSeed.header.starttime:
        if orientation != mSeed.header.channel[2]:
            return True
        else:
            return False
    else:
        return False

def calculatePacketPeakMagnitude(Components):
    firstPass=True
    for ThePacket in Components:
        mseed=simpleMiniseed.unpackMiniseedRecord(ThePacket.data)
        data=mseed.data
        if firstPass:
            datasqrd=[]
            npts=len(data)
        if len(data) != npts:
            print("NPTS mismatch, returning negative max")
            return -1, npts
        i=0
        #print(data[12])
        while i < len(data):
            if firstPass:
                thedata=[]
                datasqrd.append(data[i]*data[i])
            else:
                datasqrd[i]=datasqrd[i]+(data[i]*data[i])
            i=i+1
        firstPass=False
    i=0
    while i < len(data):
        datasqrd[i]=math.sqrt(datasqrd[i])
        i=i+1
    return max(datasqrd), npts

def doTest():
    global keepGoing
    global daliDownload
    global daliUpload
    loop = asyncio.get_event_loop()
    loop.set_debug(True)


#    initTask = loop.create_task(initConnections(".*PI04.*HNZ/MSEED"))
    initTask = loop.create_task(initConnections(STREAM_PATTERN))
    loop.run_until_complete(initTask)

    packetDictionary={}
    packetCount=0
    Components=[]
    match_count=1
    GotAllThree=False
#    print("Entering test ... Initializing Components", match_count)

    while(keepGoing):
#        print("inside keepGoing loop")
        dlPacket = getNextPacket()
        try:
            key,orientation,starttime,station=buildPacketKey(dlPacket,"HN")
            if verbose:
                print("Got another packet: ", key,orientation,starttime)
            if not key in packetDictionary:
    #            print("     New Key: ", key,orientation,starttime)
                packetDictionary[key]=[]
                packetDictionary[key].append(dlPacket)
            else:
               Components.append(dlPacket)
               for value in packetDictionary[key]:
                    if matchingPackets(value,orientation,starttime):
        #                print("     A match: ",value,orientation,starttime)

                        Components.append(value)
                        match_count=match_count + 1
    #                    print("B ... putting value in Components",match_count,key)
                    if match_count == 3:
                        for ThePacket in Components:
                            mSeed = simpleMiniseed.unpackMiniseedRecord(ThePacket.data)
                            thedata=mSeed.data
                            StartTime = mSeed.header.starttime
                            sta = mSeed.header.station
                            Orient = mSeed.header.channel[2]
        #                print("Got 3 components at the same time and station ... WooHoo")
                        GotAllThree=True
    #                    print("Component Length",len(Components))
                        #print(Components)
                        maxMag, npts_packet=calculatePacketPeakMagnitude(Components)
        #
        # TEMPORARY FIR FIlter # FIXME:
        #
                        maxMag=maxMag / COUNTS_PER_G
                        streamid = "{}.{}/MAXACC".format("XX", station)
                        hpdatastart = simpleDali.datetimeToHPTime(starttime)
                        hpdataend = simpleDali.datetimeToHPTime(starttime)
                        jsonMessage = {
                            "station": station,
                            "time": starttime.isoformat(),
                            "accel": maxMag
                        }
                        if verbose:
                            print("Send json max: {}".format(jsonMessage["accel"]));
                        writeJsonToDatalink(streamid, hpdatastart, hpdataend, jsonMessage)
                        jsonMessage={}
                        packetDictionary[key].append(dlPacket)
                        for UsedPacket in Components:
                            packetDictionary[key].remove(UsedPacket)
               match_count=1
               if not GotAllThree:
                   packetDictionary[key].append(dlPacket)
               GotAllThree=False
               Components=[]

            packetCount+=1
            if MAX_COUNT > 0 and packetCount>MAX_COUNT:
                keepGoing=False
        except Exception as e:
            print("Got bad miniseed record, skipping..."+e)
    for key, db in dataBuffers.items():
#            for key, db in dataBuffers.items():
        # just in case some data has not been sent
        db.flush()
            #
    daliDownload.close()
    daliUpload.close()
    loop.close()

# main
print("starting....")
doTest()
print("after doTest()")
