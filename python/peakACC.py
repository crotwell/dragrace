# Calculate Peak Acceleration
# Making peak acceleration stuff
import asyncio
import sys
import struct
import array
import math
from SeismogramTasks import Rotate_2D_TimeSeries,VectorMagnitude,Rotate_3D_TimeSeries
from datetime import datetime, timedelta
import json

# note: each element of x,y,z makes one vector!
array_x = [1,2,3,4,500,15,25]
array_y = [5,6,7,8,32,69,70]
array_z = [9,10,11,12,47,100,0]
# theta = 20.0
# station = 'PI01'
# start_time = simpleDali.utcnowWithTz()
# time_diff = timedelta(seconds=0.20)
# end_time = start_time + time_diff
import simpleDali
# timestamp = simpleDali.utcnowWithTz().strftime("%Y-%m-%dT%H:%M%SZ") # time need to be...
# datetime.strftime("%Y-%m-%dT%H:%M%SZ")
# note this time is associated with last element of x,y,z data we get
# would like to compare first and last of two packets..?

# overall : take in raw packets (arrays Z,N,E), do rotation and rest state
# correction, calculate peak counts over the entire time series, divide
#  time series by factor to convert into g's (4069 = 1g?), returns the g's
# magnitude over a small amount of time (depends on len of arrays given),
# and sends this mag to ring server

def peakAccelerationCalculation(x,y,z,theta,alpha,station,start_time,end_time):
    # rotation correction
    # First, do coordiate rotation about the y-axis (downtrack). Note the...
    #  Rotate_2D_TimeSeries function has rotation about z, but can put...
    #  z in for y in code
    # input: array_x, array_z, theta
    # output: rotate_array_x, rotate_array_z
    r = Rotate_3D_TimeSeries(x,y,z,theta,alpha)
    rotate_array_x = r[0]
    rotate_array_y = r[1]
    rotate_array_z = r[2]

    countToGravity = 4096 # may need to be -4096, counts not g
    new_array_z = subtractGravity(rotate_array_z, countToGravity)

    vmag = Magnitude_ThreeC_TimeSeries_jake(rotate_array_x, rotate_array_y, new_array_z)

    maxVmag = max(vmag)
    #print(f"maxVmag is {maxVmag}")
    maxIndex = vmag.index(maxVmag) #index function searches elements to return position, returns the smallest position first
    vmagPair = (maxIndex,maxVmag) #create tuple of index and vmag value


    maxacc = max(vmag)/countToGravity
    #print(f"maxVmag is {maxVmag}")
    #print(f"maxacc is {maxacc}")
    maxAcceljson = {
        "station":station,
        "start_time":start_time,
        # "start_time":start in MMA8451 line 254
        "end_time":end_time,
        # "end_time": last_sample_time in MMA8451 line, also as now
        "maxacc":maxacc,
        # add in x,y,z and x',y',z', theta
        "maxVmag":maxVmag,
        "maxIndex":maxIndex,
        "vmagPair":vmagPair
        # return the index of peak Acceleration
    }
    a = maxAcceljson['maxVmag']
    print(f"maxVmag is {a}")
    return maxAcceljson

def compareSendPeakAccel(establishedJson, freshJson, Dali, maxWindow):
    if freshJson is None:
        return None
    if establishedJson is None:
        return freshJson
    if freshJson["end_time"] - establishedJson["start_time"] < maxWindow:
        #print('in time window {} - {} = {}  {}'.format(freshJson["end_time"], establishedJson["start_time"], freshJson["end_time"] - establishedJson["start_time"], maxWindow))
        establishedJson["end_time"] = freshJson["end_time"]
        if freshJson["maxacc"] > establishedJson["maxacc"]:
            establishedJson["maxacc"] = freshJson["maxacc"]
            # if "freshly calculated" maxAcceljson has larger MAXCC than
            # "already established" json, then establsihed takes on MAXACC of
            # freshjson
        return establishedJson
    else:
        # helps with time alignment
        if freshJson['start_time'] < establishedJson["start_time"] + maxWindow:
            if freshJson["maxacc"] > establishedJson["maxacc"]:
                establishedJson["maxacc"] = freshJson["maxacc"]
            establishedJson['end_time'] = establishedJson["start_time"] + maxWindow
            freshJson['start_time'] = establishedJson['end_time']

        # need datetime to calc hp times
        hpdatastart = simpleDali.datetimeToHPTime(establishedJson["start_time"])
        hpdataend = simpleDali.datetimeToHPTime(establishedJson["end_time"])
        establishedJson["start_time"] = establishedJson["start_time"].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+'Z'
        establishedJson["end_time"] = establishedJson["end_time"].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+'Z'
        if Dali is not None:
            # send establishedJson to ring server
            streamid = "{}.{}/MAXACC".format("XX", establishedJson["station"])
            loop = asyncio.get_event_loop()
            sendTask = loop.create_task(Dali.writeJSON(streamid, hpdatastart, hpdataend, establishedJson))
            loop.run_until_complete(sendTask)
            if (sendTask.exception()):
                raise Exception("Unable to send peak acc") from sendTask.exception()
            result = sendTask.result()
            if result.type == 'ERROR':
                raise Exception("Unable to send peak acc: {}".format(result))
            #print('sending to ringserver')
        else:
            print(json.dumps(establishedJson,indent = 4))
        return freshJson
        # if time between samples is >= 0.25s, then make establishedJson take
        # on values of freshJson, so freshJson will can be compared to

    # time = simpleDali.utcnowWithTz()
    # time_2 = simpleDali.utcnowWithTz()
    # time_3 = time - time_2
    # return time_3
    # NOTE: can do:  if now - prevTime == 0.25 update maxAcceljson dictionary


    # need to make station and time configuerable/changeable within function
    # need to then send this dictionary every 0.25-0.5 sec
    # make new maxAcceljson every 0.25 secs
    # def sendPeakAccel():
    #     now = simpleDali.utcnowWithTz()
    #     prevAcc = maxAcceljson["maxacc"]
    #     prevTime = maxAcceljson["time"]
    #     # if now - datetime.datetime.timedelta(seconds=0.25):

# magnitude time series
# function to take magnitude of rotated and rest state corrected time ...
# series
# input = rotate_array_x,array_y,new_array_z
# output = vmag
def Magnitude_ThreeC_TimeSeries_jake(x,y,z):
    nptsx=len(x)
    nptsy=len(y)
    nptsz=len(z)
    if nptsx != nptsy:
        print("x and y of different lengths",nptsx,nptsy)
        return
    elif nptsx != nptsz:
        print("z different length than x and y",nptsx,nptsz)
        return
    i = 0
    vmag = []
    while i < nptsx:
        vmag.append(VectorMagnitude(x[i],y[i],z[i]))
        i += 1
    return vmag

# Divide vmag list by 4096 to convert counts to g's
# input = vmag
# output = peakAccel
def countsTog(vmag):
    npts = len(vmag)
    peakAccel = []
    i = 0
    countsIng = 4096
    while i < npts:
        peakAccel.append(vmag[i]/countsIng)
        i += 1
    return peakAccel

# rest state correction
# function to correct rotate_array_z for the rest state correction of -1
# input = rotate_array_z
# output = new_array_z
def subtractGravity(rotate_array_z, countToGravity):
    correct = []
    for i in rotate_array_z:
        correct.append(i-countToGravity) # substracting gravity
    return correct

def jsonToString(maxJson):
    s = maxJson["start_time"]
    e = maxJson["end_time"]
    maxJson["start_time"] = maxJson["start_time"].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+'Z'
    maxJson["end_time"] = maxJson["end_time"].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+'Z'
    out = json.dumps(maxJson,indent = 4)
    maxJson["start_time"] = s
    maxJson["end_time"] = e
    return out

if __name__ == "__main__":
    # execute only if run directly as a script, ignore if imported
    # note: each element of x,y,z makes one vector!
    array_x = [1,2,3,4,500,15,25]
    array_y = [5,6,7,8,32,69,70]
    array_z = [9,10,11,12,47,100,0]
    theta = 20.0
    alpha = 0
    station = 'PI01'
    start_time = simpleDali.utcnowWithTz().replace(hour=0, minute=0, second=0, microsecond=0)
    time_diff = timedelta(seconds=0.10)
    end_time = start_time + time_diff

    maxWindow = timedelta(seconds=0.25)

    # print('---')
    # print(sendPeakAccel(newJson))
    # timedelta should be about 0.25-0.5 s

    establishedJson = peakAccelerationCalculation(array_x,array_y,array_z,theta, alpha,station,start_time,end_time)
    print("first: "+jsonToString(establishedJson))
    start_time = start_time + timedelta(seconds=0.10)
    end_time = start_time + time_diff
    freshJson = peakAccelerationCalculation(array_x,array_y,array_z,theta, alpha,station,start_time,end_time)
    establishedJson = compareSendPeakAccel(establishedJson, freshJson, None, maxWindow)
    print("second: "+jsonToString(establishedJson))

    start_time = start_time + timedelta(seconds=0.10)
    end_time = start_time + time_diff
    freshJson = peakAccelerationCalculation(array_x,array_y,array_z,theta, alpha,station,start_time,end_time)
    establishedJson = compareSendPeakAccel(establishedJson, freshJson, None, maxWindow)
    print("third: "+jsonToString(establishedJson))

    start_time = start_time + timedelta(seconds=0.10)
    end_time = start_time + time_diff
    freshJson = peakAccelerationCalculation(array_x,array_y,array_z,theta, alpha,station,start_time,end_time)
    establishedJson = compareSendPeakAccel(establishedJson, freshJson, None, maxWindow)
    print("forth: "+jsonToString(establishedJson))

    start_time = start_time + timedelta(seconds=0.10)
    end_time = start_time + time_diff
    freshJson = peakAccelerationCalculation(array_x,array_y,array_z,theta, alpha,station,start_time,end_time)
    establishedJson = compareSendPeakAccel(establishedJson, freshJson, None, maxWindow)

    print("last: "+jsonToString(establishedJson))
    #print(freshJson)
    # establishedJson =
    # need an IP catcher, config listener + thrower, and make a dictionary...
    #  that makes info dictionary for each heat (time, max accel, )
    # Theta is found from config listener + thrower from ring server
