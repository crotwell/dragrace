package org.crotwell.horseyTime;

import java.io.BufferedInputStream;
import java.io.EOFException;
import java.io.IOException;
import java.net.URL;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.Queue;

import org.apache.log4j.Logger;

import com.rapplogic.xbee.XBeeConnection;
import com.rapplogic.xbee.api.ApiId;
import com.rapplogic.xbee.api.AtCommand;
import com.rapplogic.xbee.api.AtCommandResponse;
import com.rapplogic.xbee.api.AtCommandResponse.Status;
import com.rapplogic.xbee.api.CollectTerminator;
import com.rapplogic.xbee.api.PacketListener;
import com.rapplogic.xbee.api.XBee;
import com.rapplogic.xbee.api.XBeeAddress16;
import com.rapplogic.xbee.api.XBeeAddress64;
import com.rapplogic.xbee.api.XBeeConfiguration;
import com.rapplogic.xbee.api.XBeeException;
import com.rapplogic.xbee.api.XBeePacket;
import com.rapplogic.xbee.api.XBeeRequest;
import com.rapplogic.xbee.api.XBeeResponse;
import com.rapplogic.xbee.api.XBeeTimeoutException;
import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;

import edu.sc.seis.seisFile.mseed.Btime;


public class MockXBee extends XBee {
    
    public MockXBee(){
        createHeartbeat();
        createInfo("Howdy, just starting up");
        cretaeMMA8451Packet();
        Runnable packetFaker = new Runnable() {

            public void run() {
                while(true) {
                    if (connected) {
                        sendPacket();
                    }
                }
            }
            
        };
        Thread t = new Thread(packetFaker);
        t.setDaemon(true);
        t.start();
    }

    public MockXBee(XBeeConfiguration conf) {
        this();
    }
    
    @Override
    public void open(String port, int baudRate) throws XBeeException {
        connected = true;
    }

    @Override
    public void initProviderConnection(XBeeConnection connection) throws XBeeException {
    }

    @Override
    public void addPacketListener(PacketListener packetListener) {
        packetListenerList.add(packetListener);
    }

    @Override
    public void removePacketListener(PacketListener packetListener) {
        packetListenerList.remove(packetListener);
    }

    @Override
    public void sendRequest(XBeeRequest request) throws IOException {
    }

    @Override
    public void sendPacket(XBeePacket packet) throws IOException {
    }

    @Override
    public void sendPacket(int[] packet) throws IOException {
    }

    @Override
    public void sendAsynchronous(XBeeRequest request) throws XBeeException {
        if (request instanceof AtCommand) {
            AtCommand at = (AtCommand)request;
            if (at.getCommand().equals("ND")) {
                AtCommandResponse cmdResp = new AtCommandResponse();
                cmdResp.setApiId(ApiId.AT_RESPONSE);
                cmdResp.setChar1('N');
                cmdResp.setChar2('D');
                cmdResp.setStatus(Status.OK);
                String nodeId = "Test Node 1";
                int[] data = new int[2+8+nodeId.length()+1+2+1+1+2+2];
                int index = 0;
                // 2 ints for 16 addr, 8 for 64 addr
                for (int i = 0; i < 10; i++) {
                    data[index++] = i;
                }
                for (int i=0; i< nodeId.length(); i++) {
                    data[index++] = nodeId.charAt(i);
                }
                data[index++] = 0;
                // parent 16
                data[index++] = 2;
                data[index++] = 1;
                //device type
                data[index++] = 1;
                // status
                data[index++] = 1;
                // profile id
                data[index++] = 6;
                data[index++] = 5;
                // MfgId
                data[index++] = 4;
                data[index++] = 3;
                
                cmdResp.setValue(data);
                addPacketToQueue(cmdResp);
            }
        }
    }

    @Override
    public AtCommandResponse sendAtCommand(AtCommand command) throws XBeeException {
        return null;
    }

    @Override
    public XBeeResponse sendSynchronous(XBeeRequest xbeeRequest, int timeout) throws XBeeTimeoutException,
            XBeeException {
        return null;
    }

    @Override
    public XBeeResponse sendSynchronous(XBeeRequest request) throws XBeeTimeoutException, XBeeException {
        return null;
    }

    @Override
    public XBeeResponse getResponse() throws XBeeException {
        return null;
    }

    @Override
    public XBeeResponse getResponse(int timeout) throws XBeeException, XBeeTimeoutException {
        yodaSleep(timeout);
        return getResponse();
    }

    @Override
    public List<? extends XBeeResponse> collectResponses(int wait, CollectTerminator terminator) throws XBeeException {
        return collectResponses(wait);
    }

    @Override
    public List<? extends XBeeResponse> collectResponses(int wait) throws XBeeException {
        yodaSleep(wait);
        return new ArrayList<XBeeResponse>();
    }

    @Override
    public int getResponseQueueSize() {
        return 0;
    }

    @Override
    public void close() {
        connected = false;
    }

    @Override
    public boolean isConnected() {
        return connected;
    }

    @Override
    public int getCurrentFrameId() {
        return frameId;
    }

    @Override
    public int getNextFrameId() {
        return frameId+1;
    }

    @Override
    public void updateFrameId(int val) {
        this.frameId = val;
    }

    @Override
    public void clearResponseQueue() {
    }
    
    synchronized void addPacketToQueue(XBeeResponse resp) {
        packetQueue.offer(resp);
    }

    void pushPacket(XBeeResponse response) {
        for (PacketListener packetListener : packetListenerList) {
            packetListener.processResponse(response);
        }
    }
    
    synchronized void sendPacket() {
        yodaSleep(2);
        if ( ! packetQueue.isEmpty()) {
            pushPacket(packetQueue.poll());
        } else {
            createRandomPacket(); // adds to queue
        }
    }

    void createRandomPacket() {

        int[] packetData;
        yodaSleep(2);
        System.out.println("createRandomPacket");
        int millis = (int)System.currentTimeMillis();
        cretaeMMA8451Packet();
        int val = Math.round((float)Math.random()*PACKET_TYPE_RANGE);
//        switch(val) {
//            case 0: // detect
//                cretaeMMA8451Packet();
//                break;
//            default: // heartbeat
//                createHeartbeat();
//                break;
//        }
    }

    XBeeResponse createRandomPacket(int[] packetData) {
        ZNetRxResponse resp = new ZNetRxResponse();
        resp.setApiId(ApiId.ZNET_RX_RESPONSE);
        resp.setData(packetData);
        resp.setRemoteAddress16(new XBeeAddress16(12, 34));
        resp.setRemoteAddress64(new XBeeAddress64(12, 34, 56, 78, 90, 12, 34, 56));
        return resp;
    }
    
    void cretaeMMA8451Packet() {
        int numSamples = 30;
        int dataSectionLength = 3*2*30;
        int[] dataPacket = new int[11+dataSectionLength];
        dataPacket[0] = 'A';
        Instant now = Instant.now();

            ZonedDateTime zdt = ZonedDateTime.ofInstant(now, ZoneId.of("UTC"));
            Btime btime = new Btime();
            int milli = zdt.getNano()/1000000;
            btime.year = zdt.getYear();
            btime.jday = zdt.getDayOfYear();
            btime.hour = zdt.getHour();
            btime.min = zdt.getMinute();
            btime.sec = zdt.getSecond();
            dataPacket[1] = 30;
            dataPacket[2] = (btime.year & 0xff00) >> 8;
                
                dataPacket[3] = (btime.year & 0xff);
                dataPacket[4] = (btime.getDayOfYear() >> 8 ) & 0xff;
                dataPacket[5] = (btime.getDayOfYear() & 0xff);
                dataPacket[6] = btime.hour;
                dataPacket[7] = btime.min;
                dataPacket[8] = btime.sec;
                dataPacket[9] = (milli  >> 8 ) & 0xff;
                dataPacket[10] = (milli & 0xff);
                dataPacket[11] = 50;
                System.out.println("MockXBee cretaeMMA8451Packet "+milli+"  "+dataPacket[9]+"  "+dataPacket[10]+"  sps"+dataPacket[11]);
                for (int i = 11; i < numSamples; i++) {
                    dataPacket[11+i*6] = 1;
                    dataPacket[11+i*6+1] = 1;
                    dataPacket[11+i*6+2] = 1;
                    dataPacket[11+i*6+3] = 1;
                    dataPacket[11+i*6+4] = 1;
                    dataPacket[11+i*6+5] = 1;
                }
                addPacketToQueue(createRandomPacket(dataPacket));
    }
    
    void cretaeDetectWithPicture() {
        System.out.println("cretaeDetectWithPicture");
        // detect
        int[] packetData = new int[6];
        int millis = (int)System.currentTimeMillis();
        packetData[0] = MessageProcessor.DETECT_PACKET;
        packetData[1] = 47;
        packetData[2] = (millis >> 24) & 0xff;
        packetData[3] = (millis >> 16) & 0xff;
        packetData[4] = (millis >> 8) & 0xff;
        packetData[5] = (millis) & 0xff;
        addPacketToQueue(createRandomPacket(packetData));
        packetData = new int[5];
        packetData[0] = MessageProcessor.PHOTO_BEGIN;
        packetData[1] = (millis >> 24) & 0xff;
        packetData[2] = (millis >> 16) & 0xff;
        packetData[3] = (millis >> 8) & 0xff;
        packetData[4] = (millis) & 0xff;
        addPacketToQueue(createRandomPacket(packetData));
        try {
            BufferedInputStream bis = new BufferedInputStream(this.getClass().getClassLoader()
                    .getResourceAsStream("org/crotwell/horseyTime/data/mockPicture.jpeg"));
            packetData = new int[35];
            packetData[0] = MessageProcessor.PHOTO_PACKET;
            int seq = 0;
            int i = 0;
            int next;
            try {
                System.out.println("Before while");
            while ((next = bis.read()) != -1) {
                packetData[i%32 + 3] = next;
                if (i % 32 == 31) {
                    addPacketToQueue(createRandomPacket(packetData));
                    System.out.println("Packet added to queue: "+seq);
                    seq++;
                    packetData = new int[39];
                    packetData[0] = MessageProcessor.PHOTO_PACKET;
                    packetData[1] = (seq >> 8) & 0xff;
                    packetData[2] = (seq & 0xff);
                }
                i++;
            }
            } catch (EOFException ee) {}
            System.out.println("read done");
            yodaSleep(2);
            if (i % 32 != 0) {
                // one last one to send
                addPacketToQueue(createRandomPacket(packetData));
                seq++;
            }
            packetData = new int[11];
            packetData[0] = MessageProcessor.PHOTO_END;
            packetData[1] = (millis >> 24) & 0xff;
            packetData[2] = (millis >> 16) & 0xff;
            packetData[3] = (millis >> 8) & 0xff;
            packetData[4] = (millis) & 0xff;
            packetData[5] = (seq >> 8) & 0xff;
            packetData[6] = (seq) & 0xff;
            packetData[7] = (i >> 24) & 0xff;
            packetData[8] = (i >> 16) & 0xff;
            packetData[9] = (i >> 8) & 0xff;
            packetData[10] = (i) & 0xff;
            addPacketToQueue(createRandomPacket(packetData));
            createHeartbeat();
        } catch(IOException e) {
            logger.error("Unable to load fake picture", e);
        }
    }
    
    void createHeartbeat() {
        int[] packetData  = new int[5];
        packetData[0] = MessageProcessor.HEARTBEAT_PACKET;
        int millis = (int)System.currentTimeMillis();
        packetData[1] = (millis >> 24) & 0xff;
        packetData[2] = (millis >> 16) & 0xff;
        packetData[3] = (millis >>  8) & 0xff;
        packetData[4] = (millis      ) & 0xff;
        addPacketToQueue(createRandomPacket(packetData));
    }
    
    void createInfo(String s) {
        int[] packetData = initPacketWithTime(MessageProcessor.INFO_PACKET);
        byte[] msgBytes = s.getBytes();
        for (int i = 0; i < msgBytes.length && i < 63; i++) {
            packetData[i+5] = msgBytes[i];
        }
        addPacketToQueue(createRandomPacket(packetData));
    }

    int[] initPacketWithTime(int type) {
        return initPacketWithTime(type, (int)System.currentTimeMillis());
    }
    
    int[] initPacketWithTime(int type, int millis) {
        int[] packetData = new int[64+5];
        packetData[0] = type;
        packetData[1] = (millis >> 24) & 0xff;
        packetData[2] = (millis >> 16) & 0xff;
        packetData[3] = (millis >>  8) & 0xff;
        packetData[4] = (millis      ) & 0xff;
        return packetData;
    }
    
    /** do or not do, there is no try...*/
    void yodaSleep(int seconds) {
        try {
            Thread.sleep(seconds*1000);
        } catch(InterruptedException e) {}
    }
    
    static final int PACKET_TYPE_RANGE = 3;
    
    Queue<XBeeResponse> packetQueue = new LinkedList<XBeeResponse>();
    
    List<PacketListener> packetListenerList = new ArrayList<PacketListener>();
    
    int frameId = 0;
    
    boolean connected = false;

    private static final Logger logger = Logger.getLogger(MockXBee.class);
}
