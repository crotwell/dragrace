#!/usr/bin/python3

# Simple demo of fifo mode on the MMA8451.
# Author: Philip Crotwell
import time
import struct
import queue
from threading import Thread
from datetime import datetime, timedelta
import sys, os, signal
from pathlib import Path
import asyncio
import traceback
import faulthandler

faulthandler.enable()

#import logging
#logging.basicConfig(filename='xbee.log',level=logging.DEBUG)

import board
import busio

import adafruit_mma8451
import RPi.GPIO as GPIO

import simpleMiniseed
import simpleDali
import dataBuffer
import decimate

daliHost="129.252.35.36"
daliPort=15003
dali=None

pin = 18  # GPIO interrupt
#MAX_SAMPLES = 2000
MAX_SAMPLES = -1
#MAX_SAMPLES = 1

doDali = True
doArchive = True
doFIR = True
decimationFactor = 1
if doFIR:
    decimationFactor = 2

quitOnError = True

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
    decimateMap = {
        "X":decimate.DecimateTwo(),
        "Y":decimate.DecimateTwo(),
        "Z":decimate.DecimateTwo(),
    }

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
    print("starting worker")

    time.sleep(5)
    global keepGoing
    global startACQ
    global dataQueue
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
                print("Exception sending packet: {}".format(err))
                traceback.print_exc()
                if dali:
                    # if at first you don't suceed, try try again
                    dali.reconnect()
                    try:
                        do_work( now, status, samplesAvail, data)
                        dataQueue.task_done()
                    except Exception as err:
                        dataQueue.task_done()
                        print("2nd Exception sending packet: {}".format(err))
                        traceback.print_exc()
                        if quitOnError:
                            keepGoing = False
        except queue.Empty:
            print("no data in queue??? startACQ={0:b}".format(startACQ))
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

def sendToMseed(now, status, samplesAvail, data):
    global staString
    global sta
    global net
    global loc
    global chanMap
    dataIdx = 0
    start = now - timedelta(seconds=1.0*(samplesAvail-1)/sps)
    xData, yData, zData = sensor.demux(data)
    if doFIR:
        start = start - decimateMap["X"].FIR.calcDelay(sps)
        xData = decimateMap["X"].process(xData)
        yData = decimateMap["Y"].process(yData)
        zData = decimateMap["Z"].process(zData)

    loop = asyncio.get_event_loop()
    ztask = loop.create_task(doMiniseedBuffer(miniseedBuffers[chanMap["Z"]], start, zData))
    loop.run_until_complete(ztask)
    ytask = loop.create_task(doMiniseedBuffer(miniseedBuffers[chanMap["Y"]], start, yData))
    loop.run_until_complete(ytask)
    xtask = loop.create_task(doMiniseedBuffer(miniseedBuffers[chanMap["X"]], start, xData))
    loop.run_until_complete(xtask)
    return [xtask, ytask, ztask]
    # return [
    #     await miniseedBuffers[chanMap["X"]].push(start, xData),
    #     await miniseedBuffers[chanMap["Y"]].push(start, yData),
    #     await miniseedBuffers[chanMap["Z"]].push(start, zData)
    # ]

@asyncio.coroutine
def doMiniseedBuffer(miniseedBuf, start, data):
    r = miniseedBuf.push(start, data)
    return r

def decimate(decimator, data):
    out = []
    for v in data:
        out.append(decimator.pushPop(v))
    return out

def initDali(host, port):
    print("Init Dali at {0}:{1:d}".format(host, port))
    dl = simpleDali.DataLink(host, port)
    return dl

def getLocalHostname():
    with open("/etc/hostname") as hF:
        hostname = hF.read()
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
    if sensor is not None:
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




signal.signal(signal.SIGTERM, handleSignal)
signal.signal(signal.SIGINT, handleSignal)
sta = getLocalHostname()[0:5].upper()
print("set station code to {}".format(sta))

if doDali:
    try:
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


dataQueue = queue.Queue()
print("before create thead")
sendThread = Thread(target = sending_worker)
sendThread.daemon=True
print("thread start")
sendThread.start()
time.sleep(3)
print("after thread start sleep")

try:
    print('task creation started')
    before = time.perf_counter()
    sensor.enableFifoBuffer(28, pin, dataCallback)
    sps = getSps()
    gain = getGain()

    while keepGoing:
        line = sys.stdin.readline()
        if (line.startswith("q")):
            keepGoing = False
            break
        time.sleep(0.1)
    print("before sendThread.join()")

    sendThread.join()
    print("after sendThread.join()")

finally:
    doQuit()
    print("main finally")
    #cleanUp()
print("Main thread done")
