package org.crotwell.horseyTime.data;

import java.awt.Image;

import com.rapplogic.xbee.api.XBeeAddress16;

public class TimedPhoto {

    public TimedPhoto(XBeeAddress16 source, int timeId, Image photo) {
        super();
        this.source = source;
        this.timeId = timeId;
        this.photo = photo;
    }

    public XBeeAddress16 getSource() {
        return source;
    }

    public int getTimeId() {
        return timeId;
    }

    public Image getPhoto() {
        return photo;
    }

    @Override
    public String toString() {
        return source + " " + timeId;
    }

    XBeeAddress16 source;

    int timeId;

    Image photo;
}
