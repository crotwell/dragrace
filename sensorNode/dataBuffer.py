from datetime import timedelta, datetime
import simpleMiniseed
MICRO = 1000000

class DataBuffer:
    def __init__(self, network, station, location, channel, samprate, encoding=simpleMiniseed.ENC_INT, byteorder=simpleMiniseed.BIG_ENDIAN):
        self.network = network
        self.station = station
        self.location = location
        self.channel = channel
        self.samprate = samprate
        self.sampPeriod = timedelta(microseconds = MICRO/samprate)
        self.encoding = encoding
        self.byteorder = byteorder
        self.dataArray = None
        self.starttime = None
        self.numpts = 0

    def push(self, starttime, dataArray):
        if not (self.continuous(starttime) and self.canFit(dataArray)):
            self.flush()
            self.starttime = starttime
            self.dataArray = dataArray
        else:
            self.dataArray.extend(dataArray)
        self.numpts += len(dataArray)

    def flush(self):
        if self.dataArray is None:
            return
        filename = "{}.{}.{}.{}.{}".format(self.network,
                                            self.station,
                                            self.location,
                                            self.channel,
                                            self.starttime.strftime("%Y.%j.%H"))
        msh = simpleMiniseed.MiniseedHeader(self.network,
                                            self.station,
                                            self.location,
                                            self.channel,
                                            self.starttime,
                                            self.numpts,
                                            self.samprate,
                                            encoding=self.encoding,
                                            byteorder=self.byteorder)
        msr = simpleMiniseed.MiniseedRecord(msh, self.dataArray)
        msFile = open(filename, "ab")
        msFile.write(msr.pack())
        msFile.close()
        self.dataArray = None
        self.starttime = None
        self.numpts = 0

    def continuous(self, nextstarttime):
        if self.dataArray is None:
            # we are empty, very first chunk of data
            return False
        predictedNextStart = self.starttime + self.numpts*self.sampPeriod
        if abs(predictedNextStart - nextstarttime) < self.sampPeriod:
            return True
        return False

    def canFit(self, nextdataArray):
        if self.dataArray is None:
            return True
        maxPerRecord=0
        if (self.encoding==simpleMiniseed.ENC_INT):
            maxPerRecord = simpleMiniseed.MAX_INT_PER_512
        elif (self.encoding==simpleMiniseed.ENC_SHORT):
            maxPerRecord = simpleMiniseed.MAX_SHORT_PER_512
        return len(self.dataArray)+len(nextdataArray) < maxPerRecord
