package org.crotwell.horseyTime;

import java.util.Date;

import com.rapplogic.xbee.api.XBeeResponse;


public class TimedMessage {
    
    private XBeeResponse msg;
    
    private Date receiveTime;

    
    public TimedMessage(XBeeResponse msg, Date receiveTime) {
        super();
        this.msg = msg;
        this.receiveTime = receiveTime;
    }


    public XBeeResponse getMsg() {
        return msg;
    }

    
    public Date getReceiveTime() {
        return receiveTime;
    }
}
