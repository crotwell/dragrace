package org.crotwell.horseyTime.events;

import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.time.Duration;
import java.time.Instant;
import java.time.ZonedDateTime;
import java.util.HashMap;
import java.util.Map;

import org.apache.log4j.Logger;
import org.crotwell.horseyTime.SpsByNode;
import org.crotwell.horseyTime.data.TimeSeriesPacket;

import edu.iris.dmc.seedcodec.B1000Types;
import edu.iris.dmc.seedcodec.Codec;
import edu.sc.seis.seisFile.TimeUtils;
import edu.sc.seis.seisFile.mseed.Blockette100;
import edu.sc.seis.seisFile.mseed.Blockette1000;
import edu.sc.seis.seisFile.mseed.Btime;
import edu.sc.seis.seisFile.mseed.DataHeader;
import edu.sc.seis.seisFile.mseed.DataRecord;
import edu.sc.seis.seisFile.mseed.SeedFormatException;

public class MiniseedGenerator implements TimeSeriesListener {
    
    public MiniseedGenerator(Map<String, String> stationCodeMap) {
        this.stationCodeMap = stationCodeMap;
        logger.info("MiniseedGenerator constructor");
        this.dataDir = new File("Data");
        if (! dataDir.exists()) {
            dataDir.mkdirs();
        }
    }

    @Override
    public void timeSeries(TimeSeriesPacket tsp) {
        try {

            //logger.info("MiniseedGenerator timeseries \n"+tsp.toString());
            //logger.info("MiniseedGenerator timeseries");
            createMiniseed(tsp);
        } catch (SeedFormatException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }
    
    public String createKey(String staCode, int chanIndex) {
        return staCode+"_"+chanIndex;
    }

    public void createMiniseed(TimeSeriesPacket tsp) throws SeedFormatException {
        for (int chanIndex=0; chanIndex < 3; chanIndex++) {
            DataRecord current;
            String key = createKey(tsp.getStaCode(), chanIndex);
            if (dataRecordCache.get(key) == null) {
                current = createDataRecord(chanIndex, tsp);
            } else {
                current = dataRecordCache.get(key);
                Instant currentEnd = current.getPredictedNextStartBtime().toInstant();
                Instant packetBegin = getStartInstant(tsp);

                Instant currentBegin = current.getStartBtime().toInstant();
                if (! SpsByNode.contains(tsp.getStaCode())) {
                    // second packet for this station, calc a sps
                    // based on previous and current
                    Float sps = SpsByNode.getSpsGuess(tsp.getStaCode(), tsp.getSPS(), currentBegin, current.getHeader().getNumSamples(), packetBegin);
                    if (SpsByNode.contains(tsp.getStaCode()) && current.getBlockettes(100).length == 0) {
                        // only add b100 if SpsByNode actually did calc, ie not too far off
                        // and have not already added
                        Blockette100 b100 = new Blockette100();
                        b100.setActualSampleRate(sps);
                        current.addBlockette(b100);
                    }
                }
                // force a positive duration to allow small gaps or overlaps less than
                // a sample interval
                Duration d = Duration.between(currentEnd, packetBegin).abs();
                if (d.getSeconds() > 0 || d.getNano()/1000000000 > 0.5/current.getSampleRate()) {
                    Duration spsDur = Duration.between(currentBegin, packetBegin).dividedBy(current.getHeader().getNumSamples());
                    logger.info("GAP  "+current.getHeader().getStationIdentifier()+"."+current.getHeader().getChannelIdentifier()+" "+current.getHeader().getNumSamples()+"  dr end="+currentEnd+"  tsp start="+packetBegin+"  dur="+d+"   SPS:"+(1000000000.0/spsDur.toNanos()));
                    sendDataRecord(current, key);
                    current = createDataRecord(chanIndex, tsp);
                } else if (current.getHeader().getNumSamples() + tsp.getNumSamples() < MAX_SHORTS_IN_DR) {
                    // fits in remaining space, assuming short, no compression
                    //logger.info("fits in current datarecord");
                    int[] appendData = tsp.getData(chanIndex);
                    combine(current, appendData);
                } else {
                    // doesn't fit, ship it and make new
                    //logger.info("does not fit in current datarecord");
                    // back calc the sample rate
                    Float sps = SpsByNode.calcSps(currentBegin, current.getHeader().getNumSamples(), packetBegin);
                    if (SpsByNode.isSpsWithinTolOfNominal(sps, tsp.getNominalSPS())) {
                        SpsByNode.update(tsp.getStaCode(), sps);
                        if (SpsByNode.contains(tsp.getStaCode()) && current.getBlockettes(100).length == 0) {
                            // only add b100 if SpsByNode actually did calc, ie not too far off
                            Blockette100 b100 = new Blockette100();
                            b100.setActualSampleRate(sps);
                            current.addBlockette(b100);
                        } else {
                            Blockette100 b100 = (Blockette100) current.getUniqueBlockette(100);
                            b100.setActualSampleRate(sps);
                        }
                    }
                    sendDataRecord(current, key);
                    current = createDataRecord(chanIndex, tsp);
                }
            }
            dataRecordCache.put(key, current);
        }
    }

    public static Btime getBtime(TimeSeriesPacket tsp) {
        Btime btime = new Btime();
        btime.tenthMilli = tsp.getMillisecond()*10;

        if (tsp.getMillisecond() == 1000) {
            // can happen due to rounding of micros/1000, but causes err,
            // so just back up by one tenth millisecond
            btime.tenthMilli = 9999;
        }
        btime.year = tsp.getYear();
        btime.jday = tsp.getDoy();
        btime.hour = tsp.getHour();
        btime.min = tsp.getMinute();
        btime.sec = tsp.getSecond();
        //logger.info("getBtime for tsp: "+tsp.getHour()+" "+tsp.getMillisecond()+"  "+btime.toString());
        return btime;
    }

    public static Btime getBtime(Instant date) {
        ZonedDateTime zdt = ZonedDateTime.ofInstant(date, TimeUtils.TZ_UTC);
        Btime btime = new Btime();
        btime.tenthMilli = zdt.getNano()/100000;
        btime.year = zdt.getYear();
        btime.jday = zdt.getDayOfYear();
        btime.hour = zdt.getHour();
        btime.min = zdt.getMinute();
        btime.sec = zdt.getSecond();
        return btime;
    }
    
    private void sendDataRecord(DataRecord current, String key) {
        String sta = current.getHeader().getStationIdentifier().trim();
        String chan = current.getHeader().getChannelIdentifier();
        int hour = current.getStartBtime().hour;
        String filename = sta+"."+chan+"_"+current.getStartBtime().jday+"_"+hour+".mseed";
        DataOutputStream dos = null;
        try {
        if (filenameByChan.get(key) != filename) {
            if (dosByChan.get(key) != null) { 
                try {
                    dosByChan.get(key).close();
                } catch (IOException e) {
                    // TODO Auto-generated catch block
                    e.printStackTrace();
                }
            }
            File dir =   new File(dataDir, "Day_"+current.getStartBtime().jday);
            if (! dir.exists()) {
                dir.mkdirs();
            }
            File f = new File(dir, filename);
            dos = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(f,true)));
            dosByChan.put(key, dos);
        } else {
            dos = dosByChan.get(key);
        }
            logger.info("sending... samp period="+(Duration.between(current.getStartBtime().toInstant(), current.getPredictedNextStartBtime().toInstant()).dividedBy(current.getHeader().getNumSamples()))+" "+current.getHeader().getNumSamples());
            //current.writeASCII(printer, "  ");
            //printer.flush();
            
            current.write(dos);
            //logger.info("Write data record: "+current.getHeader().getDataBlocketteOffset());
        } catch (FileNotFoundException e) {
            System.err.println("unable to write data to file: "+e);
            e.printStackTrace();
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } finally {
        }
    }
    
    public void flush() {
        for (String key : stationCodeMap.keySet()) {
            DataRecord current;
            if (dataRecordCache.get(key) == null) {
                // nothing to flush
            } else {
                current = dataRecordCache.get(key);
                dataRecordCache.put(key, null);
                sendDataRecord(current, key);
            }
        }
    }

    public DataRecord createDataRecord(int chanIndex, TimeSeriesPacket tsp) throws SeedFormatException {
        String staCode = "UNKNW";
        if (stationCodeMap != null) {
            staCode = stationCodeMap.get(tsp.getXBeeResponse().getRemoteAddress64().toString());
            if (staCode == null) {
                staCode = "UNKNW";
            }
        }
        DataHeader dh = new DataHeader(0, 'D', false);
        dh.setNetworkCode(networkCode);
        dh.setStationIdentifier(staCode);
        dh.setLocationIdentifier(locationCode);
        dh.setChannelIdentifier(channelCodes[chanIndex]);
        dh.setNumSamples((short)tsp.getNumSamples()); 
        dh.setSampleRate(tsp.getNominalSPS()); // will set actual in B100
        Btime btime = getBtime(tsp);
        Btime start = new Btime(getStartInstant(tsp));
        //logger.info("DataRecord BTime :"+start.toString()+" "+btime.toString());
        dh.setStartBtime(start);
        DataRecord dr = new DataRecord(dh);
        Blockette1000 b1000 = new Blockette1000();
        b1000.setDataRecordLength(MSEED_512);
        b1000.setEncodingFormat((byte) B1000Types.SHORT);
        b1000.setWordOrder(BIG_ENDIAN);
        dr.addBlockette(b1000);
        int[] data = tsp.getData(chanIndex);
        dr.setData(CODEC.encodeAsBytes(intToShort(data)));
        //logger.info("createDataRecord blockette offset=" +dh.getDataBlocketteOffset()+"  "+b1000.getDataRecordLength());
        return dr;
    }
    
    public Instant getStartInstant(TimeSeriesPacket tsp) {
        Btime btime = getBtime(tsp);
        double seconds = (tsp.getNumSamples()-1)/tsp.getSPS();
        Duration dur = Duration.ofSeconds(0, Math.round(seconds * 1000000000));
        Instant out =  btime.toInstant().minus(dur);
        //logger.debug("getStartInstant   tsp: "+btime+"  dur "+dur+"  start: "+out);
        return out;
    }
    
    public DataRecord combine(DataRecord current, int[] appendData) throws SeedFormatException {
        byte[] curData = current.getData();
        byte[] appendBytes = CODEC.encodeAsBytes(intToShort(appendData));
        byte[] combinedData = new byte[curData.length+appendBytes.length];
        for (int j = 0; j < combinedData.length; j++) {
            if (j < curData.length) {
                combinedData[j] = curData[j];
            } else {
                combinedData[j] = appendBytes[j-curData.length];
            }
        }
        current.setData(combinedData);
        current.getHeader().setNumSamples((short) (current.getHeader().getNumSamples()+appendData.length));

        //logger.info("combine blockette offset=" +current.getHeader().getDataBlocketteOffset());
        return current;
    }
    
    public static short[] intToShort(int[] data) {
        short[] out = new short[data.length];
        for (int i = 0; i < out.length; i++) {
            out[i] = (short)data[i];
        }
        return out;
    }
    
    public static final Codec CODEC = new Codec();

    public static final byte BIG_ENDIAN = (byte)1;

    public static final byte MSEED_512 = (byte)9;
    
    public static final byte MSEED_4096 = (byte)12;

    public static final int DATA_HEADER_SIZE = 48;
    
    public static final int MAX_SHORTS_IN_DR = (512 - DATA_HEADER_SIZE - Blockette1000.B1000_SIZE - Blockette100.B100_SIZE) / 2;
    
    File dataDir;

    Map<String, DataRecord> dataRecordCache = new HashMap<String, DataRecord>();
    
    String networkCode = "CO";
    Map<String, String> stationCodeMap;
    String locationCode = "00";
    String[] channelCodes = { "HNX", "HNY", "HNZ" };
    
    Map<String, DataOutputStream> dosByChan = new HashMap<String, DataOutputStream>();
    
    Map<String, String> filenameByChan = new HashMap<String, String>();
    
    PrintWriter printer = new PrintWriter(new OutputStreamWriter(System.out));

    private static final Logger logger = Logger.getLogger(MiniseedGenerator.class);
}
