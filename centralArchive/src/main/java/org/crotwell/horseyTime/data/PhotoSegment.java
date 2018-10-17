package org.crotwell.horseyTime.data;

import java.util.Date;

import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;

public class PhotoSegment extends ZNetRxResponseTimedData {

    public PhotoSegment(ZNetRxResponse xbeeResp, Date received) {
        super(xbeeResp, received);
        int[] xbeeData = xbeeResp.getData();
        timeId = (xbeeData[1] << 24) + (xbeeData[2] << 16) + (xbeeData[3] << 8) + xbeeData[4];
        sequence = ((int)xbeeData[5]) << 8 + ((int)xbeeData[6]) & 0xff;
        photoData = new byte[datasize];
        for (int i = 0; i < photoData.length; i++) {
            photoData[i] = (byte)xbeeData[i+7];
        }
    }

    public byte[] getPhotoData() {
        return photoData;
    }

    public int getSequence() {
        return sequence;
    }

    byte[] photoData;

    int sequence;
    
    int timeId;
    
    int datasize = 32;
}
