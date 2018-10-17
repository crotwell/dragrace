package org.crotwell.horseyTime;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;

import org.crotwell.horseyTime.data.TimeSeriesPacket;
import org.crotwell.horseyTime.events.MiniseedGenerator;

public class PostProcessAcceleration {

    public PostProcessAcceleration() {
        // TODO Auto-generated constructor stub
    }

    public static void main(String[] args) throws IOException {
        HorseyTime.loadPropsConfigLogging();
        if (args.length < 2) {
            System.out.println("Usage: postProcess.sh accerationfilename staCode");
        }
        File inFile = new File(args[0]);
        if ( ! inFile.isFile()) {
            System.err.println("Can't open "+args[0]+" to read from acceleration file.");
            System.exit(1);
        }
        String staCode = "UKNWN";
        if (args.length > 1) {
            staCode = args[1];
        }
        int loop=0;
        BufferedInputStream in = new BufferedInputStream(new FileInputStream(inFile));
        int headerLen = 12;
        byte[] head = new byte[headerLen];
        MiniseedGenerator mseedGen = new MiniseedGenerator(null);
        while(true) {
            int numRead = in.read(head);
            if (numRead != headerLen) {
                System.err.println("Tried to read 12 header bytes but only got "+numRead);
                return;
            }
            for (int i = 0; i < head.length; i++) {
                System.out.print(head[i]+" ");
            }
            System.out.println();
            int samplesAvail = head[1];
            System.out.println("samples: "+head[1]+" "+samplesAvail);
            byte[] dataBytes = new byte[6*samplesAvail];
            numRead = in.read(dataBytes);
            byte[] tspBytes = new byte[headerLen+dataBytes.length];
            System.arraycopy(head, 0, tspBytes, 0, headerLen);
            System.arraycopy(dataBytes, 0, tspBytes, headerLen, dataBytes.length);
            System.out.println(tspBytes[0]+" "+tspBytes[1]+" "+tspBytes[2]+" "+tspBytes[3]);

            int[] asInts = new int[tspBytes.length];
            for (int i = 0; i < asInts.length; i++) {
                asInts[i] = tspBytes[i] & 0xff;
            }
            TimeSeriesPacket tsp = new TimeSeriesPacket(asInts, staCode );
            mseedGen.timeSeries(tsp);
            System.out.println("done packet "+tsp.getHour()+":"+tsp.getMinute()+":"+tsp.getSecond()+"."+tsp.getMillisecond());
            loop++;
            if (loop > 100) {
                System.out.println("quitting early!!!");
                break;
            }
        }
        mseedGen.flush();
    }

}
