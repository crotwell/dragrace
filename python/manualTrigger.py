import simpleDali
import simpleMiniseed
import asyncio
import json
import logging
from datetime import datetime, timedelta
from array import array

logging.basicConfig(level=logging.DEBUG)

host = "129.252.35.36"
port = 15003
#host = "127.0.0.1"
#host = "129.252.35.20"
#port = 6382
uri = "ws://www.seis.sc.edu/dragracews/datalink"

programname="simpleDali"
username="dragrace"
processid=0
architecture="python"


async def doTest(loop):
    dali = simpleDali.SocketDataLink(host, port)
    #dali = simpleDali.WebSocketDataLink(uri)
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
    dutyOfficer="Philip"
    trigtime = datetime.utcnow()

    streamid = "{}.{}.{}.{}/MTRIG".format(network, station, location, channel)
    hpdatastart = int(trigtime.timestamp() * simpleDali.MICROS)
    hpdataend = int(trigtime.timestamp() * simpleDali.MICROS)
    trigInfo= {
        "type": "manual",
        "dutyOfficer": dutyOfficer,
        "time": trigtime.isoformat(),
        "creation": trigtime.isoformat(),
        "override": {
            "modtime": trigtime.isoformat(),
            "value": "enable"
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
