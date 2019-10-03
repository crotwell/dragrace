import simpleMiniseed
import sys
import dataBuffer
import os

def checkComponentMax(filename, bitShift=False):
    print("checkComponent Max {}".format(filename))
    with open(filename, 'rb+') as f:
        while True:
            try:
                rawBytes = f.read(512)
                if len(rawBytes) < 512:
                    #print("Done {:d}".format(len(rawBytes)))
                    break
                msr = simpleMiniseed.unpackMiniseedRecord(rawBytes)
                #print("read record: {} {:d} {:d} {:d}".format(msr.codes(), msr.header.recordLength, msr.header.numsamples, msr.header.encoding))
                for i in range(len(msr.data)):
                   if msr.data[i] > 8000 or msr.data[i] < -8000:
                      print("Almost 2g for {} at index {}, {:d}".format(msr.codes(), i, msr.data[i]))
            except:
                print("Bad record in file {}".format(filename))
                break

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
