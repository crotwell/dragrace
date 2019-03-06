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
array_x = [1,2,3,4]
array_y = [5,6,7,8]
array_z = [9,10,11,12]

# overall : take in raw packets (arrays Z,N,E), do rotation and rest state
# correction, calculate peak counts over the entire time series, divide
#  time series by factor to convert into g's (4069 = 1g?), returns the g's
# magnitude over a small amount of time (depends on len of arrays given),
# and sends this mag to ring server


# First, do coordiate rotation about the y-axis (downtrack)


# function to convert input array_z into a array_z minus a rest state factor
rest_factor_z = -1
def rest_state_correction(array_z):
    correct = []
    for i in array_z:
        correct.append(i+rest_factor_z)
    return correct
new_array_z = rest_state_correction(array_z)
# print(new_array_z)


# need: what is rest state? (calculate mean of before and after filter) (have a
# 'z-corrected factor', and rn it is 1)
# look at MMA file... look at line 249
