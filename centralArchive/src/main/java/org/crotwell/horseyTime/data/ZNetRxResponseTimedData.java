package org.crotwell.horseyTime.data;

import java.util.Date;

import com.rapplogic.xbee.api.XBeeAddress16;
import com.rapplogic.xbee.api.XBeeResponse;
import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;


public class ZNetRxResponseTimedData extends TimedData {

    public ZNetRxResponseTimedData(ZNetRxResponse response, Date received) {
        super(response, received);
    }

    public ZNetRxResponseTimedData() {
    }

    public ZNetRxResponse getXBeeResponse() {
        return (ZNetRxResponse)xbeeResponse;
    }

    public XBeeAddress16 getWho() {
        return getXBeeResponse().getRemoteAddress16();
    }
}
