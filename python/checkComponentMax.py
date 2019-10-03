import simpleMiniseed
import sys
import dataBuffer
import os

def checkComponentMax(filename, bitShift=False):
    print("recompress {}".format(filename))
    with open(filename, 'rb+') as f:
        while True:
            rawBytes = f.read(512)
            if len(rawBytes) < 512:
                print("Done {:d}".format(len(rawBytes)))
                break
            msr = simpleMiniseed.unpackMiniseedRecord(rawBytes)
            #print("read record: {} {:d} {:d} {:d}".format(msr.codes(), msr.header.recordLength, msr.header.numsamples, msr.header.encoding))
            if not msr.codes() in miniseedBuffers:
                miniseedBuffers[msr.codes()] = \
                    dataBuffer.DataBuffer(msr.header.network,
                        msr.header.station,
                        msr.header.location,
                        msr.header.channel,
                        msr.header.sampleRate,
                        archive=True,
                        encoding=simpleMiniseed.ENC_SHORT)
            if bitShift:
                for i in range(len(msr.data)):
                    msr.data[i] = msr.data[i] >> 2

            miniseedBuffers[msr.codes()].push(msr.starttime(), msr.data)

def checkComponentMaxDir(topDirName, bitShift=False):
    if (os.path.isfile(topDirName)):
        checkComponentMax(topDirName)
    else:
        for dirname, dirnames, filenames in os.walk(topDirName):
            for filename in filenames:
                checkComponentMax(os.path.join(dirname, filename), bitShift=bitShift)

filename = sys.argv[1]
miniseedBuffers = dict()
bitShift = False

checkComponentMaxDir(filename, bitShift)

for key in miniseedBuffers:
    miniseedBuffers[key].close()
