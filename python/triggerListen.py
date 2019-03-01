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
    dali = simpleDali.DataLink(host, port)
    dali.verbose = True
    serverId = yield from dali.id(programname, username, processid, architecture)
    print("Resp: {}".format(serverId))
    serverInfo = yield from dali.info("STATUS")
    print("Info: {} ".format(serverInfo.message))
    #serverInfo = yield from dali.info("STREAMS")
    #print("Info: {} ".format(serverInfo.message))
    r = yield from dali.match(".*/MTRIG")
    print("match() Resonse {}".format(r))

    begintime = datetime.utcnow() - timedelta(minutes=5)
    r = yield from dali.positionAfter(begintime)
    print("positionAfter() Resonse {}".format(r))
    r = yield from dali.stream()
    while(keepGoing):
        trig = yield from dali.parseResponse()
        print("parseResponse {} ".format(trig.type))
        print("Trigger: {}  {}".format(trig, json.dumps(json.loads(trig.data), indent=4)))

    dali.close()


loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(doTest(loop))
loop.close()
