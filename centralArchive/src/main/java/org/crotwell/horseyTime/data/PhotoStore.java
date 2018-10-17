package org.crotwell.horseyTime.data;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.crotwell.horseyTime.events.TimedPhotoListener;

import com.rapplogic.xbee.api.XBeeAddress16;

public class PhotoStore implements TimedPhotoListener {

    public void photoReceived(TimedPhoto photo) {
        store(photo);
    }

    public void store(TimedPhoto photo) {
        if (!photos.containsKey(photo.getSource())) {
            photos.put(photo.getSource(), new ArrayList<TimedPhoto>());
        }
        photos.get(photo.getSource()).add(photo);
    }

    HashMap<XBeeAddress16, List<TimedPhoto>> photos = new HashMap<XBeeAddress16, List<TimedPhoto>>();
}
