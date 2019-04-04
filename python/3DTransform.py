## create a 3-D transformation matrix

import math
import array
import numpy as np
import vpython as vp # pip install vpython

v1 = vp.vector(1,0,0) # creates a vector of floating points [1.0,0.0,0.0]
# # print(v1)
# # print(type(v1)) # class 'vpython.cyvector.vector'
# # print(v1.x, v1.y, v1.z) # returns each component
#
# # ROTATE
# degrees_from_vertical = 20.0
degrees_rotate = 90.0
theta = math.radians(degrees_rotate) # theta is radians of measured degrees
v2 = vp.rotate(v1,angle=theta,axis=vp.vector(0,1,0))
print("vp rotate: {}".format(v2))
# print(type(v2))
# print(v2) # outputs a rotation of v1 about the y-axis by theta radians
#
# # making own CS transform of 20 deg from vertical = 110 deg roration
# A_jake = np.array([[math.cos(math.radians(110)),math.cos(math.radians(0.0)),math.cos(math.radians(200.0))],
#                 [0,math.cos(math.radians(0)),0],
#                 [math.cos(math.radians(20)),0,math.cos(math.radians(110))]])
# # coordiate rotation matrix of 110 deg counter clockwise about y axis
# # print(A_jake)
# v_prime_jake = np.array([1,0,0]) # vector in prime CS aligned with x' axis
# v_jake = np.matmul(A_jake,v_prime_jake)
# print("v_jake rotate: {}".format(v_jake))


def CoordinateRotation_3D(x,y,z,theta,alpha):
    v1 = vp.vector(x,y,z)
    # Rotate about y'-axis for x' to x and z' to z
    theta_radians = math.radians(theta) # theta is radians of measured degrees
    v_abouty = vp.rotate(v1,angle=theta_radians,axis=vp.vector(0,1,0))

    # Rotate about x-axis for y' to y and z' to z
    alpha_radians = math.radians(alpha)
    v_aboutx = vp.rotate(v_abouty,angle=alpha_radians,axis=vp.vector(1,0,0))
    return v_aboutx

# FL = CoordinateRotation_3D(1,0,0,theta = 70.0,alpha = 0.0)
# print("FL: {}".format(FL))
CL = CoordinateRotation_3D(1,0,0,theta=90.0,alpha=0.0)
print("CL: {}".format(CL))
# CT = CoordinateRotation_3D(1,0,0,theta=0.0,alpha=0.0)
# print("CT: {}".format(CT))
# CR = CoordinateRotation_3D(1,0,0,theta=90.0,alpha=180.0)
# print("CR: {}".format(CR))
# FR = CoordinateRotation_3D(1,0,0,theta=110.0,alpha=180.0)
# print("FR: {}".format(FR))

A = np.array([[0,0,0],[0,1,0],[-1,0,0]])
v_prime = np.array([1,0,0])
v_new = np.matmul(A,v_prime)
print("v matrix: {}".format(v_new))

# def Rotate_3D_TimeSeries(x,y,z,theta,alpha)
