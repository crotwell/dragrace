package org.crotwell.horseyTime.events;

import java.util.ArrayList;

import org.crotwell.horseyTime.data.TimedPhoto;


public class MultiTimedPhotoListener implements TimedPhotoListener {

    public MultiTimedPhotoListener(TimedPhotoListener listener) {
        listeners.add(listener);
    }
    
    public void addListener(TimedPhotoListener listener) {
        listeners.add(listener);
    }

    public void photoReceived(TimedPhoto photo) {
        for (TimedPhotoListener listen : listeners) {
            listen.photoReceived(photo);
        }
    }
    
    ArrayList<TimedPhotoListener> listeners = new ArrayList<TimedPhotoListener>();
}
