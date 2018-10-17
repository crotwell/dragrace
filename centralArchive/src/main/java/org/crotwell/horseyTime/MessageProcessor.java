package org.crotwell.horseyTime;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Queue;

import org.apache.log4j.Logger;
import org.crotwell.horseyTime.data.Detection;
import org.crotwell.horseyTime.data.Heartbeat;
import org.crotwell.horseyTime.data.InfoMessage;
import org.crotwell.horseyTime.data.PhotoBegin;
import org.crotwell.horseyTime.data.PhotoDone;
import org.crotwell.horseyTime.data.PhotoSegment;
import org.crotwell.horseyTime.data.TimeSync;
import org.crotwell.horseyTime.data.TimeSeriesPacket;
import org.crotwell.horseyTime.events.DetectionListener;
import org.crotwell.horseyTime.events.InfoListener;
import org.crotwell.horseyTime.events.MultiListener;
import org.crotwell.horseyTime.events.MultiPhotoSegmentListener;
import org.crotwell.horseyTime.events.MultiRadioStatListener;
import org.crotwell.horseyTime.events.PhotoSegmentListener;
import org.crotwell.horseyTime.events.RadioStatListener;
import org.crotwell.horseyTime.events.TimeSeriesListener;

import com.rapplogic.xbee.api.ApiId;
import com.rapplogic.xbee.api.AtCommand;
import com.rapplogic.xbee.api.AtCommandResponse;
import com.rapplogic.xbee.api.PacketParser;
import com.rapplogic.xbee.api.XBee;
import com.rapplogic.xbee.api.XBeeAddress64;
import com.rapplogic.xbee.api.XBeeException;
import com.rapplogic.xbee.api.XBeeRequest;
import com.rapplogic.xbee.api.zigbee.ZBNodeDiscover;
import com.rapplogic.xbee.api.XBeeResponse;
import com.rapplogic.xbee.api.zigbee.ZNetNodeIdentificationResponse;
import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;
import com.rapplogic.xbee.api.zigbee.ZNetTxRequest;
import com.rapplogic.xbee.util.ByteUtils;


public class MessageProcessor implements Runnable {

    public MessageProcessor(Queue<TimedMessage> messageQueue, Map<String, String> stationCodeMap) {
        this.messageQueue = messageQueue;
        this.stationCodeMap = stationCodeMap;
    }
    
    
    
    public void run() {
        TimedMessage timeMsg;
        int index = 0;
        while(true) {
            synchronized(messageQueue) {
                while(messageQueue.isEmpty()) {
                    try {
                        messageQueue.wait();
                    } catch(InterruptedException e) {
                    }
                }
                timeMsg = messageQueue.remove();
            }
            if (timeMsg.getMsg() != null) {
                try {
                    handleMessage(timeMsg);
                } catch(RuntimeException e) {
                    logger.error("Problem processing message at: "+timeMsg.getReceiveTime(), e);
                }
                index++;
                if (index % 10 == 0 && messageQueue.size() > 1) {
                    logger.info("Message Queue size="+messageQueue.size());
                }
            }
        }
    }
    
    void handleMessage(TimedMessage timeMsg) {
        XBeeResponse msg = timeMsg.getMsg();
        //log.info("received response " + msg.toString());
        if (msg.getApiId() == ApiId.ZNET_RX_RESPONSE) {
            ZNetRxResponse rx = (ZNetRxResponse)msg;
            if (false) logger.info("Received RX packet, option is " + rx.getOption() + ", sender 64 address is "
                     + ByteUtils.toBase16(rx.getRemoteAddress64().getAddress())
                     + ", remote 16-bit address is "
                     + ByteUtils.toBase16(rx.getRemoteAddress16().getAddress()) + ", data is "
                     + ByteUtils.toBase16(rx.getData()));
            int[] data = rx.getData();
            switch(data[0]) {
                case HEARTBEAT_PACKET: // heartbeat
                    radioStatListener.heartbeat(new Heartbeat(rx, timeMsg.getReceiveTime()));
                    break;
                case DETECT_PACKET: // detect
                    //detectTable.detected(new Detection(rx, timeMsg.getReceiveTime()));
                    break;
                case TIME_PACKET: // time sync response
                    TimeSync tSync = new TimeSync(rx, timeMsg.getReceiveTime());

                case TIME_SERIES_PACKET: // timeseries packet
                    String staCode = stationCodeMap.get(rx.getRemoteAddress64().toString());
                    if (staCode == null) {
                        staCode = "UNKNW";
                        try {
                            logger.info("send ND");
                            xbee.sendAsynchronous(new AtCommand("ND"));
                        } catch (XBeeException e) {
                            logger.warn("unable to send NI command");
                        }
                    }
                    TimeSeriesPacket tsp = new TimeSeriesPacket(rx, timeMsg.getReceiveTime(), staCode);
                    timeSeriesTable.timeSeries(tsp);
                    break;
                case PHOTO_BEGIN: // photo begin
                    photoListener.photoBegin(new PhotoBegin(rx, timeMsg.getReceiveTime()));
                    break;
                case PHOTO_END: // photo done
                    photoListener.photoEnd(new PhotoDone(rx, timeMsg.getReceiveTime()));
                    break;
                case PHOTO_PACKET: // photo segment
                    photoListener.segmentReceived(new PhotoSegment(rx, timeMsg.getReceiveTime()));
                    break;
                case INFO_PACKET: // info/debugging
                    infoListener.infoMessageReceived(new InfoMessage(rx, timeMsg.getReceiveTime()));
                    break;
                default:
                    logger.info("Unknown packet: "+ByteUtils.toBase16(data));
                    String message = "";
                    for (int i = 0; i < data.length; i++) {
                        if (data[i] > 31 && data[i] < 127) {
                            message += Character.toString((char)data[i]);
                        } else {
                            message += ".";
                        }
                    }
                    logger.info("Unknown packet: "+message);
            }
        } else if (msg.getApiId() == ApiId.AT_RESPONSE) {
            PacketParser parser;
            //log.info("got a AT response packet: "+msg.toString());
            AtCommandResponse cmdResp = (AtCommandResponse)msg;
            if (cmdResp.getCommand().equals("ND")) {
                logger.info("got a ND packet");
                ZBNodeDiscover nd = ZBNodeDiscover.parse((AtCommandResponse)cmdResp);
                radioStatListener.nodeIdentify(nd);
            } else if (cmdResp.getCommand().equals("MY")) {
                logger.info("got a MY packet");
                ZNetNodeIdentificationResponse zid;
                ZBNodeDiscover nd = ZBNodeDiscover.parse((AtCommandResponse)cmdResp);
                radioStatListener.nodeIdentify(nd);
            }
        } else {
            logger.info("received unexpected packet " + msg.getApiId()+"  " + msg.toString());
        }
    }

    public void addPhotoSegmentListener(PhotoSegmentListener listen) {
        this.photoListener.addListener( listen);
    }

    
    public void addRadioStatListener(RadioStatListener listen) {
        this.radioStatListener.addListener( listen);
    }
    
    public void addTimeSeriesListener(TimeSeriesListener listener) {
        timeSeriesTable.addListener(listener);
        
    }

    MultiListener timeSeriesTable = new MultiListener();
    
    MultiRadioStatListener radioStatListener = new MultiRadioStatListener();
    
    MultiPhotoSegmentListener photoListener = new MultiPhotoSegmentListener();
    
    InfoListener infoListener = new InfoListener() {

        public void infoMessageReceived(InfoMessage message) {
            System.out.println("Info: "+message.getInfo());
            logger.info(message.getWho()+" "+message.getRemoteWhen()+" "+message.getInfo());
        }
        
    };
    
    List<XBeeAddress64> knownRadios = new ArrayList<XBeeAddress64>();

    Map<String, String> stationCodeMap;
    
    Queue<TimedMessage> messageQueue;
    
    XBee xbee;
    
public static final int HEARTBEAT_PACKET = 'H';
public static final int DETECT_PACKET = 'D';
public static final int TIME_PACKET = 'T';
public static final int PHOTO_BEGIN = 'B';
public static final int PHOTO_END = 'E';
public static final int PHOTO_PACKET = 'P';
public static final int INFO_PACKET = 'I';
public static final int TIME_SERIES_PACKET = 'A';
    
    private static final Logger logger = Logger.getLogger(MessageProcessor.class);

    public void setXBee(XBee xbee) {
        this.xbee = xbee;
        
    }
}
