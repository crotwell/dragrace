import struct

EMPTY_SEQ = "      ".encode('UTF-8')
ENC_INT = 3

def createMiniseedRecord(msHeader, data):
    record = bytearray(512)
    record[0:48] = msHeader
    struct.pack_into('', record, 48)
    record[39] = 1 #  one blockette, b1000
    record[44] = 64 # offset to first data
    record[46] = 48 # offset to first blockette
    packB1000(record, 48, ENC_INT)
    packData(record, 64, data)
    return record

def createMiniseedHeader(net, sta, loc, chan, start, nsamp, sps):
    header = bytearray(48)
    if isinstance(net, str):
        net = net.encode('UTF-8')
    if isinstance(sta, str):
        sta = sta.encode('UTF-8')
    if isinstance(loc, str):
        loc = loc.encode('UTF-8')
    if isinstance(chan, str):
        chan = chan.encode('UTF-8')
    struct.pack_into('6scc5s2s3s2s', header, 0,
      EMPTY_SEQ, b'D', b' ', sta, loc, chan, net)
    packBTime(header, start)
    struct.pack_into('HHH', header, 30, nsamp, sps, 1);
    return header

def packBTime(header, time):
    tt = time.timetuple()
    struct.pack_into('HHBBBxH', header, 20, tt.tm_year, tt.tm_yday, tt.tm_hour, tt.tm_min, tt.tm_sec, int(time.microsecond/100))

def packB1000(header, offset, encode):
    struct.pack_into('HHBBBx', header, offset, 1000, 0, encode, 0, 9)

def packData(record, offset, data):
    for d in data:
        record[offset:offset+4] = d.to_bytes(4, byteorder='little')
        offset+=4
