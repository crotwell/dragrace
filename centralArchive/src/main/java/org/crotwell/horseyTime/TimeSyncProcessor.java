package org.crotwell.horseyTime;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;
import java.util.TimerTask;

import org.crotwell.horseyTime.data.Heartbeat;
import org.crotwell.horseyTime.events.RadioStatListener;

import com.rapplogic.xbee.api.XBee;
import com.rapplogic.xbee.api.XBeeAddress64;
import com.rapplogic.xbee.api.XBeeException;
import com.rapplogic.xbee.api.wpan.TxRequest64;
import com.rapplogic.xbee.api.zigbee.ZBNodeDiscover;

public class TimeSyncProcessor extends TimerTask implements RadioStatListener {

    public TimeSyncProcessor(XBee xbee) {
        super();
        this.xbee = xbee;
    }
    
    public void add(XBeeAddress64 who) {
        this.who.add(who);
    }

    public void run() {
        int[] payload = new int[9];
        payload[0] = 3;
        for (XBeeAddress64 addr : who) {
            try {
                Calendar cal = Calendar.getInstance();
                int ymd = (cal.get(Calendar.YEAR))*10000
                        +(cal.get(Calendar.MONTH)+1)*100 // month zero based
                        +cal.get(Calendar.DAY_OF_MONTH);
                payload[1] = (ymd >> 24) & 0xff;
                payload[2] = (ymd >> 16) & 0xff;
                payload[3] = (ymd >>  8) & 0xff;
                payload[4] = (ymd      ) & 0xff;
                int millisInDay = ((cal.get(Calendar.HOUR_OF_DAY)*60 + cal.get(Calendar.MINUTE))*60
                        +cal.get(Calendar.SECOND))*1000
                        +cal.get(Calendar.MILLISECOND);
                payload[5] = (millisInDay >> 24) & 0xff;
                payload[6] = (millisInDay >> 16) & 0xff;
                payload[7] = (millisInDay >>  8) & 0xff;
                payload[8] = (millisInDay      ) & 0xff;
                xbee.sendAsynchronous(new TxRequest64(addr, payload));
                Thread.sleep(1000);
            } catch(XBeeException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            } catch(InterruptedException e) {}
        }
    }

    List<XBeeAddress64> who = new ArrayList<XBeeAddress64>();

    XBee xbee;

    public void nodeIdentify(ZBNodeDiscover nodeId) {
    }

    public void heartbeat(Heartbeat heartbeat) {
        if ( ! who.contains(heartbeat.getXBeeResponse().getRemoteAddress64())) {
            who.add(heartbeat.getXBeeResponse().getRemoteAddress64());
        }
        run();
    }
}
