package org.crotwell.horseyTime.data;

import java.util.Date;

import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;

public class PhotoDone extends ZNetRxResponseTimedData {

    public PhotoDone(ZNetRxResponse xbeeResp, Date received) {
        super(xbeeResp, received);
        int[] data = xbeeResp.getData();
        timeId = (data[1] << 24) + (data[2] << 16) + (data[3] << 8) + data[4];
        numSegments = data[5] << 8 + data[6];
        size = (data[7] << 24) + (data[8] << 16) + (data[9] << 8) + data[10];
    }

    public int getNumSegments() {
        return numSegments;
    }

    public int getTimeId() {
        return timeId;
    }

    public int getSize() {
        return size;
    }

    int numSegments;

    int timeId;

    int size;
}
