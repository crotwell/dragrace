package org.crotwell.horseyTime.data;

import java.util.Date;

import org.apache.log4j.Logger;

import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;


public class Heartbeat  extends ZNetRxResponseTimedData  {
    
    public Heartbeat(ZNetRxResponse xbeeResp, Date received) {
        super(xbeeResp, received);
        int[] data = xbeeResp.getData();
        time = (data[1] << 24) +
               (data[2] << 16) +
               (data[3] << 8)  +
               data[4];
        log.info("Heartbeat: "+time);
    }
    
    public int getTime() {
        return time;
    }

    int time;


    private static final Logger log = Logger.getLogger(Heartbeat.class);
}
