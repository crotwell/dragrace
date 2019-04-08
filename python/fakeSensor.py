#!/usr/bin/python3

# Simple demo of fifo mode on the MMA8451.
# Author: Philip Crotwell
import time
import math
import struct
import queue
from threading import Thread
from datetime import datetime, timedelta, timezone
import sys, os, signal
from pathlib import Path
import asyncio
import traceback
import faulthandler

class FakeAdafruit:
    def __init__(self):
        self.RANGE_8G         = 0b10   # +/- 8g
        self.RANGE_4G         = 0b01   # +/- 4g (default value)
        self.RANGE_2G         = 0b00   # +/- 2g
        self.DATARATE_800HZ   = 0b000  #  800Hz
        self.DATARATE_400HZ   = 0b001  #  400Hz
        self.DATARATE_200HZ   = 0b010  #  200Hz
        self.DATARATE_100HZ   = 0b011  #  100Hz
        self.DATARATE_50HZ    = 0b100  #   50Hz
        self.DATARATE_12_5HZ  = 0b101  # 12.5Hz
        self.DATARATE_6_25HZ  = 0b110  # 6.25Hz
        self.DATARATE_1_56HZ  = 0b111  # 1.56Hz


class FakeSensor:
    def __init__(self):
        self.adafruit_mma8451 = FakeAdafruit()
        self.keepGoing = True
        self.sinePeriod = 20
        self.data_rate = self.adafruit_mma8451.DATARATE_400HZ  #  400Hz
        self.range = self.adafruit_mma8451.RANGE_2G  # +/- 2G
        self.sensorThread = Thread(target = self.generateFakeData)
        self.sensorThread.daemon=True
        time.sleep(1)
    def reset(self):
        self.keepGoing = False
    def enableFifoBuffer(self, watermark, pin, dataCallback):
        self.watermark = watermark
        self.pin = pin
        self.callback = dataCallback
        print("sensor thread start")
        self.sensorThread.start()
    def getSps(self):
        sps = 1
        if self.data_rate == self.adafruit_mma8451.DATARATE_800HZ:
            sps = 800
        elif self.data_rate == self.adafruit_mma8451.DATARATE_400HZ:
            sps = 400
        elif self.data_rate == self.adafruit_mma8451.DATARATE_200HZ:
            sps = 200
        elif self.data_rate == self.adafruit_mma8451.DATARATE_100HZ:
            sps = 100
        elif self.data_rate == self.adafruit_mma8451.DATARATE_50HZ:
            sps = 50
        return sps

    def getGain(self):
        gain = 0
        if self.range == self.adafruit_mma8451.RANGE_2G:
            gain = 2
        elif self.range == self.adafruit_mma8451.RANGE_4G:
            gain = 4
        elif self.range == self.adafruit_mma8451.RANGE_8G:
            gain = 8
        return gain

    def demux(self, data):
        x = []
        y = []
        z = []
        i = 0
        while i < len(data):
            x.append(data[i])
            y.append(data[i+1])
            z.append(data[i+2])
            i+=3
        return x, y, z

    def generateFakeData(self):
        idx = 0
        sps = self.getSps()
        gain = self.getGain()
        sleepTime = 1.0*self.watermark/sps
        packetWidth = timedelta(seconds=sleepTime)
        lastTime = now = datetime.now(timezone.utc)
        print("sleep for {} seconds per chunk {}".format(sleepTime, self.watermark))
        while self.keepGoing:
            time.sleep(sleepTime)
            # change method here to get different type of fake data
            data = self.createFakeConstantUp(idx)
            if (len(data) != 3*self.watermark):
                print("expect {:d} sample from fake calc but got {:d}".format(3*self.watermark, len(data)))
                self.keepGoing
                return
            idx += self.watermark
            now = lastTime + packetWidth
            status = self.watermark
            samplesAvail = self.watermark
            self.callback(now, status, samplesAvail, data)
            lastTime = now
            #print("after callback: {} {}".format(now, len(data)))
            #if idx > 4000:
            #    self.keepGoing = False

    def createFakeSine(self, curIdx):
        data = []
        gain = self.getGain()
        sps = self.getSps()
        for i in range(curIdx, curIdx+self.watermark):
            val = 4096*gain*math.sin(2*math.pi*(i)/self.sinePeriod/sps)
            data.append(val/100) # x
            data.append(val/100) # and y are smaller
            data.append(val)
        return data

    def createFakeConstantUp(self, curIdx):
        # input x,y,z values are x,y,z values of 70 deg counterclockwise (-70 deg)
        # rotation about y axis for vector of [0,0,4096]
        # should end with maxacc ~ 0 g's 
        data = []
        for i in range(curIdx, curIdx+self.watermark):
            # data.append(0)
            data.append(-3848.98097)
            data.append(0)
            # data.append(4096)
            data.append(1400.91451)
        return data

    def createFakeXhalfG(self, curIdx):
        data = []
        for i in range(curIdx, curIdx+self.watermark):
            data.append(0)
            data.append(2048)
            data.append(4096)
        return data

    def createFakeRotate(self, curIdx):
        # 45 deg rotation about y axis
        data = []
        for i in range(curIdx, curIdx+self.watermark):
            data.append(-0.353553*4096)
            data.append(0)
            data.append((0.7071068+0.353553)*4096)
        return data

    def createOtherRotate(self, curIdx):
        # 20 deg rotation about y axis
        # lets try 90 degree rotation
        data = []
        for i in range(curIdx, curIdx+self.watermark):
            degrees = math.radians(20)
            accel = 0.5
            data.append((-math.sin(degrees)*accel)*4096)
            data.append(0)
            data.append(((math.sin(degrees)*accel)+math.cos(degrees))*4096)
        return data
    # def createFakeRotate(self, curIdx):
    #     data = []
    #     for i in range(curIdx, curIdx+self.watermark):
    #         if i//140.0 == 0:
    #             data.append(-0.353553*4096)
    #             data.append(0)
    #             data.append((0.7071068+0.353553)*4096)
    #             print('in 150', curIdx)
    #         elif i//252.0 == 0:
    #             data.append((-0.7071068-0.353553)*4096)
    #             data.append(0)
    #             data.append((0.7071068-0.353553)*4096)
    #             print('in 200',curIdx)
    #         else:
    #             data.append(0)
    #             data.append(0)
    #             data.append(4096)
    #             print('not in either',curIdx)
    #     return data
