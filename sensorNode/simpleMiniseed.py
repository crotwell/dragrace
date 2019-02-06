import struct
from datetime import datetime, timedelta

MICRO = 1000000

EMPTY_SEQ = "      ".encode('UTF-8')
ENC_SHORT = 1
ENC_INT = 3

BIG_ENDIAN = 1
LITTLE_ENDIAN = 0

HEADER_SIZE = 48
B1000_SIZE = 8
MAX_INT_PER_512 = (512-HEADER_SIZE-B1000_SIZE)//4
MAX_SHORT_PER_512 = (512-HEADER_SIZE-B1000_SIZE)//2


class MiniseedHeader:
    def __init__(self, network, station, location, channel, starttime, numsamples, samprate, encoding=ENC_INT, byteorder=BIG_ENDIAN):
        self.sequence_number=0; # SEED record sequence number */
        self.network = network     # Network designation, NULL terminated */
        self.station=station    # Station designation, NULL terminated */
        self.location=location     # Location designation, NULL terminated */
        self.channel=channel      # Channel designation, NULL terminated */
        self.dataquality='D'    # Data quality indicator */
        self.starttime=starttime    # Record start time, corrected (first sample) */
        self.samprate=samprate          # Nominal sample rate (Hz) */
        self.numsamples=numsamples        # Number of samples in record */
        self.encoding=encoding    # Data encoding format */
        self.byteorder=byteorder        # Original/Final byte order of record */
        if self.byteorder==1:
            self.endianChar = '>'
        else:
            self.endianChar = '<'

        self.sampPeriod = timedelta(microseconds = MICRO/samprate)  # Nominal sample period (Sec) */

    def codes(self):
        return "{}.{}.{}.{}".format(self.network, self.station, self.location, self.channel)

    def pack(self):
        header = bytearray(48)
        net = self.network.ljust(2).encode('UTF-8')
        sta = self.station.ljust(5).encode('UTF-8')
        loc = self.location.ljust(2).encode('UTF-8')
        chan = self.channel.ljust(3).encode('UTF-8')
        struct.pack_into(self.endianChar+'6scc5s2s3s2s', header, 0,
          EMPTY_SEQ, b'D', b' ', sta, loc, chan, net)
        self.packBTime(header, self.starttime)
        sps=int(self.samprate)
        struct.pack_into(self.endianChar+'HHH', header, 30, self.numsamples, sps, 1);
        return header

    def packBTime(self, header, time):
        tt = time.timetuple()
        struct.pack_into(self.endianChar+'HHBBBxH', header, 20, tt.tm_year, tt.tm_yday, tt.tm_hour, tt.tm_min, tt.tm_sec, int(time.microsecond/100))

class MiniseedRecord:
    def __init__(self, header, data):
        self.header = header
        self.data = data

    def codes(self):
        return self.header.codes()

    def starttime(self):
        return self.header.starttime

    def endtime(self):
        return self.starttime() + self.header.sampPeriod * (self.header.numsamples-1)

    def pack(self):
        record = bytearray(512)
        record[0:48] = self.header.pack()
        record[39] = 1 #  one blockette, b1000

        record[45] = 64 # offset to first data
        record[47] = 48 # offset to first blockette
        self.packB1000(record, 48)
        self.packData(record, 64, self.data)
        return record

    def packB1000(self, recordBytes, offset):
        struct.pack_into(self.header.endianChar+'HHBBBx', recordBytes, offset, 1000, 0, self.header.encoding, self.header.byteorder, 9)

    def packData(self, recordBytes, offset, data):
        if self.header.encoding == ENC_SHORT:
            for d in data:
                struct.pack_into(self.header.endianChar+'h', recordBytes, offset, d)
                #record[offset:offset+4] = d.to_bytes(4, byteorder='big')
                offset+=2
        elif self.header.encoding == ENC_INT:
            for d in data:
                struct.pack_into(self.header.endianChar+'i', recordBytes, offset, d)
                #record[offset:offset+4] = d.to_bytes(4, byteorder='big')
                offset+=4
        else:
            raise Error("Encoding type {} not supported.".format(self.header.encoding))
