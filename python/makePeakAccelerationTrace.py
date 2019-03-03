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
    daliUpload = simpleDali.DataLink(host, port)
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

def CompareHeaders(dlPacket1,dlPacket2):
    global daliUpload
#    print(dlPacket1.streamId)
#    print(dlPacket2.streamId)
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
        #starttime = mseedRecord.header.starttime
        #outputSampleRate = mseedRecord.header.samprate
        #net = mseedRecord.header.network
        #sta = mseedRecord.header.station
        #loc = mseedRecord.header.location
        #chan = mseedRecord.header.channel
        # fake channel, but use orientation code
        #chan = "TJ"+mseedRecord.header.channel[2]
        #outputData = array('h', inData)
#        for i in range(len(inData)):
#                print("i= , data= {}".format(i,outputData[i]))
#            outputData[i] = inData[i]
        # if data is ready to ship out, maybe
#        dBuf = getDataBuffer(net, sta, loc, chan, outputSampleRate, daliUpload)
#        dBuf.push(starttime, outputData)

def doTest():
    global keepGoing
    global daliDownload
    global daliUpload
    loop = asyncio.get_event_loop()
    loop.set_debug(True)


#    initTask = loop.create_task(initConnections(".*PI04.*HNZ/MSEED"))
    initTask = loop.create_task(initConnections(".*PI.*/MSEED"))
    loop.run_until_complete(initTask)

    packetCount=0
    while(keepGoing):
        print("inside keepGoing loop")
        dlPacket1 = getNextPacket()
        dlPacket2 = getNextPacket()
        while(not CompareHeaders(dlPacket1,dlPacket2)):
            dlPacket2 = getNextPacket()
        dlPacket3 = getNextPacket()
        while( not CompareHeaders(dlPacket1,dlPacket3)):
            dlPacket3 = getNextPacket()
    #
    # OK, get the data
    #
        print("Got 3 components at the same time and station ... WooHoo")
        Packet1 = simpleMiniseed.unpackMiniseedRecord(dlPacket1.data)
        Packet2 = simpleMiniseed.unpackMiniseedRecord(dlPacket2.data)
        Packet3 = simpleMiniseed.unpackMiniseedRecord(dlPacket3.data)
        P1data=Packet1.data
    #    print(P1data[0])
        P2data=Packet2.data
        P3data=Packet3.data
        npts=len(P1data)
    #    print("NPTS ...",npts)
        i=0
        maxMag=0
        while i < npts:
            PacketMag=math.sqrt(P1data[i]*P1data[i]+P2data[i]*P2data[i]+P3data[i]*P3data[i])
            if PacketMag > maxMag:
                maxMag = PacketMag
            i=i+1
        #PacketMag=SeismogramTasks.Magnitude_ThreeC_TimeSeries(P1data,P2data,P3data)
        #PacketMaximum=max(PacketMag)
        print("Maximum Magnitude for this packet: ",maxMag)

        packetCount+=1
        if packetCount>15:
            keepGoing=False
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
