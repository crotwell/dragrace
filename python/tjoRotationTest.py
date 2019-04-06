import sys
import struct
import array
import math
from SeismogramTasks import *
#
# [theta,alpha] pairs for a 30deg wall at FL & NR, vertical at NL and NR and ground installation at CT
# Order: FL,FR,NL,NR,CT
#
angles=[["FL",60,0], ["FR",-120,180], ["NL",90,0], ["NR",-90,180], ["CT",0,0]]
#
# Some arbitrary signals that we will hopefully recover
#
dragsters=[[0,0,1],[-1,0,0],[0,1,0],[0.5,0.5,0.5]]
#added gravity by hand, ugh
signals=[[0,0,2],[-1,0,1],[0,1,1],[0.5,0.5,1.5]]

startingSignals=[]
local=[]
for position in signals:
    for rotation in angles:
       local=Global2Local_Pseudo3D_Rotation(position[0],position[1],position[2],rotation[1],rotation[2])
       #[yp,zp]=Coordinate_Rotation_2D(position[1],position[2],-rotation[2])
       #print('Angles {}, Output: Z={:4.3f}, Y={:4.3f}'.format(rotation,zp,yp))
       #[zp1,xp] = Coordinate_Rotation_2D(zp,position[0],-rotation[1])
#       print('Angles {}, Starting Orientation: [{:4.3f},{:4.3f},{:4.3f}]'.format(rotation,xp,yp,zp1))
       print('Angles {}, Initial: [{:4.3f},{:4.3f},{:4.3f}],Ready: [{:4.3f},{:4.3f},{:4.3f}]'.format(rotation,position[0],position[1],position[2],local[0],local[1],local[2]))
       startingSignals.append([rotation[0],local[0],local[1],local[2]])
    print('====')
#
# To recover, we do theta rotation first, then alpha rotation
#
correctedSignals=[]
dragsterSignals=[]
track=[]
for position in startingSignals:
    for rotation in angles:
       if(position[0] == rotation[0]):
           track=Local2Global_Pseudo3D_Rotation(position[1],position[2],position[3],rotation[1],rotation[2])
           #[zp,xp] = Coordinate_Rotation_2D(position[3],position[1],rotation[1])
           #yp,zp1]= Coordinate_Rotation_2D(position[2],zp,rotation[2])
           print('Angles {}, Start: [{:4.3f},{:4.3f},{:4.3f}],      End: [{:4.3f},{:4.3f},{:4.3f}]'.format(rotation,position[1],position[2],position[3],track[0],track[1],track[2]))
    correctedSignals.append([local[0],local[1],local[2]])
    dragsterSignals.append([local[0],local[1],local[2]-1])
print('===')

print('=== Original Dragster Signals ===')
print(dragsters)
print('===')
#print(dragsterSignals)
#
#for i in [0, 1, 2, 3, 4]:
#    print('Angles: {} Dragster: {} Recovered {}'.format(angles[i],dragsters[i],dragsterSignals[i]))
