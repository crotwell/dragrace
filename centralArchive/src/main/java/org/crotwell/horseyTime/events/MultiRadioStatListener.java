package org.crotwell.horseyTime.events;

import java.util.ArrayList;
import java.util.List;

import org.crotwell.horseyTime.data.Heartbeat;

import com.rapplogic.xbee.api.zigbee.ZBNodeDiscover;


public class MultiRadioStatListener implements RadioStatListener {

    public void nodeIdentify(ZBNodeDiscover nodeId) {
        for (RadioStatListener rs : listenList) {
            rs.nodeIdentify(nodeId);
        }
    }
    
    public void addListener(RadioStatListener listener) {
        listenList.add(listener);
    }
    
    List<RadioStatListener> listenList = new ArrayList<RadioStatListener>();

    public void heartbeat(Heartbeat heartbeat) {
        for (RadioStatListener rs : listenList) {
            rs.heartbeat(heartbeat);
        }
    }
    
}
