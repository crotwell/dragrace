package org.crotwell.horseyTime.events;

import org.crotwell.horseyTime.data.TimeSeriesPacket;

public interface TimeSeriesListener {

    public void timeSeries(TimeSeriesPacket tsp);
}
