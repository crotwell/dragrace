# -*- coding: utf-8 -*-
"""
Created on Sun Mar  3 20:27:44 2019

@author: Jake
"""

# Making peak acceleration stuff
import sys
import struct
import array
import math
from SeismogramTasks import *

# note: each element of x,y,z makes one vector!
array_x = [1,2,3,4,500,15,25]
array_y = [5,6,7,8,32,69,70]
array_z = [9,10,11,12,47,100,0]

# overall : take in raw packets (arrays Z,N,E), do rotation and rest state
# correction, calculate peak counts over the entire time series, divide
#  time series by factor to convert into g's (4069 = 1g?), returns the g's
# magnitude over a small amount of time (depends on len of arrays given),
# and sends this mag to ring server


# First, do coordiate rotation about the y-axis (downtrack). Note the...
#  Rotate_2D_TimeSeries function has rotation about z, but can put...
#  z in for y in code
# input: array_x, array_z, theta
# output: rotate_array_x, rotate_array_z
theta = 20.0
rotate_array_x = Rotate_2D_TimeSeries(array_x,array_z,theta)[0]
rotate_array_z = Rotate_2D_TimeSeries(array_x,array_z,theta)[1]
# print(rotate_array_x)
# print(rotate_array_z)


# function to convert input array_z into a array_z minus a rest state factor
# input : rotate_array_z
# output : new_array_z
rest_factor_z = -1
def rest_state_correction(rotate_array_z):
    correct = []
    for i in rotate_array_z:
        correct.append(i+rest_factor_z)
    return correct
new_array_z = rest_state_correction(rotate_array_z)
print(rotate_array_x)
print(array_y)
print(new_array_z)
print('---')

# now use: rotate_array_x, array_y, new_array_z

# vmag = Magnitude_ThreeC_TimeSeries(rotate_array_x,array_y,new_array_z)
# print('vmag: {}'.format(vmag))
#
# test_1 = math.sqrt((rotate_array_x[0]**2 + array_y[0]**2 + new_array_z[0]**2))
# test_2 = VectorMagnitude(rotate_array_x[1],array_y[1],new_array_z[3])
# test_3 = VectorMagnitude(rotate_array_x[2],array_y[2],new_array_z[2])
# test_4 = VectorMagnitude(rotate_array_x[3],array_y[3],new_array_z[3])
# print(test_1,test_2,test_3,test_4)

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
    # i=0
    # vmag=0
    # while i < nptsx:
    #     vmag[i]=VectorMagnitude(x[i],y[i],z[i])
    #     i=i+1
    # return vmag
    i = 0
    vmag = []
    while i < nptsx:
        vmag.append(VectorMagnitude(x[i],y[i],z[i]))
        i += 1
    return vmag
vmag = Magnitude_ThreeC_TimeSeries_jake(rotate_array_x,array_y,new_array_z)
# print('vmag: {}'.format(vmag))

# Divide vmag list by 4096 to convert counts to g's
def countsTog(vmag):
    npts = len(vmag)
    peakAccel = []
    i = 0
    countsIng = 4096
    while i < npts:
        peakAccel.append(vmag[i]/countsIng)
        i += 1
    return peakAccel
peakAccel = countsTog(vmag)
print('peak_Accel: {}'.format(peakAccel))

# now have a peakAccel list for as many times as we want 



# max = 0
# # timestamp = #
# #(see picture)

# next: Magnitude_ThreeC_TimeSeries --> vmag in counts, then divide this
#  vmag from counts into g's (by some factor)

# need: what is rest state? (calculate mean of before and after filter) (have a
# 'z-corrected factor', and rn it is 1)
# look at MMA file... look at line 249
