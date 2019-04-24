import simpleDali
import simpleMiniseed
import asyncio
import logging
import signal
import sys
import json
from datetime import datetime, timedelta, date, timezone
from array import array
import os
import dateutil.parser
from threading import Thread
import time

# logging.basicConfig(level=logging.DEBUG)


host = "129.252.35.36"
port = 15003
#host = "129.252.35.20"
#host = "127.0.0.1"
#port = 6382
uri = "ws://www.seis.sc.edu/dragracews/datalink"

programname="triggerListen"
username="dragrace"
processid=0
architecture="python"

keepGoing = True
# create global variables for maxAccPacket list and Trigger Holding Pin
maxAccPacket_list = []
trig_HoldingPin = []

def handleSignal(sigNum, stackFrame):
    print("############ handleSignal {} ############".format(sigNum))
    global keepGoing
    if keepGoing:
        keepGoing = False
    else:
        sys.exit(0)

signal.signal(signal.SIGINT, handleSignal)
signal.signal(signal.SIGTERM, handleSignal)

async def doTest(loop):
    #dali = simpleDali.SocketDataLink(host, port)
    global maxAccPacket_list
    global trig_HoldingPin
    dali = simpleDali.WebSocketDataLink(uri)
    # dali.verbose = True
    serverId = await dali.id(programname, username, processid, architecture)
    print("Resp: {}".format(serverId))
    serverInfo = await dali.info("STATUS")
    print("Info: {} ".format(serverInfo.message))
    #serverInfo = yield from dali.info("STREAMS")
    #print("Info: {} ".format(serverInfo.message))
    r = await dali.match(".*/(MAXACC|MTRIG)")
    print("match() Resonse {}".format(r))

    # begintime = simpleDali.utcnowWithTz() - timedelta(minutes=5)
    # r = await dali.positionAfter(begintime)
    # if r.type.startswith("ERROR"):
    #     print("positionAfter() Resonse {}, ringserver might not know about these packets?".format(r))
    # else:
    #     print("positionAfter() Resonse m={}".format(r.message))
    r = await dali.stream()

    while(keepGoing):
        packet = await dali.parseResponse()
        # print("got a packet: {}".format(packet.streamId))


        # from MMA8451ToMseed.py lines 430-435
        # peakPacket = await configDali.parseResponse()
        # print("got a packet: {}".format(peakPacket.streamId,))
        # if  peakPacket.streamId.endswith("ZMAXCFG"):
        #     config = json.loads(peakPacket.data.decode("'UTF-8'"))
        if packet.streamId.endswith("MAXACC"):
            HandleMaxACC_Packet(packet)

        elif packet.streamId.endswith("MTRIG"):
            HandleTriggerPacket(packet)
            ProcessHoldingPin()
        else:
            print("Packet is not a MaxACC or a Trigger")
            continue

    dali.close()

def HandleMaxACC_Packet(packet):
    global maxAccPacket_list
    global trig_HoldingPin
    maxAccPacket = json.loads(packet.data.decode("'UTF-8'"))
    if maxAccPacket["maxacc"] > 1.0:
        print('ACC too Large: {}'.format(1.0))

    maxAccPacket["start_time"] = dateutil.parser.parse(maxAccPacket["start_time"])
    maxAccPacket["start_time"].replace(tzinfo = timezone.utc)
    maxAccPacket["end_time"] = dateutil.parser.parse(maxAccPacket["end_time"])
    maxAccPacket["end_time"].replace(tzinfo = timezone.utc)
    maxAccPacket_list.append(maxAccPacket)
    if len(maxAccPacket_list) > 2000: # number subject to change
        maxAccPacket_list = maxAccPacket_list[1:]

    else:
        pass




def HandleTriggerPacket(packet):
    global maxAccPacket_list
    global trig_HoldingPin
    trig = json.loads(packet.data.decode("'UTF-8'"))
    print("trig start {}".format(trig["startTime"]))
    print("trig end {}".format(trig["endTime"]))

    trig["startTime"] = dateutil.parser.parse(trig["startTime"])
    trig["startTime"].replace(tzinfo = timezone.utc)
    trig["endTime"] = dateutil.parser.parse(trig["endTime"])
    trig["endTime"].replace(tzinfo = timezone.utc)
    trig_HoldingPin.append(trig)

def ProcessHoldingPin():

    global maxAccPacket_list
    global trig_HoldingPin
    tooYoungTriggers = []
    for trig in trig_HoldingPin:
        # convert incoming isoformat objects into datetime objects
        # *** check to verify correct method to do this ***


        if trig["endTime"] < simpleDali.utcnowWithTz():
        # process the trigger: look trough maxAccPacket_list, find the maxacc
        # for each location
            FL_acc = [0]
            NL_acc = [0]
            # CT_acc = []
            NR_acc = [0]
            FR_acc = [0]
            m = maxAccPacket_list[0]
            # print("maxAccPacket_list {} {} {}".format(m["start_time"], m["end_time"],m["station"]))
            # print("trig  {} {}".format(trig["startTime"], trig["endTime"]))

            count = 0

            for maxAccJson in maxAccPacket_list:
                # while maxcc's starttime > trig starttime AND maxacc's endtime < trigs endtime create a new results json
                # this loop calls upon the keys of each individual json object as it loop through the big max acc packet list
                if maxAccJson["start_time"] > trig["startTime"] and maxAccJson["end_time"] < trig["endTime"]:
                    count = count + 1
                    if maxAccJson["station"] == "FL":
                        FL_acc.append(maxAccJson["maxacc"])
                    elif maxAccJson["station"] == "NL":
                        NL_acc.append(maxAccJson["maxacc"])
                    # if maxAccJson["station"] == "CT"
                    #     CT_acc.append(maxAccJson["maxacc"])
                    elif maxAccJson["station"] == "NR":
                        NR_acc.append(maxAccJson["maxacc"])
                    elif maxAccJson["station"] == "FR":
                        FR_acc.append(maxAccJson["maxacc"])
                    else:
                        print("maxACC Packet doesn't contain a station")
                # else:
            #         print("maxacc packet too old {}".format(maxAccJson["start_time"]))
            # print("count {} {}".format(count, len(maxAccPacket_list)))

            today = date.today()
            weekday = date.isoweekday(today)
            if weekday == 1:
                dayName = "Monday"
            if weekday == 2:
                dayName = "Tuesday"
            if weekday == 3:
                dayName = "Wednesday"
            if weekday == 4:
                dayName = "Thursday"
            if weekday == 5:
                dayName == "Friday"
            if weekday == 6:
                dayName = "Saturday"
            if weekday == 7:
                dayName = "Sunday"
            trig["startTime"] = trig["startTime"].strftime("%Y-%m-%dT%H:%M:%SZ")
            trig["endTime"] = trig["endTime"].strftime("%Y-%m-%dT%H:%M:%SZ")
            ResultsJson = {
                "Day_Name": dayName,
                "Trigger_Info": trig,
                # Trigger info is a json that contains Duty Officer, Starttime, Endtime
                "peakACC_FL": max(FL_acc),
                "peakACC_NL": max(NL_acc),
                # "peakACC_CT": max(CT_acc),
                "peakACC_NR": max(NR_acc),
                "peakACC_FR": max(FR_acc),
                # add day: Friday Saturday Sunday as part of json
                # add duty office (from trigger)
                # add class name
            }
            # dump ResultsJson into a directory, index html
            # sends ResultsJson to directories
            SendResultsJson(ResultsJson)
        else:
            tooYoungTriggers.append(trig)
            # else: keep looping...
        trig_HoldingPin = tooYoungTriggers

def SendResultsJson(ResultsJson):
    day = ResultsJson["Day_Name"]
    classType = ResultsJson["Trigger_Info"]["class"] # need to see updated trig with info!
    heat = ResultsJson["Trigger_Info"]["heat"] # need to see updated trig with info!

    # Define directories to put jsons into
    resultsPath = "mseed/www/results/{}/{}/{}".format(day,classType,heat)
    classNamesPath = "mseed/www/results/{}".format(day)
    heatNamesPath = "mseed/www/results/{}/{}".format(day,classType)

    # Define file paths for jsons to send
    resultsFile = "mseed/www/results/{}/{}/{}/results.json".format(day,classType,heat)
    classNamesFile = "mseed/www/results/{}/classnames.json".format(day)
    heatNamesFile = "mseed/www/results/{}/{}/heatnames.json".format(day,classType)

    # Create directories baased on directory PATHS defined 181-184
    if not os.path.exists(resultsPath):
        os.makedirs(resultsPath)
    if not os.path.exists(classNamesPath):
        os.makedirs(classNamesPath)
    if not os.path.exists(heatNamesPath):
        os.makedirs(heatNamesPath)

    # NOTE: classType, heat, resultsPath, classNamesPath, heatNamesPath ALL
    # need to be checked with updated trigger from gabby

    # send ResultsJson to directory

    with open(resultsFile,"w") as f:
        if f is not None:
            json.dump(ResultsJson,f)

    # read in classnames.json

    try:
        with open(classNamesFile,'r') as f:
            if f is not None:
                classNames = json.load(f)
                # if class (ie top fuel) is not in classnames.json, add the class
                # to the classnames.json, then send this updated classnames.json to directory
                # else, pass
            else:
                pass
            if classNames.count(classType) == 0:
                classNames.append(classType)
                with open(classNamesFile,'w') as f:
                    json.dump(classNames,f)
            else:
                pass
# first iteration through, create a classNames array
    except FileNotFoundError:
        classNames = [classType]
        with open(classNamesFile,'w') as f:
            json.dump(classNames,f)



    # read in heatNames.json
    try:
        with open(heatNamesFile,'r') as f:
            if f is not None:
                heatNames = json.load(f)
                # if heat (ie heat 2) is not in heatnames.json, add the heat
                # to the heatnames.json, then send this updated heatnames.json to directory
                # else, pass
            else:
                pass
            if heatNames.count(heat) == 0:
                heatNames.append(heat)
                with open(heatNamesFile,'w') as f:
                    json.dump(heatNames,f)
            else:
                pass
# first iteration through, create a heat array
    except FileNotFoundError:
        heatNames = [heat]
        with open(heatNamesFile,'w') as f:
            json.dump(heatNames,f)

    print('I succesffuly sent results to results directory!')
def loopHoldingPen():
    while True:
        ProcessHoldingPin()
        time.sleep(1)

sendThread = Thread(target = loopHoldingPen)
sendThread.daemon=True
print("thread start")
sendThread.start()


loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(doTest(loop))
loop.close()
