package org.crotwell.horseyTime.gui;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;

import javax.imageio.ImageIO;

import org.apache.log4j.Logger;
import org.crotwell.horseyTime.data.PhotoBegin;
import org.crotwell.horseyTime.data.PhotoDone;
import org.crotwell.horseyTime.data.PhotoSegment;
import org.crotwell.horseyTime.data.TimedPhoto;
import org.crotwell.horseyTime.events.PhotoSegmentListener;
import org.crotwell.horseyTime.events.TimedPhotoListener;

import com.rapplogic.xbee.api.XBeeAddress16;

public class PhotoAssembler implements PhotoSegmentListener {

    public PhotoAssembler(TimedPhotoListener photoListener) {
        this.photoListener = photoListener;
    }

    public void photoBegin(PhotoBegin photoBegin) {
        begin.put(photoBegin.getXBeeResponse().getRemoteAddress16(), photoBegin);
    }

    public void segmentReceived(PhotoSegment ps) {
        if (!segments.containsKey(ps.getXBeeResponse().getRemoteAddress16())) {
            segments.put(ps.getXBeeResponse().getRemoteAddress16(), new ArrayList<PhotoSegment>());
        }
        segments.get(ps.getXBeeResponse().getRemoteAddress16()).add(ps);
    }

    public void photoEnd(PhotoDone photoDone) {
        List<PhotoSegment> pieces = segments.get(photoDone.getXBeeResponse().getRemoteAddress16());
        if (pieces.size() == photoDone.getNumSegments()) {
            // must have receive all segments
            Collections.sort(pieces, new Comparator<PhotoSegment>() {

                public int compare(PhotoSegment ps1, PhotoSegment ps2) {
                    if (ps1.getSequence() == ps2.getSequence()) {
                        return 0;
                    }
                    if (ps1.getSequence() < ps2.getSequence()) {
                        return -1;
                    }
                    return 1;
                }
            });
            byte[] jpegBytes = new byte[photoDone.getSize()];
            int position = 0;
            int segmentNumber = 0;
            for (PhotoSegment photoSegment : pieces) {
                if (photoSegment.getSequence() != segmentNumber) {
                    logger.warn("photo segment " + segmentNumber + " has seq number " + photoSegment.getSequence());
                }
                int thisSegment = Math.min(32, photoDone.getSize() - position);
                System.out.println(photoSegment.getPhotoData().length);
                System.out.println("System.arraycopy(photoSegment, 0, "+jpegBytes+", "+position+", "+thisSegment+");"+"  "+photoDone.getSize());
                System.arraycopy(photoSegment.getPhotoData(), 0, jpegBytes, position, thisSegment);
                position += thisSegment;
                segmentNumber++;
            }
            try {
                final BufferedImage bufferedImage = ImageIO.read(new ByteArrayInputStream(jpegBytes));
                TimedPhoto photo = new TimedPhoto(photoDone.getXBeeResponse().getRemoteAddress16(),
                                                  photoDone.getTimeId(),
                                                  bufferedImage);
                photoListener.photoReceived(photo);
            } catch(IOException e) {
                logger.error("unable to convert bytes to jpeg.", e);
            } finally {
                begin.remove(photoDone.getXBeeResponse().getRemoteAddress16());
                segments.remove(photoDone.getXBeeResponse().getRemoteAddress16());
            }
        } else {
            // hummm, maybe one is still in flight and will arrive out of order?
        }
    }

    TimedPhotoListener photoListener;

    HashMap<XBeeAddress16, List<PhotoSegment>> segments = new HashMap<XBeeAddress16, List<PhotoSegment>>();

    HashMap<XBeeAddress16, PhotoBegin> begin = new HashMap<XBeeAddress16, PhotoBegin>();

    private static final Logger logger = Logger.getLogger(PhotoAssembler.class);
}
