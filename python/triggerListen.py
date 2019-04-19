import simpleDali
import simpleMiniseed
import asyncio
import logging
import signal
import sys
import json
from datetime import datetime, timedelta
from array import array

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

    begintime = simpleDali.utcnowWithTz() - timedelta(minutes=5)
    r = await dali.positionAfter(begintime)
    if r.type.startswith("ERROR"):
        print("positionAfter() Resonse {}, ringserver might not know about these packets?".format(r))
    else:
        print("positionAfter() Resonse m={}".format(r.message))
    r = await dali.stream()
    while(keepGoing):
        trig = await dali.parseResponse()
        if not trig.type == "PACKET":
            # might get an OK very first after stream
            print("parseResponse not a PACKET {} ".format(trig))
        else:
            print("Trigger: {}  {}".format(trig, json.dumps(json.loads(trig.data), indent=4)))

    dali.close()


loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(doTest(loop))
loop.close()


# import simpleDali
# import simpleMiniseed
# import asyncio
# import logging
# import signal
# import sys
# import json
# from datetime import datetime, timedelta
# from array import array
#
# logging.basicConfig(level=logging.DEBUG)
#
#
# host = "129.252.35.36"
# port = 15003
# #host = "129.252.35.20"
# #host = "127.0.0.1"
# #port = 6382
# uri = "ws://www.seis.sc.edu/dragracews/datalink"
#
# programname="triggerListen"
# username="dragrace"
# processid=0
# architecture="python"
#
# keepGoing = True
#
#
# def handleSignal(sigNum, stackFrame):
#     print("############ handleSignal {} ############".format(sigNum))
#     global keepGoing
#     if keepGoing:
#         keepGoing = False
#     else:
#         sys.exit(0)
#
# signal.signal(signal.SIGINT, handleSignal)
# signal.signal(signal.SIGTERM, handleSignal)
#
# async def doTest(loop):
#     #dali = simpleDali.SocketDataLink(host, port)
#     dali = simpleDali.WebSocketDataLink(uri)
#     dali.verbose = True
#     serverId = await dali.id(programname, username, processid, architecture)
#     print("Resp: {}".format(serverId))
#     serverInfo = await dali.info("STATUS")
#     print("Info: {} ".format(serverInfo.message))
#     #serverInfo = yield from dali.info("STREAMS")
#     #print("Info: {} ".format(serverInfo.message))
#     r = await dali.match(".*/(MAXACC|MTRIG) ")
#     print("match() Resonse {}".format(r))
#
#     # begintime = simpleDali.utcnowWithTz() - timedelta(minutes=5)
#     # r = await dali.positionAfter(begintime)
#     # if r.type.startswith("ERROR"):
#     #     print("positionAfter() Resonse {}, ringserver might not know about these packets?".format(r))
#     # else:
#     #     print("positionAfter() Resonse m={}".format(r.message))
#     r = await dali.stream()
#     maxAccPacket_list = []
#     trig_HoldingPin = []
#     while(keepGoing):
#         maxAccPacket = await dali.parseResponse()
#         trig = await dali.parseResponse()
#         # Question: how to parse out maxAccPacket and triggers
#
#         if maxAccPacket:
#             maxAccPacket_list.append(maxAccPacket)
#
#         if trig:
#             trig_HoldingPin.append(trig)
#
# # loop thru the trig_HoldingPin
#         for trig in trig_HoldingPin:
#             # convert incoming isoformat objects into datetime objects
#             trig["startTime"] = trig["startTime"].datetime()
#             trig["endTime"] = trig["startTime"].datetime()
#
#             if trig["endTime"] < datetime.utc.now:
#             # process the trigger: look trough maxAccPacket_list, find the maxacc
#             # for each location
#                 for maxAccJson in maxAccPacket_list:
#                     # while maxcc's starttime > trig starttime AND maxacc's endtime < trigs endtime create a new results json
#                     # this loop calls upon the keys of each individual json object as it loop through the big max acc packet list
#                     if maxAccJson["start_time"] > trig["startTime"] and maxAccJson["end_time"] < trig["endTime"]:
#                         FL_acc = []
#                         NL_acc = []
#                         # CT_acc = []
#                         NR_acc = []
#                         FR_acc = []
#                         if maxAccJson["station"] == "FL"
#                             FL_acc.append(maxAccJson["maxacc"])
#                         if maxAccJson["station"] == "NL"
#                             NL_acc.append(maxAccJson["maxacc"])
#                         # if maxAccJson["station"] == "CT"
#                         #     CT_acc.append(maxAccJson["maxacc"])
#                         if maxAccJson["station"] == "NR"
#                             NR_acc.append(maxAccJson["maxacc"])
#                         if maxAccJson["station"] == "FR"
#                             FR_acc.append(maxAccJson["maxacc"])
#
#                 # build a json with maxACC's for each station within time range of trigger
#                 # convert the start times and endtimes from datetime objects back into isoformat objects
#                 ResultsJson = {
#                     "trigger_startTime": trig["startTime"].isoformat(),
#                     "trigger_endTime": trig["endTime"].isoformat(),
#                     "peakACC_FL": max(FL_acc),
#                     "peakACC_NL": max(NL_acc),
#                     # "peakACC_CT": max(CT_acc),
#                     "peakACC_NR": max(NR_acc),
#                     "peakACC_FR": max(FR_acc)
#                 }
#             else:
#                 # keep looping...
#
#
#
#         if not trig.type == "PACKET":
#             # might get an OK very first after stream
#             print("parseResponse not a PACKET {} ".format(trig))
#         else:
#             print("Trigger: {}  {}".format(trig, json.dumps(json.loads(trig.data), indent=4)))
#
#     dali.close()
#
#
# loop = asyncio.get_event_loop()
# loop.set_debug(True)
# loop.run_until_complete(doTest(loop))
# loop.close()
