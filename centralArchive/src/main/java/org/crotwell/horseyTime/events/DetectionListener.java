package org.crotwell.horseyTime.events;

import org.crotwell.horseyTime.data.Detection;


public interface DetectionListener {

    public void detected(Detection event);
}
