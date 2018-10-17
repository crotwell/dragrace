package org.crotwell.horseyTime.events;

import org.crotwell.horseyTime.data.InfoMessage;


public interface InfoListener {
    
    public void infoMessageReceived(InfoMessage message);
    
}
