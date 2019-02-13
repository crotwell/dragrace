from datetime import timedelta, datetime
import os
import simpleMiniseed
MICRO = 1000000

class DataBuffer:
    def __init__(self, network, station, location, channel, samprate,
                 encoding=simpleMiniseed.ENC_INT,
                 byteorder=simpleMiniseed.BIG_ENDIAN,
                 dali=None,
                 archive=False,
                 continuityFactor=5):
        self.network = network
        self.station = station
        self.location = location
        self.channel = channel
        self.samprate = samprate
        self.sampPeriod = timedelta(microseconds = MICRO/samprate)
        self.encoding = encoding
        self.byteorder = byteorder
        self.continuityFactor = continuityFactor
        self.dali = dali
        self.archive = archive
        self.dataArray = None
        self.starttime = None
        self.numpts = 0
        self.msFile = None
        self.msFilename = None


    def push(self, starttime, dataArray):
        if starttime is None:
            raise Error("Starttime cannot be None")
        if dataArray is None:
            raise Error("dataArray cannot be None")
        if not (self.continuous(starttime) and self.canFit(dataArray)):
            self.flush()
            self.starttime = starttime
            self.dataArray = dataArray
            self.numpts = len(dataArray)
        else:
            self.dataArray.extend(dataArray)
            self.numpts += len(dataArray)

    def flush(self):
        if self.dataArray is None:
            return
        msr = self._bufferToMiniseed()
        if self.dali:
            self.miniseedToDali(msr)
        elif self.archive:
            self.miniseedToRingserverFile(msr)
        else:
            self.miniseedToPlainFile(msr)
        self.numpts = 0
        self.starttime = None
        self.dataArray = None

    def close(self):
        self.flush()
        if self.msFile:
            self.msFile.close()
            self.msFile = None
            self.msFilename = None

    def miniseedToRingserverFile(self, msr):
        filename = "{net}/{sta}/{year}/{yday}/{net}.{sta}.{loc}.{chan}.{year}.{yday}.{hour}".format(net=self.network,
                                            sta=self.station,
                                            loc=self.location,
                                            chan=self.channel,
                                            year=self.starttime.strftime("%Y"),
                                            yday=self.starttime.strftime("%j"),
                                            hour=self.starttime.strftime("%H"))
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        self.miniseedToFile(msr, filename)

    def miniseedToPlainFile(self, msr):
        filename = "{net}.{sta}.{loc}.{chan}.{year}.{yday}.{hour}".format(net=self.network,
                                            sta=self.station,
                                            loc=self.location,
                                            chan=self.channel,
                                            year=self.starttime.strftime("%Y"),
                                            yday=self.starttime.strftime("%j"),
                                            hour=self.starttime.strftime("%H"))
        self.miniseedToFile(msr, filename)

    def miniseedToFile(self, msr, filename):
        if self.msFile == None or self.msFilename is not filename:
            if self.msFile:
                self.msFile.close()
            self.msFile = open(filename, "ab")
            self.msFilename = filename
        self.msFile.write(msr.pack())
        self.msFile.flush()

    def miniseedToDali(self, msr):
        self.dali.writeMSeed(msr)


    def _bufferToMiniseed(self):
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
        return msr

    def continuous(self, nextstarttime):
        if self.dataArray is None:
            # we are empty, very first chunk of data
            return False
        predictedNextStart = self.starttime + self.numpts*self.sampPeriod
        if abs(predictedNextStart - nextstarttime) < self.continuityFactor*self.sampPeriod:
            return True
        print("Not Cont: {} {} < {}".format(predictedNextStart, nextstarttime, self.continuityFactor*self.sampPeriod ))
        return False

    def canFit(self, nextdataArray):
        if self.dataArray is None:
            return True
        maxPerRecord=0
        if (self.encoding==simpleMiniseed.ENC_INT):
            maxPerRecord = simpleMiniseed.MAX_INT_PER_512
        elif (self.encoding==simpleMiniseed.ENC_SHORT):
            maxPerRecord = simpleMiniseed.MAX_SHORT_PER_512
        #print("{:d}+{:d} < {:d}".format(len(self.dataArray),len(nextdataArray), maxPerRecord))
        return len(self.dataArray)+len(nextdataArray) < maxPerRecord
