#!/bin/bash

echo "Starting " > /home/pi/Production/Run/run.log
/usr/bin/python3 /home/pi/Production/dragrace/python/MMA8451ToMSeed.py >> /home/pi/Production/Run/run.log 2>&1
