package org.crotwell.horseyTime;

import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.Map;
import java.util.Properties;
import java.util.Queue;
import java.util.Set;

import javax.swing.ImageIcon;

import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Logger;
import org.apache.log4j.PropertyConfigurator;
import org.crotwell.horseyTime.data.DataStore;
import org.crotwell.horseyTime.data.Heartbeat;
import org.crotwell.horseyTime.data.InfoMessage;
import org.crotwell.horseyTime.data.PhotoStore;
import org.crotwell.horseyTime.data.TimedPhoto;
import org.crotwell.horseyTime.events.InfoListener;
import org.crotwell.horseyTime.events.MiniseedGenerator;
import org.crotwell.horseyTime.events.MultiListener;
import org.crotwell.horseyTime.events.MultiTimedPhotoListener;
import org.crotwell.horseyTime.events.RadioStatListener;
import org.crotwell.horseyTime.events.TimedPhotoListener;
import org.crotwell.horseyTime.gui.GUI;
import org.crotwell.horseyTime.gui.HeartbeatModel;
import org.crotwell.horseyTime.gui.KnownRadiosTableModel;
import org.crotwell.horseyTime.gui.PhotoAssembler;
import org.crotwell.horseyTime.gui.SerialPortChooser;
import org.crotwell.horseyTime.gui.TimeSeriesTableModel;

import com.rapplogic.xbee.api.AtCommand;
import com.rapplogic.xbee.api.RemoteAtRequest;
import com.rapplogic.xbee.api.XBee;
import com.rapplogic.xbee.api.XBeeAddress64;
import com.rapplogic.xbee.api.XBeeException;
import com.rapplogic.xbee.api.XBeeResponse;
import com.rapplogic.xbee.api.XBeeTimeoutException;
import com.rapplogic.xbee.api.zigbee.ZBNodeDiscover;
import com.rapplogic.xbee.api.zigbee.ZNetTxRequest;
import com.rapplogic.xbee.api.zigbee.ZNetTxStatusResponse;
import com.rapplogic.xbee.util.ByteUtils;

// controller: XBeeAddress64(0x0013a200, 0x40764575)
//
//
// router: XBeeAddress64(0x0013a200, 0x40764567)
// /dev/tty.usbserial-A700fpNT
//
//
// must download drivers from http://www.ftdichip.com/Drivers/VCP.htm
//
// rxtx  http://rxtx.qbang.org/wiki/index.php/Download
// rxtx seemed to stop working with update to mac, switch to
// http://nrjavaserial.googlecode.com

public class HorseyTime {
    
    public static boolean isMockXbee = false;
    
    public Map<String, String> stationCodeMap = new HashMap<String, String>();
    
    public HorseyTime(String[] args) throws XBeeException, IOException {
        loadPropsConfigLogging();
        
        
        msgReader = new MessageReader(messageQueue);
        
        processor = new MessageProcessor(messageQueue, stationCodeMap);
        Thread t = new Thread(processor, "MessageProcessor");
        t.setDaemon(true);
        t.start();
        
        if (args.length > 0 && args[0] == "--gui") {
            port = findSerialPort();
            doInitGui();
        } else {
            MiniseedGenerator mseedGenerator = new MiniseedGenerator(stationCodeMap);
            processor.addTimeSeriesListener(mseedGenerator);
            closeXBee();
            setMockXBee(isMockXbee);
            port = findSerialPort();
            if (port == null) {
                logger.fatal("###############################");
                logger.fatal("Can't find serial port for xbee");
                logger.fatal("###############################");
                System.exit(1);
            }
            XBee xbee = getXBee();
            processor.setXBee(xbee);
            logger.info("XBee init at "+getPort()+" "+getBaud()+" "+xbee.getResponseQueueSize());
        }
        logger.info("Ready for remote packets");
    }
    
    public static void loadPropsConfigLogging() throws IOException {
        BasicConfigurator.configure();
        Properties props = new Properties();
        props.load((HorseyTime.class).getClassLoader().getResourceAsStream(DEFAULT_PROPS));
        PropertyConfigurator.configure(props);
    }
    
    void simpleTests() throws XBeeTimeoutException, XBeeException {
        XBeeAddress64 remote64 = new XBeeAddress64("00 13 a2 00 40 76 45 67");
        XBeeResponse respRemote = getXBee().sendSynchronous(new RemoteAtRequest(remote64, "ID"), 5000);
        logger.info(respRemote);

        getXBee().sendAsynchronous(new AtCommand("ND"));
/*
        doRemoteATCommand("A0", remote64);
        doRemoteATCommand("MY", remote64);
        doRemoteATCommand("ID", remote64);
        

        Timer timer = new Timer("Time Sync", true);
        timer.schedule(new TimeSyncProcessor(xbee, remote64), 1000, 10000);*/
    }
    
    public void nodeDiscovery() throws XBeeException {
        System.out.println("node discovery");
        getXBee().sendAsynchronous(new AtCommand("ND"));
    }
    
    public void sendCommand(String cmd) throws XBeeException {
        int[] cmdBytes = ByteUtils.stringToIntArray(cmd);
        for (XBeeAddress64 xbee64Addr : knownNodes) {
            try {
            ZNetTxRequest request = new ZNetTxRequest(xbee64Addr, cmdBytes);
            ZNetTxStatusResponse response = (ZNetTxStatusResponse) xbee.sendSynchronous(request, 2000);
            if (response.getDeliveryStatus() == ZNetTxStatusResponse.DeliveryStatus.SUCCESS) {
                System.out.println("Sent to "+response.getRemoteAddress16());
            } else {
                System.out.println("Unsuccessful send "+xbee64Addr);
            }
            } catch (XBeeTimeoutException e) {
                System.out.println("Timeout send to "+xbee64Addr);
            }
        }
        System.out.println("Send Command: "+cmd+" to "+knownNodes.size()+" xbees.");
    }
    
    public XBee getXBee() throws XBeeException {
        if (xbee == null) {
            try {
                initXBee();
            } catch( XBeeException e) {
                xbee = null;
                throw e;
            }
        }
        return xbee;
    }
    
    public void closeXBee() {
        if (xbee != null) {
            logger.info("Close ZBee");
            xbee.close();
            xbee = null;
        }
        
    }
    
    void initXBee() throws XBeeException {
        try {
            closeXBee();
            if (mockXBee) {
                xbee = new MockXBee();
            } else {
                xbee = new XBee();
            }
            System.out.println("try to init xbee at "+getPort()+" "+getBaud());
            logger.info("try to init xbee at "+getPort()+" "+getBaud());
            xbee.open(getPort(), getBaud());
        
            /*
            XBeeResponse resp2 = getXBee().sendSynchronous(new AtCommand("AP"));
            log.info(resp2);
            resp2 = getXBee().sendSynchronous(new AtCommand("BD"));
            log.info(resp2);
            */
            tSync = new TimeSyncProcessor(xbee);
            processor.addRadioStatListener(tSync);
            processor.addRadioStatListener(new RadioStatListener() {
                
                @Override
                public void nodeIdentify(ZBNodeDiscover nodeId) {
                    String staCode = nodeId.getNodeIdentifier().trim();
                    if (staCode.length() > 5) {
                        staCode = staCode.substring(0, 5);
                    }
                    stationCodeMap.put(nodeId.getNodeAddress64().toString(), staCode);
                    knownNodes.add(nodeId.getNodeAddress64());
                    System.out.println("Discover Station: "+nodeId.getNodeAddress64().toString()+" -> "+staCode);
                    logger.info("Station Node Map: "+nodeId.getNodeAddress64().toString()+" -> "+staCode);
                }
                
                @Override
                public void heartbeat(Heartbeat heartbeat) {
                    // TODO Auto-generated method stub
                    
                }
            });
            xbee.clearResponseQueue();
            xbee.addPacketListener(msgReader);
            nodeDiscovery();
            //getXBee().sendAsynchronous(new AtCommand("ND"));
        } catch(XBeeException e) {
            logger.error("Unable to init xbee, closing", e);
            try {
            closeXBee();
            } catch(Throwable ee) {
                //oh well
            }
            throw e;
        }
    }
    
    void doRemoteATCommand(String cmd, XBeeAddress64 remote64) throws XBeeException {
        XBeeResponse respRemote = xbee.sendSynchronous(new RemoteAtRequest(remote64, cmd), 5000);
        logger.info(respRemote);
    }
    
    
    
    public String getPort() {
        return port;
    }

    
    public void setPort(String port) {
        this.port = port;
    }

    
    public int getBaud() {
        return baud;
    }

    
    public void setBaud(int baud) {
        this.baud = baud;
    }
    
    
    public boolean isMockXBee() {
        return mockXBee;
    }

    
    public void setMockXBee(boolean mockXBee) {
        this.mockXBee = mockXBee;
    }

    public String findSerialPort() {
        if ( isMockXBee()) {
            return "dummy";
        }
        SerialPortChooser sChoose = new SerialPortChooser();
        if (sChoose.getPossibleSerialPorts().size() > 0) {
        return sChoose.getPossibleSerialPorts().get(0);
        } else {
            return null;
        }
    }
    
    protected void finalize() {
        closeXBee();
    }
    
    protected void doInitGui() throws IOException {

        final GUI gui = new GUI(this);

        TimeSeriesTableModel tstm = new TimeSeriesTableModel(50);
        gui.getDetectionTable().setModel(tstm);
        tstm.addTableModelListener(gui.getDetectionTable());
        MultiListener listener = new MultiListener(tstm);

        DataStore dataStore = new DataStore();
        MiniseedGenerator mseedGenerator = new MiniseedGenerator(stationCodeMap);
        listener.addListener(dataStore);
        listener.addListener(mseedGenerator);
        processor.addTimeSeriesListener(listener);

        HeartbeatModel hbModel = new HeartbeatModel();
        gui.getHeartbeatTable().setModel(hbModel);
        processor.addRadioStatListener(hbModel);

        KnownRadiosTableModel radioTM = new KnownRadiosTableModel();
        gui.getRadioTable().setModel(radioTM);
        processor.addRadioStatListener(radioTM);

        final PhotoStore photoStore = new PhotoStore();
        MultiTimedPhotoListener photoListen = new MultiTimedPhotoListener(photoStore);
        PhotoAssembler photoAssembler = new PhotoAssembler(photoListen);
        photoListen.addListener(new TimedPhotoListener() {

            public void photoReceived(TimedPhoto photo) {
                logger.info("New photo, resetting label.");
                gui.getLastPhotoLabel().setToolTipText(photo.toString());
                gui.getLastPhotoLabel().setIcon(new ImageIcon(photo.getPhoto()));
                gui.getLastPhotoLabel().repaint();
            }
        });
        processor.addPhotoSegmentListener(photoAssembler);

        processor.infoListener = new InfoListener() {

            public void infoMessageReceived(InfoMessage message) {
                gui.getInfoTextArea().append(message.getWho().get16BitValue()+"   "+message.getRemoteWhen()+"   "+message.getInfo()+"\n");
            }
        };

        gui.getFrame().addWindowListener(new WindowAdapter() {

            public void windowClosing(WindowEvent arg0) {
                closeXBee();
            }


        });
        gui.getFrame().setVisible(true);
    }

    /**
     * @param args
     * @throws IOException 
     */
    public static void main(String[] args) throws IOException {
        try {
            HorseyTime ht = new HorseyTime(args);
            BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
            while (true) {
                if (in.ready()) {
                    String line = in.readLine();
                    if (line.trim().equals("q")) {
                        ht.sendCommand("stop");
                        System.out.println("Quitting...");
                        ht.closeXBee();
                        System.exit(0);
                    } else if (line.trim().equals("help")) {
                        System.out.println("Known commands are: q nd stop start status gain sps queue help");
                    } else if (line.trim().equals("nd")) {
                        ht.nodeDiscovery();
                    } else if (line.trim().equals("stop")) {
                        ht.sendCommand("stop");
                    } else if (line.trim().equals("start")) {
                        ht.sendCommand("start");
                    } else if (line.trim().equals("status")) {
                        ht.sendCommand("status");
                    } else if (line.trim().equals("gain")) {
                        ht.sendCommand("gain");
                    } else if (line.trim().equals("sps")) {
                        ht.sendCommand("sps");
                    } else if (line.trim().equals("queue")) {
                        ht.sendCommand("queue");
                    } else {
                        System.out.println("Known commands are: q nd stop start status gain sps queue help");
                    }
                }
            }
        } catch(XBeeException e) {
            logger.error("XBee init problem: ", e);
        }
    }

    boolean mockXBee = false;
    
    Set<XBeeAddress64> knownNodes = new HashSet<XBeeAddress64>();
    
    XBee xbee;
    MessageReader msgReader;
    Queue<TimedMessage> messageQueue = new LinkedList<TimedMessage>();
    TimeSyncProcessor tSync;
    MessageProcessor processor;
    String port = "/dev/tty.usbserial-A700fpNT";
    //int baud = 9600;
    //int baud = 57600;
    int baud = 115200;
    static final String DEFAULT_PROPS = "org/crotwell/horseyTime/data/horseyTime.prop";
    private static final Logger logger = Logger.getLogger(HorseyTime.class);
}
