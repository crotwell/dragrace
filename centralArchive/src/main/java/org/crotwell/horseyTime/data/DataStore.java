package org.crotwell.horseyTime.data;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

import org.apache.log4j.Logger;
import org.crotwell.horseyTime.events.TimeSeriesListener;
import org.crotwell.horseyTime.gui.DisplayUtil;



public class DataStore implements TimeSeriesListener {
    
    public DataStore() throws IOException {
        schema();
        out = new BufferedWriter(new FileWriter(new File("horseyTime.out")));
    }
    

    protected void schema() {
        //SchemaUpdate update = new SchemaUpdate(getConfiguration());
        //update.execute(false, true);
        
    }
    
    public void put(TimeSeriesPacket d) throws IOException {
        out.write(d.getReceived()+","+DisplayUtil.display(d.getWho())+","+d.getRemoteWhen()+","+d.getX()[0]+"\n");
        out.flush();
    }

  
    private static BufferedWriter out;
    private static final Logger logger = Logger.getLogger(DataStore.class);
    public void timeSeries(TimeSeriesPacket event) {
        try {
            put(event);
        } catch(IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }


    public void heartbeat(int remoteTime) {
        // TODO Auto-generated method stub
        
    }
    
}
