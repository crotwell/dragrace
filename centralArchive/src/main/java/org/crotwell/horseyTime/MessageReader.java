package org.crotwell.horseyTime;

import java.util.Date;
import java.util.Queue;

import org.apache.log4j.Logger;

import com.rapplogic.xbee.api.ApiId;
import com.rapplogic.xbee.api.AtCommand;
import com.rapplogic.xbee.api.AtCommandResponse;
import com.rapplogic.xbee.api.PacketListener;
import com.rapplogic.xbee.api.XBee;
import com.rapplogic.xbee.api.XBeeResponse;
import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;
import com.rapplogic.xbee.util.ByteUtils;

public class MessageReader implements PacketListener {

    public MessageReader(Queue<TimedMessage> messageQueue) {
        this.messageQueue = messageQueue;
    }
     
    public void processResponse(XBeeResponse response) {
        Date arrivalTime = new Date();
        TimedMessage timeMsg = new TimedMessage(response, arrivalTime);
        synchronized(messageQueue) {
            messageQueue.offer(timeMsg);
            messageQueue.notify();
        }
        //log.info("Message received: "+response.toString());
    }

    Queue<TimedMessage> messageQueue;

    private static final Logger log = Logger.getLogger(MessageReader.class);
}
