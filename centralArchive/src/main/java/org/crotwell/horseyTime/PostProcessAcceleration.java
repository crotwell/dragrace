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
            return;
        }
        File inFile = new File(args[0]);
        if ( ! inFile.isFile()) {
            System.err.println("Can't open "+args[0]+" to read from acceleration file.");
            System.exit(1);
        }
        String staCode = "UKNWN";
        if (args.length > 1) {
            staCode = args[1];
        } else {
          System.out.println("no station given, using UNKWN");
        }
        int loop=0;
        BufferedInputStream in = new BufferedInputStream(new FileInputStream(inFile));
        int headerLen = 12;
        byte[] head = new byte[headerLen];
        MiniseedGenerator mseedGen = new MiniseedGenerator(null);
        while(true) {
            int numRead = in.read(head);
            if (numRead == -1) {
              System.err.println("All Done! "+loop);
              return;
            }
            if (numRead != headerLen) {
                System.err.println("Tried to read 12 header bytes but only got "+numRead);
                mseedGen.flush();
                return;
            }
            //for (int i = 0; i < head.length; i++) {
          //      System.out.print(head[i]+" ");
        //    }
        //    System.out.println();
            int samplesAvail = head[1];
//System.out.println("samples: "+head[1]+" "+samplesAvail);
            if (samplesAvail < 1 || samplesAvail > 32) {
              System.out.println("Wrong num samples in TSP: "+samplesAvail+" "+head[0]);
              mseedGen.printCurrentRecordEndTimes();
              mseedGen.flush();
              int readCount = 0;
              if (head[0] == 0 && head[1] == 0) {
                // looks like region of all zeros, skip past looking for 65 30
                int readInt = 0;
                readInt = in.read();
                while(readInt == 0 ) {
                  readCount++;
                  readInt = in.read();
                }
                if (readInt == -1) {
                  // EOF
                  return;
                }
                head[1] = (byte)readInt;
                if (head[1] == 65) {
                  // might be start
                  head[0] = head[1];
                  readInt = in.read();
                  if (readInt == -1) {
                    // EOF
                    System.out.println("EOF");
                    return;
                  }
                  head[1] = (byte)readInt;
                  if (head[1] == 30) {
                    System.out.println("looks like recovery after "+readCount+" zero: "+head[0]+" "+head[1]);
                    samplesAvail = head[1];
                    // looks like clean , fill of header
                    for (int tmp = 2; tmp<12; tmp++) {
                      readInt = in.read();
                      if (readInt == -1) {
                        // EOF
                        System.out.println("EOF");
                        return;
                      }
                      head[tmp] = (byte)readInt;
                    }
                  } else {
                    // no idea, bail
                    System.err.println("looking for 65 30 after zeros but found "+head[0]+" "+head[1]);
                    return;
                  }
                } else {
                  // no idea, bail
                  System.err.println("looking for 65 after zeros but found "+readInt);
                  return;
                }
              }
            }
            byte[] dataBytes = new byte[6*samplesAvail];
            numRead = in.read(dataBytes);
            byte[] tspBytes = new byte[headerLen+dataBytes.length];
            System.arraycopy(head, 0, tspBytes, 0, headerLen);
            System.arraycopy(dataBytes, 0, tspBytes, headerLen, dataBytes.length);
//            System.out.println(tspBytes[0]+" "+tspBytes[1]+" "+tspBytes[2]+" "+tspBytes[3]);

            int[] asInts = new int[tspBytes.length];
            for (int i = 0; i < asInts.length; i++) {
                asInts[i] = tspBytes[i] & 0xff;
            }
            TimeSeriesPacket tsp = new TimeSeriesPacket(asInts, staCode );
            mseedGen.timeSeries(tsp);
  //          System.out.println("done packet "+tsp.getHour()+":"+tsp.getMinute()+":"+tsp.getSecond()+"."+tsp.getMillisecond());
            loop++;
        }
    }

}
