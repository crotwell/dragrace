## create a 3-D transformation matrix

import math
import array
import numpy as np
import vpython as vp # pip install vpython

v1 = vp.vector(1,0,0) # creates a vector of floating points [0.0,0.0,1.0]
# print(v1)
# print(type(v1)) # class 'vpython.cyvector.vector'
# print(v1.x, v1.y, v1.z) # returns each component

# ROTATE
degrees_from_vertical = 20.0
degrees_rotate = degrees_from_vertical + 90.0
theta = math.radians(degrees_rotate) # theta is radians of measured degrees
v2 = vp.rotate(v1,angle=theta,axis=vp.vector(0,1,0))
print("vp rotate: {}".format(v2))
# print(v2) # outputs a rotation of v1 about the y-axis by theta radians

# gabby stuff
A = np.array([[0.94, 0.0, 0.34],[0,1,0],[-0.342,0.0,0.94]])  # coordinate transform matrix for 20 deg
v_prime = np.array([1,0,0])
v = np.matmul(A,v_prime)
# print("matlab rotate: {}".format(v))

# making own CS transform of 20 deg from vertical = 110 deg roration
A_jake = np.array([[math.cos(math.radians(110)),math.cos(math.radians(0.0)),math.cos(math.radians(200.0))],
                [0,math.cos(math.radians(0)),0],
                [math.cos(math.radians(20)),0,math.cos(math.radians(110))]])
# coordiate rotation matrix of 110 deg counter clockwise about y axis
# print(A_jake)
v_prime_jake = np.array([1,0,0]) # vector in prime CS aligned with x' axis
v_jake = np.matmul(A_jake,v_prime_jake)
print("v_jake rotate: {}".format(v_jake))

# try to flip this vector about z axis
# A_flip =
# xlocal,ylocal,zlocal are components of a vector in the
# accelerometer's coordinate system.
# First, build 3x3 transformation matrix A given a theta to rotate with.
# Then, multiply rows 1 - 3 of A by xlocal, ylocal, zlocal components
# respectively. This results in a 3x1 vector of x,y,z components
# in the global coordinate system (the CS that we defined as, if looking
# down-track, +x pointing to the left of the track, +y pointing down-track,
# +z pointing straight down to your toes.)

# use an example of rotating 30 degrees about the y axis in which the
# x-axis rotates 30 degrees towards the z-axis
# A = [[0, 0, 0],
# [0, 0, 0],
# [0, 0, 0]]
A = np.zeros((3,3))
xlocal = [1,0,0]
ylocal = [0,1,0]
zlocal = [0,0,1]




# m rows and n columns
# def 3DTransform(xlocal,ylocal,zlocal,theta):
#     for m in range(2):
#         for n in range(2):
#             A[m][n] = 1

# for m in range(3):
#     for n in range(3):
#         A[m][n] = 1


#
# print(A)

# print(np.shape(A))
# print(range(2))
