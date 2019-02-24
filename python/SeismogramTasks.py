import sys
import struct
import array
import math

def VectorMagnitude(x,y,z):
    return math.sqrt(x*x+y*y+z*z)

def Magnitude_ThreeC_TimeSeries(x,y,z):
    nptsx=len(x)
    nptsy=len(y)
    nptsz=len(z)
    if nptsx != nptsy:
        print("x and y of different lengths",nptsx,nptsy)
        return
    elif nptsx != nptsz:
        print("z different length than x and y",nptsx,nptsz)
        return
    i=0
    vmag=x
    while i < nptsx:
        vmag[i]=VectorMagnitude(x[i],y[i],z[i])
        i=i+1
    return vmag

def Divide_TimeSeries(x,factor):
    npts=len(x)
    i=0
    xf=x
    while i < npts:
        xf[i]=x[i]/factor
        i=i+1
    return xf

def Multiply_TimeSeries(x,factor):
    npts=len(x)
    i=0
    xf=x
    while i < npts:
        xf[i]=x[i]*factor
        i=i+1
    return xf

def Add_TimeSeries(x,factor):
    npts=len(x)
    i=0
    xf=x
    while i < npts:
        xf[i]=x[i]+factor
        i=i+1
    return xf

def Subtract_TimeSeries(x,factor):
    npts=len(x)
    i=0
    xf=x
    while i < npts:
        xf[i]=x[i]-factor
        i=i+1
    return xf

def Sum_TimeSeries(x):
    npts=len(x)
    i=0
    sum=0
    while i < npts:
        sum=sum+x[i]
        i=i+1
    return sum

def RemoveMean_TimeSeries(x):
    npts=len(x)
    mean=Sum_TimeSeries(x)/npts
    xf=Subtract_TimeSeries(x,mean)
    return xf

def Coordinate_Rotation_2D(x,y,theta):
#
# Coordinate Rotation about the Z-axes
# x and y are values in the original coordinate system
# theta is the rotation angle in degrees about the Z-axis
# Looking clockwise in the positive direction of the Z-axis
#
    rad_theta=math.radians(theta)
    xprime=math.cos(rad_theta)*x + math.sin(rad_theta)*y
    yprime=-math.sin(rad_theta)*x + math.cos(rad_theta)*y
    return [xprime, yprime]

def Rotate_2D_TimeSeries(x,y,theta):
    nptsx=len(x)
    nptsy=len(y)
    if nptsx != nptsy:
        print("Mismatch npts",nptsx,nptsy)
        return
    xprime=x
    yprime=y
    i=0
    while i < nptsx:
        [xprime[i], yprime[i]]=Coordinate_Rotation_2D(x[i],y[i],theta)
        i=i+1
    return [xprime, yprime]

def Zero_List(x,m,n):
#
# Back in the olden days, routines like this were needed
# No idea how python initializes things
#
    i=0
    while m < i < n:
        x[i]=0
        i=i+1
    return

def Convolve_TimeSeries(d,ld,f,lf,o,lo):
#
# convolves two time series
# For conversation purposes, d is the data and f is the filter
#
    lo=ld+lf-1
    Zero_List(o,1,lo)
    for i in range (0,ld):
        for j in range (0,lf):
            k=i+j
#            print(i,j,k)
            o[k]=o[k]+d[i]*f[j]
    return
