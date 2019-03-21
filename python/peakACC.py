# Making peak acceleration stuff
import sys
import struct
import array
import math
from SeismogramTasks import Rotate_2D_TimeSeries,VectorMagnitude
import datetime
timestamp = datetime.datetime.utcnow().isoformat() # time need to be...
# datetime.isoformat()

# note: each element of x,y,z makes one vector!
array_x = [1,2,3,4,500,15,25]
array_y = [5,6,7,8,32,69,70]
array_z = [9,10,11,12,47,100,0]
theta = 20.0
station = 'PI01'

# overall : take in raw packets (arrays Z,N,E), do rotation and rest state
# correction, calculate peak counts over the entire time series, divide
#  time series by factor to convert into g's (4069 = 1g?), returns the g's
# magnitude over a small amount of time (depends on len of arrays given),
# and sends this mag to ring server

def peakAccelerationCalculation(x,y,z,theta,station,time):
    # rotation correction
    # First, do coordiate rotation about the y-axis (downtrack). Note the...
    #  Rotate_2D_TimeSeries function has rotation about z, but can put...
    #  z in for y in code
    # input: array_x, array_z, theta
    # output: rotate_array_x, rotate_array_z
    rotate_array_x = Rotate_2D_TimeSeries(array_x, array_z, theta)[0]
    rotate_array_z = Rotate_2D_TimeSeries(array_x, array_z, theta)[1]

    rest_factor_z = -1
    new_array_z = rest_state_correction(rotate_array_z, rest_factor_z)

    vmag = Magnitude_ThreeC_TimeSeries_jake(rotate_array_x,array_y,new_array_z)

    peakAccel = countsTog(vmag)
    maxAcceljson = {
        "station":station,
        "time":time,
        "MAXACC":max(peakAccel)
     }
    return maxAcceljson

def 
    # time = datetime.datetime.utcnow()
    # time_2 = datetime.datetime.utcnow()
    # time_3 = time - time_2
    # return time_3
    # NOTE: can do:  if now - prevTime == 0.25 update maxAcceljson dictionary


    # need to make station and time configuerable/changeable within function
    # need to then send this dictionary every 0.25-0.5 sec
    # make new maxAcceljson every 0.25 secs
    # def sendPeakAccel():
    #     now = datetime.datetime.utcnow()
    #     prevAcc = maxAcceljson["MAXACC"]
    #     prevTime = maxAcceljson["time"]
    #     # if now - datetime.datetime.timedelta(seconds=0.25):




    # Create dictionary that return
    # peakAcceljson = {"station":s, "time": starttime, "maxacc": max(peakAccel)}


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
def rest_state_correction(rotate_array_z, rest_factor_z):
    correct = []
    for i in rotate_array_z:
        correct.append(i+rest_factor_z)
    return correct

print(peakAccelerationCalculation(array_x,array_y,array_z,theta,station,timestamp))


# timedelta should be about 0.25-0.5 s
# need an IP catcher, config listener + thrower, and make a dictionary...
#  that makes info dictionary for each heat (time, max accel, )
# Theta is found from config listener + thrower from ring server
