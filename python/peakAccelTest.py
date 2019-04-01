from SeismogramTasks import VectorMagnitude, Rotate_2D_TimeSeries, Coordinate_Rotation_2D
from peakACC import Magnitude_ThreeC_TimeSeries_jake
import math

x = [1.2, 1.5, 0.0, 0.4, -0.3, 1.5]
y = [0.3, 0.2, 0.7, 0.3, 0.0, -0.5]
z = [-0.1, 1.2, 1.4, 1.0, 1.1, 0.2]

theta = [110.0, 45.0, -45.0, 20.0, -20.0, 30.0]

# Rotate xyz array, find vector mag
def maxaccel(x,y,z,theta):
    # Rotate
    r = Rotate_2D_TimeSeries(x, z, theta)
    x_prime = r[0]
    z_prime = r[1]
    # x_prime = []
    # z_prime = []
    # for i,j,k in x,z,theta:
    #     r = Coordinate_Rotation_2D(i, j, k)
    #     x_prime.append(r[0])
    #     z_prime.append(r[1])

    # find vector mag
    vmag = Magnitude_ThreeC_TimeSeries_jake(x_prime,z_prime,y)
    ACCjson = {
        "x": x_prime,
        "y": y,
        "z": z_prime,
        "theta": theta,
        "VMAG": vmag
    }
    return ACCjson

v = maxaccel(x,y,z,110.0)
# # print(v)
#
magnitude = v["VMAG"]
print(magnitude)
