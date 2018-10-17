package org.crotwell.horseyTime.events;

import org.crotwell.horseyTime.data.Heartbeat;

import com.rapplogic.xbee.api.zigbee.ZBNodeDiscover;


public interface RadioStatListener {
    
    public void nodeIdentify(ZBNodeDiscover nodeId);

    public void heartbeat(Heartbeat heartbeat);
    
}
