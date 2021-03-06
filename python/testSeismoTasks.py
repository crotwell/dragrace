import sys
import struct
import array
import math
from SeismogramTasks import *

x = [1,1,1]
y=x
z=x



print(VectorMagnitude(1,1,1))
print(Magnitude_ThreeC_TimeSeries(x,y,z))

print(Divide_TimeSeries(x,3))
print(Multiply_TimeSeries(x,3))
print(Add_TimeSeries(x,3))
print(Subtract_TimeSeries(x,3))

print(Sum_TimeSeries(x))
print(RemoveMean_TimeSeries(x))

x = [1,0,0]
y = [0,0,0]

print(Coordinate_Rotation_2D(1,0,45.))
print(Rotate_2D_TimeSeries(x,y,45.))

x = [1,1,1]
y = [1,3,1]
o = [0,0,0,0,0]
lo=len(o)

z=Zero_List(1,4)
print(z)
print('----')
v = CoordinateRotation_3D(1,0,0,70.0,0)
print(v)
print(type(v))

testx = [0,0,0,0,0]
testy = [2048,2048,2048,2048,2048]
testz = [4096,4096,4096,4096,4096]
r = Rotate_3D_TimeSeries(testx,testy,testz,theta=0,alpha=0)
x = r[0]
y = r[1]
z = r[2]
z_subG = subtractGravity(z,countToGravity=4096)
vmag = Magnitude_ThreeC_TimeSeries(x,y,z_subG)
peakAccel = max(vmag)/4096
print(peakAccel)
