package org.crotwell.horseyTime;

import java.util.Properties;

import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.ConsoleAppender;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;
import org.apache.log4j.Priority;
import org.apache.log4j.PropertyConfigurator;
import org.crotwell.horseyTime.gui.SerialPortChooser;

import com.rapplogic.xbee.api.AtCommand;
import com.rapplogic.xbee.api.AtCommandResponse;
import com.rapplogic.xbee.api.XBee;
import com.rapplogic.xbee.api.XBeeConfiguration;
import com.rapplogic.xbee.api.XBeeException;


public class SimpleATCommander {

    /**
     * @param args
     * @throws XBeeException 
     */
    public static void main(String[] args) throws XBeeException {
        Properties props = new Properties();
        props.put("log4j.rootLogger", "info, stdout");
        props.put("log4j.appender.stdout", "org.apache.log4j.ConsoleAppender");
        props.put("log4j.appender.stdout.layout", "org.apache.log4j.PatternLayout");
        PropertyConfigurator.configure(props);
        SerialPortChooser sChoose = new SerialPortChooser();
        String port = sChoose.getPossibleSerialPorts().get(0);
        XBee xbee = new XBee();

        xbee.open(port, 9600);
        //xbee.open(port, 57600);
        
        AtCommandResponse ap = (AtCommandResponse)xbee.sendSynchronous(new AtCommand("AP"), 5000);
        if (!ap.isOk()) {
            throw new XBeeException("Attempt to query AP parameter failed");
        }
        
        if (ap.getValue()[0] != 2) {
            log.warn("XBee radio is in API mode without escape characters (AP=1).  The radio must be configured in API mode with escape bytes (AP=2) for use with this library."+ap.getValue()[0]);
            
            log.info("Attempting to set AP to 2");
            ap = (AtCommandResponse)xbee.sendSynchronous(new AtCommand("AP",2), 5000);
            
            if (ap.isOk()) {
                log.info("Successfully set AP mode to 2.  This setting will not persist a power cycle without the WR (write) command"); 
            } else {
                throw new XBeeException("Attempt to set AP=2 failed");
            }
        } else {
            log.info("Radio is in correct AP mode (AP=2)");
        }
        
// reset to factory defaults
        ap = (AtCommandResponse)xbee.sendSynchronous(new AtCommand("RE"), 5000);
        if (!ap.isOk()) {
            throw new XBeeException("Attempt to reset RE failed");
        }
        
        
        ap = (AtCommandResponse)xbee.sendSynchronous(new AtCommand("BD"), 5000);
        if (!ap.isOk()) {
            throw new XBeeException("Attempt to get BD parameter failed");
        }
        log.info("baud rate: "+ap.getValue()[0]);
        

        ap = (AtCommandResponse)xbee.sendSynchronous(new AtCommand("ID", new int[] {0x8f, 0xed}), 5000);
        if (!ap.isOk()) {
            throw new XBeeException("Attempt to get ID parameter failed");
        }
        ap = (AtCommandResponse)xbee.sendSynchronous(new AtCommand("ID"), 5000);
        if (!ap.isOk()) {
            throw new XBeeException("Attempt to get ID parameter failed");
        }
        String panid = "";
        for (int i = 0; i < ap.getValue().length; i++) {
            panid += " "+ap.getValue()[i];
        }
        log.info("pan id: "+panid);

        ap = (AtCommandResponse)xbee.sendSynchronous(new AtCommand("NI"), 5000);
        if (!ap.isOk()) {
            throw new XBeeException("Attempt to get NI parameter failed");
        }
        log.info("node id: "+ap.getValue()[0]);
int node = ap.getValue()[0];

        ap = (AtCommandResponse)xbee.sendSynchronous(new AtCommand("CH"), 5000);
        if (!ap.isOk()) {
            throw new XBeeException("Attempt to get CH parameter failed");
        }
        log.info("chan id: "+ap.getValue()[0]);
 int chan = ap.getValue()[0];
 
        /*
        ap = (AtCommandResponse)xbee.sendSynchronous(new AtCommand("BD",3), 5000);
        if (!ap.isOk()) {
            throw new XBeeException("Attempt to set BD parameter failed");
        }
        */
        // flash mem has limited writes, so avoid doing WR too often
      /*
        ap = (AtCommandResponse)xbee.sendSynchronous(new AtCommand("WR"), 5000);
        if (!ap.isOk()) {
            throw new XBeeException("Attempt to set params with WR parameter failed");
        }
        */
        log.info("closing up...");
        xbee.close();
        log.info("All done");
        log.info("panid "+panid+" node "+node+"  chan "+chan);
    }
    

    private static final Logger log = Logger.getLogger(SimpleATCommander.class);
}
