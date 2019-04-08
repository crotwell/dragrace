import argparse
import asyncio
import json
import math
import random
import signal
import time
from datetime import datetime, timedelta
#from netifaces import interfaces, ifaddresses, AF_INET
import socket
import traceback
import configChecker
import filecmp
import shutil

import simpleDali

configDirectory="./ConfigFiles"

oldfile=configDirectory+"/config_deployed"
newfile=configDirectory+"/config_new"

if(filecmp.cmp(oldfile,newfile)):
                   print("files are the same")
else:
   print("files differ")
   if(filecmp.cmp(oldfile,newfile)):
   # Files are the same, no action required
      noChange=True
   else:
   # Files are different, process the new one
      noChange=False
      json_file=open(newfile)
      goodConfig=configChecker.configSanityCheck(json_file)
      if(not goodConfig):
         print("Config file fails")
      else:
         print("Config file passes")
         starttime = simpleDali.utcnowWithTz()
         shutil.move(oldfile,oldfile+"_"+str(starttime))
         shutil.copy2(newfile,oldfile)
