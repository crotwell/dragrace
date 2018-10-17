package org.crotwell.horseyTime.gui;

import java.util.List;
import java.util.ArrayList;

import javax.swing.table.AbstractTableModel;

import org.crotwell.horseyTime.data.Heartbeat;
import org.crotwell.horseyTime.events.RadioStatListener;

import com.rapplogic.xbee.api.zigbee.ZBNodeDiscover;
import com.rapplogic.xbee.api.zigbee.ZNetNodeIdentificationResponse;


public class KnownRadiosTableModel extends AbstractTableModel implements RadioStatListener {

    public KnownRadiosTableModel()  {
    }
    
    public int getColumnCount() {
        // TODO Auto-generated method stub
        return 5;
    }

    public int getRowCount() {
        return known.size();
    }

    public Object getValueAt(int row, int col) {
        ZBNodeDiscover r = known.get(row);
        switch(col) {
            case 0:
                return DisplayUtil.display(r.getNodeAddress16());
            case 1:
                return DisplayUtil.display(r.getNodeAddress64());
            case 2:
                return r.getNodeIdentifier();
            case 3:
                return DisplayUtil.displayIntAsHex(r.getMfgId());
            case 4:
                return r.getDeviceType();
            default:
                return "eh?";    
        }
    }
    
    public String getColumnName(int col) {
        return columnNames[col].toString();
    }
    
    String[] columnNames = new String[] {"Remote XBee", "Remote XBee64", "Node Id", "Mfg Id", "Device"};
    
    List<ZBNodeDiscover> known = new ArrayList<ZBNodeDiscover>();

    public void nodeIdentify(ZBNodeDiscover nodeId) {
        known.add(nodeId);
        super.fireTableRowsInserted(known.size(), known.size());
    }

    public void heartbeat(Heartbeat heartbeat) {
        // ignore
    }
    
}
