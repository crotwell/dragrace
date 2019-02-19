import simpleDali
import simpleMiniseed
import asyncio
import json
import logging
from datetime import datetime, timedelta
from array import array

logging.basicConfig(level=logging.DEBUG)

host = "129.252.35.36"
host = "127.0.0.1"
port = 15003
#host = "129.252.35.20"
#port = 6383
programname="simpleDali"
username="dragrace"
processid=0
architecture="python"


@asyncio.coroutine
def doTest(loop):
    dali = simpleDali.DataLink(host, port)
    serverId = yield from dali.id(programname, username, processid, architecture)
    print("Resp: {}".format(serverId))
    #serverInfo = yield from dali.info("STATUS")
    #print("Info: {} ".format(serverInfo.message))
    #serverInfo = yield from dali.info("STREAMS")
    #print("Info: {} ".format(serverInfo.message))
    network = "YY"
    station = "TEST"
    location = "00"
    channel = "HNZ"
    trigtime = datetime.utcnow()

    streamid = "{}.{}.{}.{}/MTRIG".format(network, station, location, channel)
    hpdatastart = int(trigtime.timestamp() * simpleDali.MICROS)
    hpdataend = int(trigtime.timestamp() * simpleDali.MICROS)
    trigInfo= {
        "network": network,
        "station": station,
        "location": location,
        "channel": channel,
        "triggers": [
            {
                "type": "manual",
                "dutyOfficer": "Kevin",
                "time": trigtime.isoformat()
            },
            {
                "type": "manual",
                "dutyOfficer": "Gabby",
                "time": trigtime.isoformat()
            },
            {
                "type": "automated",
                "time": trigtime.isoformat()
            }
        ],
        "creation": trigtime.isoformat(),
        "override": {
            "modtime": trigtime.isoformat(),
            "value": "disable"
        }
    }
    trigBytes = json.dumps(trigInfo).encode('UTF-8')
    r = yield from dali.writeAck(streamid, hpdatastart, hpdataend, trigBytes)
    print("writem trigger resp {}".format(r));
    dali.close()


loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(doTest(loop))
loop.close()
