package org.crotwell.horseyTime.gui;

import java.io.File;
import java.io.FilenameFilter;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


public class SerialPortChooser {
    
    public SerialPortChooser() {
        String osType = getOSType();
        if (macosx.equals(osType)) {
            filter = new SerialPortFilter("tty.usbserial-.*");
        }
    }
    public List<String> getPossibleSerialPorts() {
        String osType = getOSType();
        if (macosx.equals(osType)) {
            File devDir = new File("/dev");
            File[] possiblePorts = devDir.listFiles(filter);
            List<String> out = new ArrayList<String>();
            for (int i = 0; i < possiblePorts.length; i++) {
                out.add(possiblePorts[i].getAbsolutePath());
            }
            return out;
        }
        throw new RuntimeException("Unknown OS type");
    }
    
    public String getOSType() {
        return macosx;
    }
    SerialPortFilter filter;
    
    public static final String macosx = "MacOSX";
}

class SerialPortFilter implements FilenameFilter {
    SerialPortFilter(String pattern) {
        serialPattern = Pattern.compile(pattern);
    }
    Pattern serialPattern ;
    public boolean accept(File directory, String filename) {
        Matcher m = serialPattern.matcher(filename);
        return m.matches();
    }
    
}
