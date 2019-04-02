## create a 3-D transformation matrix

import math
import array
import numpy as np

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



print(A)

# print(np.shape(A))
# print(range(2))
