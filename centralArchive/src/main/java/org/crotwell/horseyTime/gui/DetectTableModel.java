package org.crotwell.horseyTime.gui;

import java.util.LinkedList;
import java.util.List;

import javax.swing.table.AbstractTableModel;

import org.crotwell.horseyTime.data.Detection;
import org.crotwell.horseyTime.events.DetectionListener;


public class DetectTableModel extends AbstractTableModel implements DetectionListener {

    public DetectTableModel(int maxSize) {
        this.maxSize = maxSize;
    }
    
    public int getColumnCount() {
        return 4;
    }

    public int getRowCount() {
        return detectList.size();
    }

    public Object getValueAt(int row, int col) {
        Detection d = detectList.get(row);
        switch (col) {
            case 0:
                return d.getReceived();
            case 1:
                return DisplayUtil.display(d.getWho());
            case 2:
                return d.getRemoteWhen();
            case 3:
                return d.getInches();
            default:
                return "xxx";
        }
    }
    
    public String getColumnName(int col) {
        return columnNames[col].toString();
    }

    public void detected(Detection event) {
        detectList.add(event);
        if (detectList.size() >= maxSize) {
            detectList.remove(0);
            super.fireTableRowsDeleted(0, 0);
        }
        super.fireTableRowsInserted(detectList.size(), detectList.size());
    }
    
    String[] columnNames = new String[] {"Received", "Remote XBee", "Remote Millis", "Inches"};
    
    int maxSize;
    
    List<Detection> detectList = new LinkedList<Detection>();

    public void heartbeat(int remoteTime) {
        // TODO Auto-generated method stub
        
    }
}
