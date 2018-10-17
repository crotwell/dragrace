package org.crotwell.horseyTime;

import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

public class SpsByNode {

    public SpsByNode() {
        // TODO Auto-generated constructor stub
    }

    public static boolean contains(String staCode) {
        return spsMap.containsKey(staCode);
    }
    
    public static Float retreive(String staCode) {
        return spsMap.get(staCode);
    }
    
    public static void update(String staCode, Float sps) {
        // TODO Auto-generated method stub
        spsMap.put(staCode, sps);
    }

    public static Float getSpsGuess(String staCode, float nominalSps, Instant drStart, int drNpts, Instant tspStart) {
        if (drStart == null) {
            if (spsMap.containsKey(staCode)) {
                return spsMap.get(staCode);
            } else {
                return (float)nominalSps;
            }
        }
        Float sps = calcSps(drStart, drNpts, tspStart);
        if ( Math.abs(sps - nominalSps ) < MAX_SPS_PERCENT_ERR) {
            spsMap.put(staCode, sps);
        } else {
            // too far out to be legit, just use nominal
            sps = nominalSps;
        }
        return sps;
    }
    
    public static boolean isSpsWithinTolOfNominal(Float sps, float nominalSps) {
        return Math.abs(sps - nominalSps ) < MAX_SPS_PERCENT_ERR;
    }
    
    public static Float calcSps(Instant drStart, int drNpts, Instant tspStart) {
        Duration period = Duration.between(drStart, tspStart).dividedBy(drNpts);
        Float sps = (float)(NANOS_IN_SEC / period.toNanos());
        return sps;
    }
    
    
    static Map<String, Float> spsMap = new HashMap<String, Float>();
    
    static final float MAX_SPS_PERCENT_ERR = 0.03f;
    
    static final double NANOS_IN_SEC = 1e9;
}
