from dataBuffer import DataBuffer
from datetime import timedelta, datetime
from array import array
import simpleMiniseed

MICRO=1000000

def doTest():
    network = "YY"
    station = "TEST"
    location = "00"
    channel = "HNZ"
    starttime = simpleDali.utcnowWithTz()
    numsamples = 40
    sampleRate=200
    sampPeriod = timedelta(microseconds = MICRO/sampleRate)

    databuffer = DataBuffer(network, station, location, channel,
             sampleRate, encoding=simpleMiniseed.ENC_SHORT)
    for i in range(10):
        shortData = array("h") # shorts
        for i in range(numsamples):
            shortData.append(i)
        databuffer.push(starttime, shortData)
        starttime = starttime+numsamples*sampPeriod
        print("next isCont: {} canFit: {}".format(databuffer.continuous(starttime), databuffer.canFit(shortData)))
    databuffer.flush()

doTest()
