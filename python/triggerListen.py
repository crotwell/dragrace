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
import queue

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

maxAccPacket_list = []
trig_HoldingPen = queue.Queue()

def handleSignal(sigNum, stackFrame):
    print("############ handleSignal {} ############".format(sigNum))
    global keepGoing
    if keepGoing:
        keepGoing = False
    else:
        sys.exit(0)

signal.signal(signal.SIGINT, handleSignal)
signal.signal(signal.SIGTERM, handleSignal)

async def doReconnect(dali):
    if dali is None:
        #dali = simpleDali.WebSocketDataLink(uri)
        dali = simpleDali.SocketDataLink(host, port)
    await dali.reconnect()
    serverId = await dali.id(programname, username, processid, architecture)
    print("Resp: {}".format(serverId))
    serverInfo = await dali.info("STATUS")
    print("Info: {} ".format(serverInfo.message))
    r = await dali.match(".*/(MAXACC|MTRIG)")
    print("match() Resonse {}".format(r))
    r = await dali.stream()
    return dali

async def doTest(loop):
    global maxAccPacket_list
    dali = await doReconnect(None)
    while(keepGoing):
        try:
            c =
            if dali is None or dali.isClosed():
                print("dali closed, reconnecting")
                dali = await doReconnect(dali)
            packet = await dali.parseResponse()

            if packet.streamId.endswith("MAXACC"):
                HandleMaxACC_Packet(packet)

            elif packet.streamId.endswith("MTRIG"):
                HandleTriggerPacket(packet)
                ProcessHoldingPen()
            else:
                print("Packet is not a MaxACC or a Trigger")
                continue
        except Exception as e:
            print("error while streaming: ".format(e))
            await dali.close()
    print("doTest, end while keepGoing={}".format(keepGoing))
    await dali.close()

def HandleMaxACC_Packet(packet):
    global maxAccPacket_list
    maxAccPacket = json.loads(packet.data.decode("'UTF-8'"))

    maxAccPacket["start_time"] = dateutil.parser.parse(maxAccPacket["start_time"])
    maxAccPacket["start_time"].replace(tzinfo = timezone.utc)
    maxAccPacket["end_time"] = dateutil.parser.parse(maxAccPacket["end_time"])
    maxAccPacket["end_time"].replace(tzinfo = timezone.utc)
    maxAccPacket_list.append(maxAccPacket)
    if len(maxAccPacket_list) > 2000: # list reaches max length after 1 min, 25 secs.
        maxAccPacket_list = maxAccPacket_list[1:]

    else:
        pass

def HandleTriggerPacket(packet):
    global maxAccPacket_list
    global trig_HoldingPen
    trig = json.loads(packet.data.decode("'UTF-8'"))
    print("trig start {}".format(trig["startTime"]))
    print("trig end {}".format(trig["endTime"]))

    trig["startTime"] = dateutil.parser.parse(trig["startTime"])
    trig["startTime"].replace(tzinfo = timezone.utc)
    trig["endTime"] = dateutil.parser.parse(trig["endTime"])
    trig["endTime"].replace(tzinfo = timezone.utc)
    trig_HoldingPen.put(trig)

def ProcessHoldingPen():
    global maxAccPacket_list
    global trig_HoldingPen
    tooYoungTriggers = []
    trig = trig_HoldingPen.get()
    while trig["endTime"] > simpleDali.utcnowWithTz():
        time.sleep(1)
    FL_acc = [0]
    NL_acc = [0]
    CT_acc = [0]
    NR_acc = [0]
    FR_acc = [0]
    FL0_acc = [0]
    FL4G_acc = [0]
    FL60_acc = [0]
    FL330_acc = [0]
    FL660_acc = [0]
    FL1K_acc = [0]
    m = maxAccPacket_list[0]
    # print("maxAccPacket_list {} {} {}".format(m["start_time"], m["end_time"],m["station"]))
    # print("trig  {} {}".format(trig["startTime"], trig["endTime"]))
    count = 0
    for maxAccJson in maxAccPacket_list:
        if maxAccJson["start_time"] > trig["startTime"] and maxAccJson["end_time"] < trig["endTime"]:
            count = count + 1
            if maxAccJson["station"] == "FL":
                FL_acc.append(maxAccJson["maxacc"])
            elif maxAccJson["station"] == "NL":
                NL_acc.append(maxAccJson["maxacc"])
            elif maxAccJson["station"] == "CT":
                CT_acc.append(maxAccJson["maxacc"])
            elif maxAccJson["station"] == "NR":
                NR_acc.append(maxAccJson["maxacc"])
            elif maxAccJson["station"] == "FR":
                FR_acc.append(maxAccJson["maxacc"])
            elif maxAccJson["station"] == "FL0":
                FL0_acc.append(maxAccJson["maxacc"])
            elif maxAccJson["station"] == "FL60":
                FL60_acc.append(maxAccJson["maxacc"])
            elif maxAccJson["station"] == "FL330":
                FL330_acc.append(maxAccJson["maxacc"])
            elif maxAccJson["station"] == "FL660":
                FL660_acc.append(maxAccJson["maxacc"])
            elif maxAccJson["station"] == "FL1K":
                FL1K_acc.append(maxAccJson["maxacc"])
            elif maxAccJson["station"] == "FL4G":
                FL4G_acc.append(maxAccJson["maxacc"])
            else:
                #print("maxACC Packet doesn't contain a station: {}".format(maxAccJson))
                pass
    d = datetime.now(timezone.utc)
    edt = timezone(timedelta(hours=-4), name="EDT")
    d_edt = d.astimezone(tz=edt)
    weekday = date.isoweekday(d_edt)
    if weekday == 1:
        dayName = "Monday"
    if weekday == 2:
        dayName = "Tuesday"
    if weekday == 3:
        dayName = "Wednesday"
    if weekday == 4:
        dayName = "Thursday"
    if weekday == 5:
        dayName = "Friday"
    if weekday == 6:
        dayName = "Saturday"
    if weekday == 7:
        dayName = "Sunday"
    trig["startTime"] = trig["startTime"].strftime("%Y-%m-%dT%H:%M:%SZ")
    trig["endTime"] = trig["endTime"].strftime("%Y-%m-%dT%H:%M:%SZ")
    ResultsJson = {
        "Day_Name": dayName,
        "Trigger_Info": trig,
        "peakACC_FL": max(FL_acc),
        "peakACC_NL": max(NL_acc),
        "peakACC_CT": max(CT_acc),
        "peakACC_NR": max(NR_acc),
        "peakACC_FR": max(FR_acc),
        "peakACC_FL0": max(FL0_acc),
        "peakACC_FL60": max(FL60_acc),
        "peakACC_FL330": max(FL330_acc),
        "peakACC_FL660": max(FL660_acc),
        "peakACC_FL1K": max(FL1K_acc),
        "peakACC_FL4G": max(FL4G_acc),
    }
    SendResultsJson(ResultsJson)
    MostRecentResult = {
        "class": trig["class"],
        "heat": trig["heat"],
        "day": dayName
    }
    with open("mseed/www/results/MostRecentResult.json","w") as f:
        if f is not None:
            json.dump(MostRecentResult,f)
        else:
            print("can't save results to mseed/www/results/MostRecentResult.json for {}".format(MostRecentResult))

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

    # send ResultsJson to directory
    with open(resultsFile,"w") as f:
        if f is not None:
            json.dump(ResultsJson,f)
        else:
            print("can't save results to {}".format(resultsFile))

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
        ProcessHoldingPen()
        time.sleep(1)
    print("holding pen quit")

sendThread = Thread(target = loopHoldingPen)
sendThread.daemon=True
print("thread start")
sendThread.start()

loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(doTest(loop))
loop.close()
