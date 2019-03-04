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
array_x = [1,2,3,0]
array_y = [4,5,6,0]
array_z = [7,8,9,0]

# we are in counts, not g's. but can correct with divide time series to get
# g's not counts.

#def rest_state_correction(Z,N,E):   # correct each array for [Z,N,E] = [1,0,0]
#    new_array = [E,N,Z-1]     # converts from [Z,N,E] to [x,y,z]
#    return new_array

# funct to convert input array of [Z,N,E] = [1,0,0] at rest state, into
# [x,y,z] = [E,N,Z-1]
def rest_state_correction(uncorrected_array):
    Z = uncorrected_array[0]
    N = uncorrected_array[1]
    E = uncorrected_array[2]
    correct = [E,N,Z-1]

    return correct

new_array1 = rest_state_correction(array1)
new_array2 = rest_state_correction(array2)
new_array3 = rest_state_correction(array3)

print('Corrected Array 1: {}'.format(new_array1))
print('Corrected Array 2: {}'.format(new_array2))
print('Corrected Array 3: {}'.format(new_array3))


# Calculate vector magnitudes of each new array
vmags = Magnitude_ThreeC_TimeSeries(new_array1,new_array2,new_array3)
print('vmags: {}'.format(vmags))
vmag1 = vmags[0]
vmag2 = vmags[1]
vmag3 = vmags[2]
print('vmag1: {}'.format(vmag1))
print('vmag2: {}'.format(vmag2))
print('vmag3: {}'.format(vmag3))

# overall : take in raw packets (arrays Z,N,E), do rotation and rest state
# correction, calculate peak counts over the entire time series, divide
#  time series by factor to convert into g's, returns the g's magnitude over a
# small amount of time (depends on len of arrays given), and sends this mag to
# ring server

# need: what is rest state? (calculate mean of before and after filter) (have a
# 'z-corrected factor', and rn it is 1)
# look at MMA file... look at line 249
