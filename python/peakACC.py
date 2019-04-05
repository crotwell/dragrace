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
# timestamp = simpleDali.utcnowWithTz().isoformat() # time need to be...
# datetime.isoformat()
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

    vmag = Magnitude_ThreeC_TimeSeries_jake(rotate_array_x, y, new_array_z)

    peakAccel = max(vmag)/countToGravity
    maxAcceljson = {
        "station":station,
        "start_time":start_time,
        # "start_time":start in MMA8451 line 254
        "end_time":end_time,
        # "end_time": last_sample_time in MMA8451 line, also as now
        "maxacc":peakAccel
        # add in x,y,z and x',y',z', theta
     }
    return maxAcceljson

def compareSendPeakAccel(establishedJson, freshJson, Dali, maxWindow):
    if freshJson is None:
        #print('freshjson is none')
        pass
    if establishedJson is None:
        #print('established is none')
        return freshJson
    if freshJson["end_time"] - establishedJson["start_time"] < maxWindow:
        #print('in time window')
        establishedJson["end_time"] = freshJson["end_time"]
        if freshJson["maxacc"] > establishedJson["maxacc"]:
            establishedJson["maxacc"] = freshJson["maxacc"]
            # if "freshly calculated" maxAcceljson has larger MAXCC than
            # "already established" json, then establsihed takes on MAXACC of
            # freshjson
        else:
            None
        return establishedJson
    else:
        # need datetime to calc hp times
        hpdatastart = simpleDali.datetimeToHPTime(establishedJson["start_time"])
        hpdataend = simpleDali.datetimeToHPTime(establishedJson["end_time"])
        establishedJson["start_time"] = establishedJson["start_time"].isoformat()
        establishedJson["end_time"] = establishedJson["end_time"].isoformat()
        if Dali is not None:
            # send establishedJson to ring server
            streamid = "{}.{}/MAXACC".format("XX", establishedJson["station"])
            loop = asyncio.get_event_loop()
            sendTask = loop.create_task(Dali.writeJSON(streamid, hpdatastart, hpdataend, establishedJson))
            loop.run_until_complete(sendTask)
            if (sendTask.exception()):
                raise Exception("Unable to send peak acc") from sendTask.exception()
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


if __name__ == "__main__":
    # execute only if run directly as a script, ignore if imported
    # note: each element of x,y,z makes one vector!
    array_x = [1,2,3,4,500,15,25]
    array_y = [5,6,7,8,32,69,70]
    array_z = [9,10,11,12,47,100,0]
    theta = 20.0
    station = 'PI01'
    start_time = simpleDali.utcnowWithTz()
    time_diff = timedelta(seconds=0.20)
    end_time = start_time + time_diff


    # print('---')
    # print(sendPeakAccel(newJson))
    # timedelta should be about 0.25-0.5 s

    freshJson = peakAccelerationCalculation(array_x,array_y,array_z,theta,station,start_time,end_time)
    print(freshJson)
    # establishedJson =
    # need an IP catcher, config listener + thrower, and make a dictionary...
    #  that makes info dictionary for each heat (time, max accel, )
    # Theta is found from config listener + thrower from ring server
