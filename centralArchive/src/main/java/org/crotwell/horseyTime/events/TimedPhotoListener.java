package org.crotwell.horseyTime.events;

import org.crotwell.horseyTime.data.TimedPhoto;

public interface TimedPhotoListener {

    public void photoReceived(TimedPhoto photo);
}
