package org.crotwell.horseyTime.data;

import java.util.Date;

import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;

public class PhotoBegin extends ZNetRxResponseTimedData {

    public PhotoBegin(ZNetRxResponse xbeeResp, Date received) {
        super(xbeeResp, received);
        int[] data = xbeeResp.getData();
        timeId = (data[1] << 24) + (data[2] << 16) + (data[3] << 8) + data[4];
    }

    public PhotoBegin() {
        // TODO Auto-generated constructor stub
    }

    public int getTimeId() {
        return timeId;
    }

    int timeId;
}
