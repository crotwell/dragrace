#!/usr/bin/python3

# Simple demo of fifo mode on the MMA8451.
# Author: Philip Crotwell
import time
import json
import struct
import queue
from threading import Thread
from datetime import datetime, timedelta, timezone
import sys, os, signal
import socket
from pathlib import Path
import asyncio
import traceback
import faulthandler

from multiprocessing import Process, Queue, Pipe

from peakACC import peakAccelerationCalculation, compareSendPeakAccel

faulthandler.enable()

#import logging
#logging.basicConfig(filename='xbee.log',level=logging.DEBUG)

# to generate fake data as PI99 set to True
doFake = False
doReplay = False

if doFake:
    import fakeSensor
elif doReplay:
    import fakeSensor
    import replaySensor
else:
    # real thing
    import board
    import busio
    import RPi.GPIO as GPIO
    import adafruit_mma8451

import simpleMiniseed
import simpleDali
import dataBuffer
import decimate


daliHost="129.252.35.36"
daliPort=15003
dali=None
uri = "ws://www.seis.sc.edu/dragracews/datalink"

pin = 18  # GPIO interrupt
#MAX_SAMPLES = 2000
MAX_SAMPLES = -1
#MAX_SAMPLES = 1

doDali = True
doArchive = True
doFIR = True
doMultiprocess = True
decimationFactor = 1
if doFIR:
    decimationFactor = 2

quitOnError = True

if not doFake and not doReplay:
    # Initialize I2C bus.
    i2c = busio.I2C(board.SCL, board.SDA)

    # Initialize MMA8451 module.
    sensor = adafruit_mma8451.MMA8451(i2c)
    # Optionally change the address if it's not the default:
    #sensor = adafruit_mma8451.MMA8451(i2c, address=0x1C)

    print("reset sensor")
    sensor.reset()
    print("remove gpio interrupt pin")
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.remove_event_detect(pin)
else:
    if doFake:
        sensor = fakeSensor.FakeSensor()
    else:
        ############################################
        # values to change:
        dataDir="Track_Data"
        netGlob = "XX"
        staGlob = "XB08"
        locGlob = "00"
        chanGlob = "HN[XYZ]"
        # if need seconds add :%S
        startTime = datetime.strptime("2018-10-14T11:00Z", "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
        duration = timedelta(hours=2)
        staRemap = {
            'XB02': 'PI02',
            'XB03': 'PI03',
            'XB05': 'PI05',
            'XB08': 'PI05',
            'XB10': 'PI10'
        }
        #elf.duration = timedelta(seconds=20)
        repeat = True
        # end values to change
        ############################################
        replaySta = staRemap[staGlob]
        sensor = replaySensor.ReplaySensor(dataDir, netGlob, staGlob, locGlob, chanGlob, startTime, staRemap, duration=None)
        sensor.verbose = True
        doFIR = False
    adafruit_mma8451 = fakeSensor.FakeAdafruit()

# Optionally change the range from its default of +/-4G:
sensor.range = adafruit_mma8451.RANGE_2G  # +/- 2G
#sensor.range = adafruit_mma8451.RANGE_4G  # +/- 4G (default)
#sensor.range = adafruit_mma8451.RANGE_8G  # +/- 8G

# Optionally change the data rate from its default of 800hz:
#sensor.data_rate = adafruit_mma8451.DATARATE_800HZ  #  800Hz (default)
sensor.data_rate = adafruit_mma8451.DATARATE_400HZ  #  400Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_200HZ  #  200Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_100HZ  #  100Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_50HZ   #   50Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_12_5HZ # 12.5Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_6_25HZ # 6.25Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_1_56HZ # 1.56Hz

sta="UNKNW"
net = "XX"
loc = "00"
chanMap = { "X":"HNX", "Y":"HNY", "Z":"HNZ"}
decimateMap = {}
if doFIR:
    if doMultiprocess:
        decimateMap = {
            "X":decimate.DecimateTwoSubprocess(),
            "Y":decimate.DecimateTwoSubprocess(),
            "Z":decimate.DecimateTwoSubprocess(),
        }
    else:
        decimateMap = {
            "X":decimate.DecimateTwo(),
            "Y":decimate.DecimateTwo(),
            "Z":decimate.DecimateTwo(),
        }
establishedJson = None
maxWindow = timedelta(seconds=0.25)
theta = 70.0
alpha = 0.0

def getSps():
    sps = 1
    if sensor.data_rate == adafruit_mma8451.DATARATE_800HZ:
        sps = 800
    elif sensor.data_rate == adafruit_mma8451.DATARATE_400HZ:
        sps = 400
    elif sensor.data_rate == adafruit_mma8451.DATARATE_200HZ:
        sps = 200
    elif sensor.data_rate == adafruit_mma8451.DATARATE_100HZ:
        sps = 100
    elif sensor.data_rate == adafruit_mma8451.DATARATE_50HZ:
        sps = 50
    return sps

def getGain():
    gain = 0
    if sensor.range == adafruit_mma8451.RANGE_2G:
        gain = 2
    elif sensor.range == adafruit_mma8451.RANGE_4G:
        gain = 4
    elif sensor.range == adafruit_mma8451.RANGE_8G:
        gain = 8
    return gain


before = time.perf_counter()
after = before
totalSamples = 0
sentSamples = 0
loops = 0
keepGoing = True
curFile = None
curFilename = None
startACQ = False
sps = 0
gain = 0

def dataCallback(now, status, samplesAvail, data):
    item = now, status, samplesAvail, data
    dataQueue.put(item)

def sending_worker():
    try:
        print("starting worker")

        global keepGoing
        global startACQ
        global dataQueue
        global sps
        my_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(my_loop)
        my_loop.set_debug(True)

        if dali:
            programname="MMA8451ToMseed"
            username="me"
            processid="0"
            architecture="python"
            task = my_loop.create_task(dali.id( programname, username, processid, architecture))
            my_loop.run_until_complete(task)
            r = task.result()
            print("id respones {}".format(r))
        while keepGoing:
            try:
                item = dataQueue.get(timeout=2)
                if item is None or not keepGoing:
                    print("Worker exiting")
                    dataQueue.task_done()
                    break
                now, status, samplesAvail, data = item
                try:
                    do_work( now, status, samplesAvail, data)
                    dataQueue.task_done()
                except Exception as err:
                    # try once more?
                    #do_work(now, status, samplesAvail, data)
                    print("Exception sending packet: {}".format(err), file=sys.stderr)
                    traceback.print_exc()
                    if dali:
                        # if at first you don't suceed, try try again
                        time.sleep(3)
                        task = my_loop.create_task(dali.reconnect())
                        my_loop.run_until_complete(task)
                        r = task.result()
                        print("reconnect respones {}".format(r))
                        try:
                            do_work( now, status, samplesAvail, data)
                            dataQueue.task_done()
                        except Exception as err:
                            dataQueue.task_done()
                            print("2nd Exception sending packet: {}".format(err), file=sys.stderr)
                            traceback.print_exc()
                            if quitOnError:
                                keepGoing = False
            except queue.Empty:
                print("no data in queue??? startACQ={0:b}".format(startACQ))
    except Exception as err:
        keepGoing = False
        print("send thread fail on {}".format(err), file=sys.stderr)
        traceback.print_exc()
    print("Worker exited")
    cleanUp()
    asyncio.get_event_loop().close()


def do_work(now, status, samplesAvail, data):
    global startACQ
    global totalSamples
    global sentSamples
    global loops
    global before
    global pin
    global keepGoing
    global after
    global sps
    loops += 1
    #print("status: {0:d} {0:08b} samps: {1:d} len(data): {2:d} queue: {3:d}".format(status, samplesAvail, len(data), dataQueue.qsize()))
    if status >>7 != 0:
        print("overflow at loops={0:d}".format(loops))
    if len(data) < samplesAvail:
        raise Exception("Not enough samples avail: len={:d}, sampsAvail={:d}".format(len(data), samplesAvail))
    sendResult = None
    if samplesAvail != 0:
        sendResult =  sendToMseed(now, status, samplesAvail, data)
        totalSamples += samplesAvail
        if (MAX_SAMPLES != -1 and totalSamples > MAX_SAMPLES):
            after = time.perf_counter()
            delta = after-before
            print("time take for {0:d} loops is {1:3.2f}, {2:d} samples at {3:3.2f} sps, nomSps={4:d}".format(loops, delta, totalSamples, (totalSamples-1)/delta, getSps()))
            sensor.reset()
            GPIO.remove_event_detect(pin)
            keepGoing = False
    return sendResult

def getDali():
    global daliPort
    global daliHost
    global dali, doDali
    if (doDali and dali is None):
        dali = initDali(daliHost, daliPort)
    return dali

def sendToFile(now, dataPacket):
    global curFile
    global curFilename
    filename = now.strftime("data_%Y-%m-%d_%H")
    if curFilename != filename:
        if curFile != None:
            curFile.close()
        curFile = open(filename, "ab")
    curFile.write(dataPacket)
    return "write to {}".format(filename)

def sendToMseed(last_sample_time, status, samplesAvail, data):
    global staString
    global sta
    global net
    global loc
    global chanMap
    global establishedJson
    global maxWindow
    global theta
    global alpha
    global sps
    global firDelay
    dataIdx = 0
    start = last_sample_time - timedelta(seconds=1.0*(samplesAvail-1)/sps)
    xData, yData, zData = sensor.demux(data)
    if doFIR:
        start = start - firDelay
        if doMultiprocess:
            decimateMap["X"].process(xData)
            decimateMap["Y"].process(yData)
            decimateMap["Z"].process(zData)
            xData = decimateMap["X"].results()
            yData = decimateMap["Y"].results()
            zData = decimateMap["Z"].results()
        else:
            xData = decimateMap["X"].process(xData)
            yData = decimateMap["Y"].process(yData)
            zData = decimateMap["Z"].process(zData)

    freshJson = peakAccelerationCalculation(xData,yData,zData,theta,alpha,sta,start,last_sample_time)
    establishedJson = compareSendPeakAccel(establishedJson, freshJson, getDali(), maxWindow)

    miniseedBuffers[chanMap["Z"]].push(start, zData)
    miniseedBuffers[chanMap["Y"]].push(start, yData)
    miniseedBuffers[chanMap["X"]].push(start, xData)
    print("sendToMseed {} {} {}".format(sta, start, len(xData)))

def initDali(host, port):
    print("Init Dali at {0}:{1:d}".format(host, port))
    dl = simpleDali.SocketDataLink(host, port)
    return dl

def getLocalHostname():
    if not doFake:
        hostname = socket.gethostname().split('.')[0]
    else:
        hostname = 'PI99'
    #with open("/etc/hostname") as hF:
    #    hostname = hF.read()
    return hostname.strip()

def handleSignal(sigNum, stackFrame):
    print("############ handleSignal {} ############".format(sigNum))
    doQuit()

def doQuit():
    global keepGoing
    if keepGoing:
        keepGoing = False
    else:
        sys.exit(0)

def cleanUp():
    global keepGoing
    keepGoing = False
    if sensor is not None:
        if not doFake:
            print("remove gpio interrupt pin")
            GPIO.remove_event_detect(pin)
        print("reset sensor")
        sensor.reset()
    for key in miniseedBuffers:
        try:
            miniseedBuffers[key].close()
        except Exception as err:
            print(err)
    if (dali != None):
        dali.close()

def busyWaitStdInReader():
    global keepGoing
    while keepGoing:
        line = sys.stdin.readline()
        if (line.startswith("q")):
            keepGoing = False
            break
        time.sleep(1.0)

async def getConfig():
    # FIX... only gets one packet and then stops listening
    global daliPort
    global daliHost
    configDali = initDali(daliHost, daliPort)
    await configDali.match("/ZMAXCFG")
    await configDali.positionAfter(simpleDali.utcnowWithTz()-timedelta(seconds=90))
    await configDali.stream()
    while(True):
        print("wait for packets")
        peakPacket = await configDali.parseResponse()
        print("got a packet: {}".format(peakPacket.streamId,))
        if  peakPacket.streamId.endswith("ZMAXCFG"):
            config = json.loads(peakPacket.data.decode("'UTF-8'"))
            await configDali.close()
            return config

signal.signal(signal.SIGTERM, handleSignal)
signal.signal(signal.SIGINT, handleSignal)
hostname = getLocalHostname()[0:5].upper()
sta = hostname
if doReplay:
    hostname = replaySta
print("set station code to {}".format(sta))

sps = getSps()
firDelay = decimate.DecimateTwo().FIR.calcDelay(sps)
gain = getGain()

if doDali:
    try:
        loop = asyncio.get_event_loop()
        print("Try to get station from config via dali")
        configTask = loop.create_task(getConfig())
        loop.run_until_complete(configTask)
        config = configTask.result()
        if hostname in config["Location"]:
            sta = config["Location"][hostname]
            print("set station code from config to {}".format(sta))
        else:
            print("host not in config, keep default name {}".format(sta))

        print("try to init dali")
        dali = getDali()
        print("init DataLink at {0} {1:d}".format(daliHost, daliPort))
    except ValueError as err:
        raise Exception("Unable to init DataLink at {0} {1:d}: {2}".format(daliHost, daliPort, err))


miniseedBuffers = dict()
for key, chan in chanMap.items():
    miniseedBuffers[chan] = dataBuffer.DataBuffer(net, sta, loc, chan,
             getSps()/decimationFactor, archive=doArchive,
             encoding=simpleMiniseed.ENC_SHORT, dali=dali,
             continuityFactor=5)


stdinThread = Thread(target = busyWaitStdInReader)
stdinThread.daemon=True
print("stdinThread start")
stdinThread.start()

dataQueue = queue.Queue()
print("before create thead")
sendThread = Thread(target = sending_worker)
sendThread.daemon=True
print("thread start")
sendThread.start()
time.sleep(1)
print("after thread start sleep")

try:
    print('task creation started')
    before = time.perf_counter()
    sensor.enableFifoBuffer(28, pin, dataCallback)

    while keepGoing:
        time.sleep(0.1)
    print("before sendThread.join()")

    sendThread.join()
    print("after sendThread.join()")

finally:
    doQuit()
    print("main finally")
    #cleanUp()
print("Main thread done")
