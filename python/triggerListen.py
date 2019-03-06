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
    serverId = await dali.id(programname, username, processid, architecture)
    print("Resp: {}".format(serverId))
    serverInfo = await dali.info("STATUS")
    print("Info: {} ".format(serverInfo.message))
    #serverInfo = yield from dali.info("STREAMS")
    #print("Info: {} ".format(serverInfo.message))
    r = await dali.match(".*/MTRIG")
    print("match() Resonse {}".format(r))

    begintime = datetime.utcnow() - timedelta(minutes=5)
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
