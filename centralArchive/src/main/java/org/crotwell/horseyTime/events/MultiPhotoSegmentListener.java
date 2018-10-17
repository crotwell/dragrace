package org.crotwell.horseyTime.events;

import java.util.ArrayList;

import org.crotwell.horseyTime.data.PhotoBegin;
import org.crotwell.horseyTime.data.PhotoDone;
import org.crotwell.horseyTime.data.PhotoSegment;

public class MultiPhotoSegmentListener implements PhotoSegmentListener {

    public MultiPhotoSegmentListener() {}

    public MultiPhotoSegmentListener(PhotoSegmentListener listener) {
        listeners.add(listener);
    }

    public void addListener(PhotoSegmentListener listener) {
        listeners.add(listener);
    }

    public void photoBegin(PhotoBegin photoBegin) {
        for (PhotoSegmentListener listen : listeners) {
            listen.photoBegin(photoBegin);
        }
    }

    public void segmentReceived(PhotoSegment ps) {
        for (PhotoSegmentListener listen : listeners) {
            listen.segmentReceived(ps);
        }
    }

    public void photoEnd(PhotoDone photoDone) {
        for (PhotoSegmentListener listen : listeners) {
            listen.photoEnd(photoDone);
        }
    }

    ArrayList<PhotoSegmentListener> listeners = new ArrayList<PhotoSegmentListener>();
}
