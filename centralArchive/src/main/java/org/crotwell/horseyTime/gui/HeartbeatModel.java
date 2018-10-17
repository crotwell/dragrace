package org.crotwell.horseyTime.gui;

import java.util.ArrayList;
import java.util.List;

import javax.swing.table.AbstractTableModel;

import org.crotwell.horseyTime.data.Heartbeat;
import org.crotwell.horseyTime.events.RadioStatListener;

import com.rapplogic.xbee.api.zigbee.ZBNodeDiscover;
import com.rapplogic.xbee.api.zigbee.ZNetNodeIdentificationResponse;


public class HeartbeatModel extends AbstractTableModel implements RadioStatListener {

    public int getColumnCount() {
        return 4;
    }

    public int getRowCount() {
        return beats.size();
    }

    public Object getValueAt(int row, int col) {
        Heartbeat r = beats.get(row);
        switch(col) {
            case 0:
                return r.getReceived();
            case 1:
                return DisplayUtil.display(r.getXBeeResponse().getRemoteAddress16());
            case 2:
                return r.getTime();
            case 3:
                return DisplayUtil.display(r.getXBeeResponse().getRemoteAddress64());
            default:
                return "eh?";    
        }
    }
    
    public String getColumnName(int col) {
        return columnNames[col].toString();
    }

    public void nodeIdentify(ZBNodeDiscover nodeId) {
        //ignore
    }

    public void heartbeat(Heartbeat heartbeat) {
        beats.add(heartbeat);
        super.fireTableRowsInserted(beats.size(), beats.size());
    }
    
    List<Heartbeat> beats = new ArrayList<Heartbeat>();
    
    String[] columnNames = new String[] {"Received", "Remote XBee", "Remote Millis", "Remote XBee64"};
}
