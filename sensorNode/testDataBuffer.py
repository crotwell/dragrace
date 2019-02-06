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
    starttime = datetime.utcnow()
    numsamples = 100
    samprate=200
    sampPeriod = timedelta(microseconds = MICRO/samprate)
    shortData = array("h") # shorts
    for i in range(numsamples):
        shortData.append(i)
    databuffer = DataBuffer(network, station, location, channel,
             samprate, encoding=simpleMiniseed.ENC_INT)
    for i in range(10):
        databuffer.push(starttime, shortData)
        starttime = starttime+numsamples*sampPeriod
    databuffer.flush()

doTest()
