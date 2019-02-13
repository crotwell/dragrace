import simpleMiniseed
import sys
import dataBuffer
import os

def recompress(filename, bitShift=False):
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
                        msr.header.samprate,
                        archive=True,
                        encoding=simpleMiniseed.ENC_SHORT)
            if bitShift:
                for i in range(len(msr.data)):
                    msr.data[i] = msr.data[i] >> 2

            miniseedBuffers[msr.codes()].push(msr.starttime(), msr.data)

def recompressDir(topDirName, bitShift=False):
    if (os.path.isfile(topDirName)):
        recompress(topDirName)
    else:
        for dirname, dirnames, filenames in os.walk(topDirName):
            for filename in filenames:
                recompress(os.path.join(dirname, filename), bitShift=bitShift)
            for subdirname in dirnames:
                recompressDir(os.path.join(dirname, subdirname), bitShift=bitShift)

filename = sys.argv[1]
miniseedBuffers = dict()
bitShift = False

recompressDir(filename, bitShift)

for key in miniseedBuffers:
    miniseedBuffers[key].flush()
