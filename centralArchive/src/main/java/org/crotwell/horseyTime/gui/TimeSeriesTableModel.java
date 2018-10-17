package org.crotwell.horseyTime.gui;

import java.util.LinkedList;
import java.util.List;

import javax.swing.table.AbstractTableModel;

import org.crotwell.horseyTime.data.Detection;
import org.crotwell.horseyTime.data.TimeSeriesPacket;
import org.crotwell.horseyTime.events.DetectionListener;
import org.crotwell.horseyTime.events.TimeSeriesListener;


public class TimeSeriesTableModel extends AbstractTableModel implements TimeSeriesListener {

    public TimeSeriesTableModel(int maxSize) {
        this.maxSize = maxSize;
    }
    
    public int getColumnCount() {
        return 4;
    }

    public int getRowCount() {
        return detectList.size();
    }

    public Object getValueAt(int row, int col) {
        TimeSeriesPacket d = detectList.get(row);
        switch (col) {
            case 0:
                return d.getReceived();
            case 1:
                return DisplayUtil.display(d.getWho());
            case 2:
                return d.getRemoteWhen();
            case 3:
                return d.getX()[0];
            default:
                return "xxx";
        }
    }
    
    public String getColumnName(int col) {
        return columnNames[col].toString();
    }

    @Override
    public void timeSeries(TimeSeriesPacket tsp) {
        detectList.add(tsp);
        if (detectList.size() >= maxSize) {
            detectList.remove(0);
            super.fireTableRowsDeleted(0, 0);
        }
        super.fireTableRowsInserted(detectList.size(), detectList.size());
    }
    
    String[] columnNames = new String[] {"Received", "Remote XBee", "Remote Millis", "Inches"};
    
    int maxSize;
    
    List<TimeSeriesPacket> detectList = new LinkedList<TimeSeriesPacket>();

    public void heartbeat(int remoteTime) {
        // TODO Auto-generated method stub
        
    }

}
