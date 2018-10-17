package org.crotwell.horseyTime.data;

import java.util.Date;

import com.rapplogic.xbee.api.XBeeAddress16;
import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;


public class TimeSync extends ZNetRxResponseTimedData {
    

    public TimeSync(ZNetRxResponse xbeeResp, Date received) {
        super(xbeeResp, received);
        int[] data = xbeeResp.getData();
         millis = data[1] << 24 +
                     data[2] << 16 +
                     data[3] << 8  +
                     data[4];
    }
    
    
    public int getMillis() {
        return millis;
    }

    int millis;
}
