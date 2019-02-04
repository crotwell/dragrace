import simpleDali
import simpleMiniseed
import asyncio
import logging
from datetime import datetime, timedelta
from array import array

logging.basicConfig(level=logging.DEBUG)

host = "129.252.35.36"
port = 15003
#host = "129.252.35.20"
#port = 6383
programname="simpleDali"
username="dragrace"
processid=0
architecture="python"

programname="s"
username="d"
processid=0
architecture="p"

@asyncio.coroutine
def doTest(loop):
    dali = simpleDali.DataLink(host, port)
    serverId = yield from dali.id(programname, username, processid, architecture)
    print("Resp: {}".format(serverId.toString()))
    serverInfo = yield from dali.info("STATUS")
    print("Info: {} ".format(serverInfo.message))
    serverInfo = yield from dali.info("STREAMS")
    print("Info: {} ".format(serverInfo.message))
    network = "YY"
    station = "TEST"
    location = "00"
    channel = "HNZ"
    starttime = datetime.utcnow()
    numsamples = 100
    samprate=200
    shortData = array("h") # shorts
    for i in range(numsamples):
        shortData.append(i)
    msh = simpleMiniseed.MiniseedHeader(network, station, location, channel, starttime, numsamples, samprate)
    msr = simpleMiniseed.MiniseedRecord(msh, shortData)
    #dali.write()
    dali.close()


loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(doTest(loop))
loop.close()
