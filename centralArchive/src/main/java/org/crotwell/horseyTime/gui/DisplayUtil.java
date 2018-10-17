package org.crotwell.horseyTime.gui;

import com.rapplogic.xbee.api.XBeeAddress16;
import com.rapplogic.xbee.api.XBeeAddress64;


public class DisplayUtil {
    
    public static String hexPrefix = "0x";
    
    public static String displayHex(int b) {
        if (b < 0x10) {
            return "0" + Integer.toHexString(b);
        } else {
            return  Integer.toHexString(b);
        }
    }
    
    public static String display(XBeeAddress16 addr) {
        return hexPrefix+displayHex(addr.getMsb())+displayHex(addr.getLsb());
    }
    
    public static String display(XBeeAddress64 addr) {
        return displayIntAsHex(addr.getAddress());
    }

    public static String displayIntAsHex(int[] val) {
        String s = hexPrefix;
        for (int i = 0; i < val.length; i++) {
            s += displayHex(val[i]);
        }
        return s;
    }
}
