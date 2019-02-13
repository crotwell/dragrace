#!/usr/bin/python3

# Simple demo of fifo mode on the MMA8451.
# Author: Philip Crotwell
import time
import struct
import queue
import threading
from datetime import datetime, timedelta
import sys, os
from pathlib import Path
import asyncio

#import logging
#logging.basicConfig(filename='xbee.log',level=logging.DEBUG)

import board
import busio

import adafruit_mma8451
import RPi.GPIO as GPIO
from digi.xbee.devices import XBeeDevice
#from digi.xbee.devices import ZigBeeDevice
from digi.xbee.models.address import XBee16BitAddress
from digi.xbee.exception import TimeoutException

import simpleMiniseed
import simpleDali

dali = None
daliMutex = threading.Lock()

daliHost="129.252.35.36"
daliPort=15003

pin = 18  # GPIO interrupt
#MAX_SAMPLES = 2000
MAX_SAMPLES = -1
#MAX_SAMPLES = 1

doDali = True

# Initialize I2C bus.
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize MMA8451 module.
sensor = adafruit_mma8451.MMA8451(i2c)
# Optionally change the address if it's not the default:
#sensor = adafruit_mma8451.MMA8451(i2c, address=0x1C)

# Optionally change the range from its default of +/-4G:
sensor.range = adafruit_mma8451.RANGE_2G  # +/- 2G
#sensor.range = adafruit_mma8451.RANGE_4G  # +/- 4G (default)
#sensor.range = adafruit_mma8451.RANGE_8G  # +/- 8G

# Optionally change the data rate from its default of 800hz:
#sensor.data_rate = adafruit_mma8451.DATARATE_800HZ  #  800Hz (default)
#sensor.data_rate = adafruit_mma8451.DATARATE_400HZ  #  400Hz
sensor.data_rate = adafruit_mma8451.DATARATE_200HZ  #  200Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_100HZ  #  100Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_50HZ   #   50Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_12_5HZ # 12.5Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_6_25HZ # 6.25Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_1_56HZ # 1.56Hz

sta="UNKNW"
net = "XX"
loc = "00"
chanList = [ "HNX", "HNY", "HNZ" ]


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
    global totalSamples
    global keepGoing
    global before
    global pin
    item = now, status, samplesAvail, data
    dataQueue.put(item)
    totalSamples += samplesAvail
    if (MAX_SAMPLES != -1 and totalSamples > MAX_SAMPLES):
        after = time.perf_counter()
        delta = after-before
        print("time take for {0:d} loops is {1:3.2f}, {2:d} samples at {3:3.2f} sps, nomSps={4:d}".format(loops, delta, totalSamples, (totalSamples-1)/delta, getSps()))
        sensor.reset()
        GPIO.remove_event_detect(pin)
        keepGoing = False

def worker():
    global keepGoing
    global startACQ
    global dataQueue
    global infoQueue
    while keepGoing:
        try:
            if not infoQueue.empty():
                doSendInfoPacket(infoQueue.get(timeout=2))
                infoQueue.task_done()
            item = dataQueue.get(timeout=2)
            if item is None or not keepGoing:
                print("Worker exiting")
                dataQueue.task_done()
                break
            now, status, samplesAvail, data = item
            try:
                do_work(now, status, samplesAvail, data)
                dataQueue.task_done
            except TimeoutException as err:
                # try once more?
                #do_work(now, status, samplesAvail, data)
                print("TimeoutException sending packet")
                dataQueue.task_done()
        except queue.Empty:
            print("no data in queue??? startACQ={0:b}".format(startACQ))
    print("Worker exited")


def do_work(now, status, samplesAvail, data):
    global daliMutex
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

    if status >= 128:
        print("overflow at loops={0:d}".format(loops))
    #preMsg = ""
    #if status >= 128:
    #    preMsg = "Overflow "
    #if status & 0x40 > 0:
    #    preMsg += "Watermark "
    #print("{0} load {1:d} samples: {2:b} {3:b}".format(preMsg, samplesAvail, (status & 128)>0, (status & 64)>0))
    dataOffset = 12
    dataPacket = bytearray(len(data)+dataOffset)
    dataPacket[0] = ord('A')
    dataPacket[1] = samplesAvail & 0xff;
    dataPacket[2:4] = now.year.to_bytes(2, byteorder='big')
    dataPacket[4:6] = now.timetuple().tm_yday.to_bytes(2, byteorder='big')
    dataPacket[6] = now.hour
    dataPacket[7] = now.minute
    dataPacket[8] = now.second
    dataPacket[9:11] = int(round(now.microsecond/1000)).to_bytes(2, byteorder='big')
    dataPacket[11] = sps
    dataPacket[dataOffset:dataOffset+len(data)] = data
    #sendToFile(now, dataPacket)
    sendToMseed(now, status, samplesAvail, data)

    sentSamples += samplesAvail
    #if sentSamples % 6000 == 0:
    if loops % 18 == 0:
          print("sent data async samplesSent={0:d} of {1:d} {2}".format(sentSamples, totalSamples, now.strftime("%Y-%m-%d %H:%M:%S")))
          #print("{0:d} {1:d} {2:d}:{3:d}:{4:d}.{5:3.3f}    sps={6:d}  npts={7:d}".format(now.year, now.timetuple().tm_yday, now.hour, now.minute, now.second, now.microsecond/1000, sps, samplesAvail));
          #xData, yData, zData = sensor.demux(data)
          #for i in range(len(xData)):
          #    print("  {0:d} {1:d} {2:d}".format(xData[i], yData[i], zData[i]))
    if sentSamples > 1000000:
          sentSamples = 0

def getDali():
    global daliPort
    global daliHost
    global dali, remote
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

def sendToMseed(now, status, samplesAvail, data):
    global staString
    global sta
    global net
    global loc
    global chanList
    dataIdx = 0
    start = now - timedelta(seconds=1.0*(samplesAvail-1)/sps)
    dataAsInt = struct.unpack('>'+'h'*3*samplesAvail, data)
    for chan in chanList:
        chanData = []
        for i in range(samplesAvail):
            # MMA8451 saves 14 bit data as 16 bit int but
            # bit shifted 2 bits to left, ie always mod 4 == 0
            # shift back to right so 1 count is 00000001
            # instead of 4, 00000100
            chanData.append( dataAsInt[3*i+dataIdx] >> 2 )

        miniseedBuffers[chan].push(start, chanData)
        dataIdx+=1

def initDali(host, port):
    print("Init Dali at {0}:{1:d}".format(host, port))
    dl = simpleDali.DataLink(host, port)
    return dl

def getLocalHostname():
    with open("/etc/hostname") as hF:
        hostname = hF.read()
    return hostname.strip()

sta = getLocalHostname()[0:5].upper()
print("set station code to {}".format(sta))

miniseedBuffers = dict()
for chan in chanList:
    miniseedBuffers[chan] = DataBuffer(net, sta, loc, chan,
             sps, encoding=simpleMiniseed.ENC_SHORT, dali=getDali())

dataQueue = queue.Queue()
infoQueue = queue.Queue()
sendThread = threading.Thread(target=worker)
sendThread.start()

try:
    before = time.perf_counter()
    sensor.enableFifoBuffer(30, pin, dataCallback)
    sps = getSps()
    gain = getGain()

    if doDali and dali == None:
        try:
            with daliMutex:
                dali = getDali()
        except ValueError as err:
            print("Unable to init DataLink at {0} {1:d}: {2}".format(daliHost, daliPort, err))

    # Main loop to print the acceleration and orientation every second.
    while keepGoing:
        line = sys.stdin.readline()
        if (line.startswith("q")):
            keepGoing = False
            break
        time.sleep(0.1)
except ValueError as err:
    print("   error: {0}".format(err))
except RuntimeError as err:
    print("Other Error: {0}".format(err))
    if (dali != None):
        dali.close()
    os._exit(1)  # harsh but must use os._exit as other threads keep alive

print("Quiting")
if sensor is not None:
    print("reset sensor")
    sensor.reset()
    print("remove gpio interrupt pin")
    GPIO.remove_event_detect(pin)


for buf in miniseedBuffers:
    buf.flush()

time.sleep(0.1)
print("join queue to wait for xbee worker to finish")
#dataQueue.join() # wait until any remaining data is sent
if dali is not None:
    print("close dali")
    dali.close()
