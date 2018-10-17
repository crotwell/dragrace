package org.crotwell.horseyTime.data;

import java.util.Date;


import com.rapplogic.xbee.api.XBeeResponse;

public class TimedData {

    public TimedData(XBeeResponse response, Date received) {
        super();
        this.xbeeResponse = response;
        this.received = received;
    }

    protected Date received;

    public Date getReceived() {
        return received;
    }

    XBeeResponse xbeeResponse;

    public TimedData() {
        super();
    }

}