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
#
# This section creates Local values starting from Global Signals
#
for position in signals:
    for rotation in angles:
       local=Global2Local_Pseudo3D_Rotation(position[0],position[1],position[2],rotation[1],rotation[2])
       print('Global: [{:05.3f},{:05.3f},{:05.3f}], Local: [{:05.3f},{:05.3f},{:05.3f}], Angles: {}'.format(position[0],position[1],position[2],local[0],local[1],local[2],rotation))
       startingSignals.append([rotation[0],local[0],local[1],local[2]])
    print('====')
#
# Now, let's see if we can recover the signals
#
correctedSignals=[]
dragsterSignals=[]
track=[]
for position in startingSignals:
    for rotation in angles:
       if(position[0] == rotation[0]):
#
# only do this when the location is the same in the local signal and the angle list
#
           track=Local2Global_Pseudo3D_Rotation(position[1],position[2],position[3],rotation[1],rotation[2])
           pgtrack=CoordinateRotation_3D(position[1],position[2],position[3],rotation[1],rotation[2])
           print('TJO: [{:05.3f},{:05.3f},{:05.3f}], Python Guys: [{:05.3f},{:05.3f},{:05.3f}], Angle: {}'.format(track[0],track[1],track[2],pgtrack[0],pgtrack[1],pgtrack[2],rotation))
           #print('Angles {}, Start: [{:4.3f},{:4.3f},{:4.3f}],      End: [{:4.3f},{:4.3f},{:4.3f}]'.format(rotation,position[1],position[2],position[3],track[0],track[1],track[2]))
    correctedSignals.append([local[0],local[1],local[2]])
    dragsterSignals.append([local[0],local[1],local[2]-1])
print('===')

print('=== Original Dragster Signals ===')
print(dragsters)
print('===')
