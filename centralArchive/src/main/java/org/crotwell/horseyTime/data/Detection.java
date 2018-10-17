package org.crotwell.horseyTime.data;

import java.util.Date;

import org.apache.log4j.Logger;

import com.rapplogic.xbee.api.XBeeAddress16;
import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;

public class Detection extends ZNetRxResponseTimedData {

    public Detection(ZNetRxResponse xbeeResp, Date received) {
        super(xbeeResp, received);
        int[] data = xbeeResp.getData();
        inches = data[1];
        remoteWhen = (data[2] << 24) + (data[3] << 16) + (data[4] << 8) + data[5];
        log.info("Detect: " + inches + " at " + remoteWhen + " " + data[2] + " " + data[3] + " " + data[4] + " "
                + data[5]);
    }

    public int getInches() {
        return inches;
    }

    public int getWhoInt() {
        return getWho().get16BitValue();
    }

    public int getRemoteWhen() {
        return remoteWhen;
    }

    protected int remoteWhen;

    int inches;

    private static final Logger log = Logger.getLogger(Detection.class);
}
