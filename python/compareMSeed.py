import simpleMiniseed
import sys
import array

filename = 'XX.SINE.00.HNZ.2019.043.20'
outfilename = 'test.mseed'

bitShift = False

def readThenWrite():
    with open(filename, 'rb+') as f:
        with open(outfilename, 'wb') as out:
            while True:
                rawBytes = f.read(512)
                if len(rawBytes) < 512:
                    print("Done {:d}".format(len(rawBytes)))
                    break
                msr = simpleMiniseed.unpackMiniseedRecord(rawBytes)
                print("read record: {} {:d} {:d} {:d}".format(msr.codes(), msr.header.recordLength, msr.header.numsamples, msr.header.encoding))
                out.write(msr.pack())

def fileCompare(filenameA, filenameB):
    with open(filenameA, 'rb+') as inA:
        with open(filenameB, 'rb+') as inB:
            msrA = readOneRecord(inA)
            msrB = readOneRecord(inB)
            compareHeader(msrA, msrB)
            dataA = array.array(msrA.data.typecode)
            dataB = array.array(msrB.data.typecode)
            msr = msrA
            while msr is not None:
                dataA.extend(msr.data)
                msr = readOneRecord(inA)

            msr = msrB
            while msr is not None:
                dataB.extend(msr.data)
                msr = readOneRecord(inB)

            if len(dataA) != len(dataB):
                print("data arrays are not same length: {:d} {:d}".format(len(dataA), len(dataB)))
                return
            if bitShift:
                for i in range(len(dataA)):
                    if (dataA[i] >>2 != dataB[i]):
                        print("bit shift data at index {:d} not equal, {:d} -> {:d} != {:d}".format(i, dataA[i], dataA[i] >>2, dataB[i]))
                        return
            else:
                for i in range(len(dataA)):
                    if (dataA[i] != dataB[i]):
                        print("data at index {:d} not equal, {:d} != {:d}".format(i, dataA[i], dataB[i]))
                        return

def readOneRecord(f):
    rawBytes = f.read(512)
    if len(rawBytes) < 512:
        if len(rawBytes) == 0:
            # assume done, return None
            return None
        else:
            raise Exception("Not enough bytes {:d}<512".format(len(rawBytes)))
    msr = simpleMiniseed.unpackMiniseedRecord(rawBytes)
    return msr

def compareHeader(msrA, msrB):
    hA = msrA.header
    hB = msrB.header
    varsA = vars(hA)
    varsB = vars(hB)
    for field,valA in varsA.items():
        valB = varsB[field]
        if valA != valB:
            print("Header {} differs: A: {} B: {}".format(field, valA, valB))


fileCompare(sys.argv[1], sys.argv[2])
