package org.crotwell.horseyTime.data;

import java.util.Date;

import org.apache.log4j.Logger;

import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;

public class InfoMessage extends ZNetRxResponseTimedData {

    public InfoMessage(ZNetRxResponse xbeeResp, Date received) {
        super(xbeeResp, received);
        int[] data = xbeeResp.getData();
        info = "";
        int i=1;
        while (i<data.length && data[i] != 0) {
            info += new Character((char)data[i]);
            i++;
        }
        log.info("Info: " + info);
    }

    public String getInfo() {
        return info;
    }

    public int getRemoteWhen() {
        return remoteWhen;
    }

    protected int remoteWhen=0;

    protected String info;

    private static final Logger log = Logger.getLogger(InfoMessage.class);
}
