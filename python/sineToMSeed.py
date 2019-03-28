
import simpleMiniseed
import simpleDali
import dataBuffer

import math
import time
import struct
import queue
import threading
from datetime import datetime, timedelta
import sys, os
from pathlib import Path


sps=200
sineFreq=2
numSeconds=30

samplesAvail = 30
sineArg=0
sineStep = 2*math.pi/sineFreq/sps
gain=1000

numPackets=numSeconds*sps/samplesAvail

sta = "SINE".upper()
net = "XX"
loc = "00"
chanList = [ "HNZ" ]

miniseedBuffers = dict()
for chan in chanList:
    miniseedBuffers[chan] = dataBuffer.DataBuffer(net, sta, loc, chan,
             sps, encoding=simpleMiniseed.ENC_SHORT)

nextStart = simpleDali.utcnowWithTz()
for i in range(int(numPackets)):
    packetDeltaTime=timedelta(seconds=1.0*(samplesAvail-1)/sps)
    start = nextStart - packetDeltaTime
    chan=chanList[0]
    chanData = []
    for i in range(samplesAvail):
        chanData.append( int(gain*math.sin(sineArg)) )
        sineArg+=sineStep
    miniseedBuffers[chan].push(start, chanData)
    nextStart = nextStart+timedelta(seconds=1.0*(samplesAvail)/sps)


for chan in chanList:
    miniseedBuffers[chan].flush()
