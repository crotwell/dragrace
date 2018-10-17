package org.crotwell.horseyTime.data;

import java.util.Date;

import org.apache.log4j.Logger;
import org.crotwell.horseyTime.SpsByNode;

import com.rapplogic.xbee.api.zigbee.ZNetRxResponse;

import edu.iris.dmc.seedcodec.Utility;
import edu.sc.seis.seisFile.mseed.Blockette100;

public class TimeSeriesPacket extends ZNetRxResponseTimedData {

    public TimeSeriesPacket(ZNetRxResponse xbeeResp, Date received, String staCode) {
        super(xbeeResp, received);
        int[] data = xbeeResp.getData();
        extractFromArray(data, staCode);
    }
    
    public TimeSeriesPacket(int[] data, String staCode) {
        super(null, null); //dummy
        extractFromArray(data, staCode);
    }
    
    void extractFromArray(int[] data, String staCode) {
        this.staCode = staCode;
        numSamples = data[1];
        if (numSamples > 32 ) {
            throw new RuntimeException("Got > 32 samples? "+numSamples);
        }
        if (data.length < numSamples + headerSize) {
            logger.warn("wrong num samples: "+numSamples+"  "+data.length);
            return;
        }
        demux(data);
        year = Utility.bytesToShort((byte)data[2], (byte)data[3], false);
        doy  = Utility.bytesToShort((byte)data[4], (byte)data[5], false);
        hour = data[6];
        minute = data[7];
        second = data[8];
        millisecond  = Utility.bytesToShort((byte)data[9], (byte)data[10], false);
        nominalSps = data[11];
        if (SpsByNode.contains(staCode)) {
            // only add b100 if SpsByNode actually did calc, ie not too far off
            sps = SpsByNode.retreive(staCode);
        } else {
            sps = nominalSps;
        }
        remoteWhen = 0; // temp
        //remoteWhen = (data[2] << 24) + (data[3] << 16) + (data[4] << 8) + data[5];
        //logger.info("TimeSeries: " + numSamples + " at " + data[2] + " " + data[3] + " " + data[4] + " "
        //        + data[5]+" "+data[6]+"  "+data[7]+" "+data[8]+" "+data[9]+" "+data[10]);
        
        logger.info("TimeSeries: "+staCode+" " + numSamples + " at " + year+" "+doy+" "+hour+" "+minute+" "+second+" "+millisecond );
 
    }

    private float guessSps(int nominalSps) {
        if (nominalSps == 200) {
            return 195.85f;
        } else if (nominalSps == 100) {
            //return 98.6193f;
            return 100f;
            //return 98.8975f;
        } else if (nominalSps == 50) {
            return 48.65f;
        } else {
            return nominalSps;
        }
    }

    public int[] getX() {
        return xData;
    }
    public int[] getY() {
        return yData;
    }
    public int[] getZ() {
        return zData;
    }
    
    public int[] getData(int chanIndx) {
        switch (chanIndx) {
        case 0:
            return getX();
        case 1:
            return getY();
        case 2:
            return getZ();

        default:
            throw new IllegalArgumentException("ChanIndx must be 0-2 but "+chanIndx);
        }
    }
    

    public int getNumSamples() {
        return numSamples;
    }

    public void setNumSamples(int numSamples) {
        this.numSamples = numSamples;
    }

    public int getYear() {
        return year;
    }

    public int getDoy() {
        return doy;
    }

    public int getHour() {
        return hour;
    }

    public int getMinute() {
        return minute;
    }

    public int getSecond() {
        return second;
    }

    public int getMillisecond() {
        return millisecond;
    }
    public int getNominalSPS() {
        return nominalSps;
    }
    
    public float getSPS() {
        return sps;
    }

    public int getWhoInt() {
        return getWho().get16BitValue();
    }

    public int getRemoteWhen() {
        return remoteWhen;
    }

    public String getStaCode() {
        return staCode;
    }

    String staCode;
    
    int headerSize = 12;
    
    protected int remoteWhen;

    void demux(int[] data) {
        xData = new int[numSamples];
        yData = new int[numSamples];
        zData = new int[numSamples];
        for (int i = 0; 6*i + headerSize < data.length; i++) {
            int idx = headerSize+ 6*i;
            xData[i] = twoBytesToInt(data[idx  ], data[idx+1]);
            yData[i] = twoBytesToInt(data[idx+2], data[idx+3]);
            zData[i] = twoBytesToInt(data[idx+4], data[idx+5]);
        }
    }
    
    int twoBytesToInt(int a, int b) {
        // MMA8451 is 14 bit, but aligned to the 16 bit mark, odd but allows
        // them to get 8 significant bits into the first byte for low res mode
        short s = (short) (Utility.bytesToShort((byte)a, (byte)b, false) >> 2);
        return s;
    }
    
    public String toString() {
        String milliStr = ""+millisecond;
        if (millisecond < 100 ) {
            if (millisecond < 10 ) {
                milliStr = "0"+milliStr;
            }
            milliStr = "0"+milliStr;
        }
        String out = year+" "+doy+" "+hour+":"+minute+":"+second+"."+milliStr+"    sps="+nominalSps+" npts="+numSamples+"\n";
        for (int i = 0; i < xData.length; i++) {
            out += "  "+xData[i]+" "+yData[i]+" "+zData[i]+"\n";
        }
        return out;
    }
    
    int numSamples;
    int year;
    int doy;
    int hour;
    int minute;
    int second;
    int millisecond;
    int nominalSps;
    float sps;
    int[] xData;
    int[] yData;
    int[] zData;
    

    private static final Logger logger = Logger.getLogger(TimeSeriesPacket.class);

}
