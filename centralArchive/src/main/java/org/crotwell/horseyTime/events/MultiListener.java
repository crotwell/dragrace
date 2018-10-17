package org.crotwell.horseyTime.events;

import java.util.ArrayList;

import org.crotwell.horseyTime.data.TimeSeriesPacket;


public class MultiListener implements TimeSeriesListener {

    public MultiListener() {}
    
    public MultiListener(TimeSeriesListener listener) {
        listeners.add(listener);
    }
    
    public void addListener(TimeSeriesListener listener) {
        listeners.add(listener);
    }

    public void timeSeries(TimeSeriesPacket event) {
        for (TimeSeriesListener listen : listeners) {
            listen.timeSeries(event);
        }
    }
    
    ArrayList<TimeSeriesListener> listeners = new ArrayList<TimeSeriesListener>();
    
}
