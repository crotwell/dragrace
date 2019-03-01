#!/bin/bash

echo "Starting " > /home/pi/mma8451/run.log
/usr/bin/python3 /home/pi/dragrace/python/MMA8451ToMSeed.py >> /home/pi/mma8451/run.log 2>&1
