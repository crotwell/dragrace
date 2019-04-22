import simpleDali
import simpleMiniseed
import asyncio
import logging
import signal
import sys
import json
from datetime import datetime, timedelta, date
from array import array
import os

logging.basicConfig(level=logging.DEBUG)


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
    dali = simpleDali.WebSocketDataLink(uri)
    dali.verbose = True
    serverId = await dali.id(programname, username, processid, architecture)
    print("Resp: {}".format(serverId))
    serverInfo = await dali.info("STATUS")
    print("Info: {} ".format(serverInfo.message))
    #serverInfo = yield from dali.info("STREAMS")
    #print("Info: {} ".format(serverInfo.message))
    r = await dali.match(".*/(MAXACC|MTRIG) ")
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
        print("got a packet: {}".format(packet.streamId))


        # from MMA8451ToMseed.py lines 430-435
        # peakPacket = await configDali.parseResponse()
        # print("got a packet: {}".format(peakPacket.streamId,))
        # if  peakPacket.streamId.endswith("ZMAXCFG"):
        #     config = json.loads(peakPacket.data.decode("'UTF-8'"))
        if packet.streamId.endswith("MAXACC"):
            maxAccPacket_list = HandleMaxACC_Packet(packet)

        if packet.streamId.endswith("MTRIG"):
            ResultsJson = HandleTriggerPacket(packet)
        else:
            print("Packet is not a MaxACC or a Trigger")
            continue
        # sends ResultsJson to directories
        SendResultsJson(ResultsJson)

    dali.close()

def HandleMaxACC_Packet(packet):
    maxAccPacket = json.loads(packet.data.decode("'UTF-8'"))
    maxAccPacket_list.append(maxAccPacket)
    if length(maxAccPacket_list) > 2000: # number subject to change
        maxAccPacket_list = maxAccPacket_list[1:]

    else:
        pass

    return maxAccPacket_list


def HandleTriggerPacket(packet):
    trig = json.loads(packet.data.decode("'UTF-8'"))
    trig_HoldingPin.append(trig)
    tooYoungTriggers = []
    for trig in trig_HoldingPin:
        # convert incoming isoformat objects into datetime objects
        # *** check to verify correct method to do this ***
        trig["startTime"] = datetime.fromisoformat(trig["startTime"])
        trig["endTime"] = datetime.fromisoformat(trig["endTime"])

        if trig["endTime"] < simpleDali.utcnowWithTz():
        # process the trigger: look trough maxAccPacket_list, find the maxacc
        # for each location
            FL_acc = []
            NL_acc = []
            # CT_acc = []
            NR_acc = []
            FR_acc = []

            for maxAccJson in maxAccPacket_list:
                # while maxcc's starttime > trig starttime AND maxacc's endtime < trigs endtime create a new results json
                # this loop calls upon the keys of each individual json object as it loop through the big max acc packet list
                if maxAccJson["start_time"] > trig["startTime"] and maxAccJson["end_time"] < trig["endTime"]:

                    if maxAccJson["station"] == "FL":
                        FL_acc.append(maxAccJson["maxacc"])
                    if maxAccJson["station"] == "NL":
                        NL_acc.append(maxAccJson["maxacc"])
                    # if maxAccJson["station"] == "CT"
                    #     CT_acc.append(maxAccJson["maxacc"])
                    if maxAccJson["station"] == "NR":
                        NR_acc.append(maxAccJson["maxacc"])
                    if maxAccJson["station"] == "FR":
                        FR_acc.append(maxAccJson["maxacc"])
                    else:
                        print("maxACC Packet doesn't contain a station")

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
            ResultsJson = {
                # "trigger_startTime": trig["startTime"].isoformat(),
                # "trigger_endTime": trig["endTime"].isoformat(),
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
        else:
            tooYoungTriggers.append(trig)
            # else: keep looping...


        trig_HoldingPin = tooYoungTriggers
        return ResultsJson

def SendResultsJson(ResultsJson):
    productionDirectory="/home/geo/Production"
    LiveStreamDirectory = productionDirectory + "/Run/mseed/www/LiveStream"
    os.mkdirs(LiveStreamDirectory)
    return








loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(doTest(loop))
loop.close()
