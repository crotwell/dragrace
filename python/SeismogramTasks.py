import sys
import struct
import array
import math
import vpython as vp # pip install vpython
# from vypthon import rotate
# from vpython import vector



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
    vmag=[]
    while i < nptsx:
        vmag.append(VectorMagnitude(x[i],y[i],z[i]))
        i=i+1
    return vmag

def Divide_TimeSeries(x,factor):
    npts=len(x)
    i=0
    xf=[]
    while i < npts:
        xf.append(x[i]/factor)
        i=i+1
    return xf

def Multiply_TimeSeries(x,factor):
    npts=len(x)
    i=0
    xf=[]
    while i < npts:
        xf.append(x[i]*factor)
        i=i+1
    return xf

def Add_TimeSeries(x,factor):
    npts=len(x)
    i=0
    xf=[]
    while i < npts:
        xf.append(x[i]+factor)
        i=i+1
    return xf

def Subtract_TimeSeries(x,factor):
    npts=len(x)
    i=0
    xf=[]
    while i < npts:
        xf.append(x[i]-factor)
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
#  This can be used for other rotations, of course:
#
#   (x,y) in the call is (x,y) only for a rotation about z.
#   (x,y) in the call is (z,x) in a rotation about y.
#   (x,y) in the call is (y,z) in a rotation about x.
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
    xprime=[]
    yprime=[]
    i=0
    while i < nptsx:
        [xp, yp]=Coordinate_Rotation_2D(x[i],y[i],theta)
        xprime.append(xp)
        yprime.append(yp)
        i=i+1
    return [xprime, yprime]

def Global2Local_Pseudo3D_Rotation(xglobal,yglobal,zglobal,theta,alpha):
    [ylocal,ztmp]=Coordinate_Rotation_2D(yglobal,zglobal,-alpha)
    [zlocal,xlocal]=Coordinate_Rotation_2D(ztmp,xglobal,-theta)
#
#  Input: a point in the Global coordinate system
#  Output:  The same point in the Local coordinate system
#
#  The relationship between Global and Local is given by two rotation angles.
#  This assumes there is at least one axis in common between the Local and Global system
#     thus, it is only a psuedo-3D rotation.
#
#  The angle theta defines a clockwise rotation about the common axis
#      [looking in the +direction of the local version of that axis]
#  The theta rotation takes the other two axes from Local to Global
#
#  The angles were flushed out assuming you had data in the Local system and wanted it in the Global system
#
#  The angle alpha defines a clockwise rotation about one of the initially non-common axes [same convention]
#  The alpha rotation ensures that the +direction of the common axis is the same in the Local and Global system
#
#  The code as written assumes that the common axis is the Y-axis.  It might work in other cases with judicial choice
#      of the (x,y,z) order in the argument list.  Test first!
#
#  In this Global=>Local version, the sign of the angles is reversed and the alpha rotation is done first.
#
#  See Coordinate_Rotation_2D for why the argument order is the way it is in those calls
#
    return [xlocal,ylocal,zlocal]

def Local2Global_Pseudo3D_Rotation(xlocal,ylocal,zlocal,theta,alpha):
    [ztmp,xglobal]=Coordinate_Rotation_2D(zlocal,xlocal,theta)
    [yglobal,zglobal]=Coordinate_Rotation_2D(ylocal,ztmp,alpha)
#
#  Input: a point in the Global coordinate system
#  Output:  The same point in the Local coordinate system
#
#  The relationship between Global and Local is given by two rotation angles.
#  This assumes there is at least one axis in common between the Local and Global system
#     thus, it is only a psuedo-3D rotation.
#
#  The angle theta defines a clockwise rotation about the common axis
#      [looking in the +direction of the local version of that axis]
#  The theta rotation takes the other two axes from Local to Global
#
#  The angles were flushed out assuming you had data in the Local system and wanted it in the Global system
#
#  The angle alpha defines a clockwise rotation about one of the initially non-common axes [same convention]
#  The alpha rotation ensures that the +direction of the common axis is the same in the Local and Global system
#
#  The code as written assumes that the common axis is the Y-axis.  It might work in other cases with judicial choice
#      of the (x,y,z) order in the argument list.  Test first!
#
#  In this Local=>Global version, the theta rotation is done first, then the alpha rotation
#
#  See Coordinate_Rotation_2D for why the argument order is the way it is in those calls.
#
    return [xglobal,yglobal,zglobal]

def Zero_List(m,n):
#
# Back in the olden days, routines like this were needed
# No idea how python initializes things
#
    i=0
    y=[]
    while m < i < n:
        y.append(0)
        i=i+1
    return y

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


def CoordinateRotation_3D(x,y,z,theta,alpha):
    v1 = vp.vector(x,y,z)   # vector in x',y',z' CS

    # Rotate about y'-axis for x' to x and z' to z
    theta_radians = math.radians(theta) # theta is radians of measured degrees
    v_abouty = vp.rotate(v1,angle=theta_radians,axis=vp.vector(0,1,0))

    # Rotate about x-axis for y' to y and z' to z
    alpha_radians = math.radians(alpha)
    v_aboutx = vp.rotate(v_abouty,angle=alpha_radians,axis=vp.vector(1,0,0))
    v_x = v_aboutx.x
    v_y = v_aboutx.y
    v_z = v_aboutx.z
    return [v_x,v_y,v_z]

def Rotate_3D_TimeSeries(x,y,z,theta,alpha):
    nptsx=len(x)
    nptsy=len(y)
    nptsz=len(z)
    if nptsx != nptsy:
        print("Mismatch npts",nptsx,nptsy)
        return
    xprime=[]
    yprime=[]
    zprime=[]
    i=0
    while i < nptsx:
        [xp, yp, zp]=CoordinateRotation_3D(x[i],y[i],z[i],theta,alpha)
        xprime.append(xp)
        yprime.append(yp)
        zprime.append(zp)
        i=i+1
    return [xprime, yprime, zprime]

def subtractGravity(rotate_array_z, countToGravity):
    correct = []
    for i in rotate_array_z:
        correct.append(i-countToGravity) # substracting gravity
    return correct
