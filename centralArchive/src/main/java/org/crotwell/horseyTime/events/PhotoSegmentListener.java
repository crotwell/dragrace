package org.crotwell.horseyTime.events;

import org.crotwell.horseyTime.data.PhotoBegin;
import org.crotwell.horseyTime.data.PhotoDone;
import org.crotwell.horseyTime.data.PhotoSegment;


public interface PhotoSegmentListener {

    public void photoBegin(PhotoBegin photoBegin);
    
    public void segmentReceived(PhotoSegment photoSegment);
    
    public void photoEnd(PhotoDone photoDone);
}
