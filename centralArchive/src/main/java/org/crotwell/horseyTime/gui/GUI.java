package org.crotwell.horseyTime.gui;

import java.awt.EventQueue;

import javax.swing.JFrame;
import javax.swing.JLabel;
import java.awt.BorderLayout;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.JTabbedPane;
import java.awt.GridLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowEvent;
import java.awt.event.WindowListener;

import javax.swing.JTextField;
import javax.swing.JButton;

import org.crotwell.horseyTime.HorseyTime;

import com.rapplogic.xbee.api.AtCommand;
import com.rapplogic.xbee.api.XBee;
import com.rapplogic.xbee.api.XBeeException;
import com.rapplogic.xbee.api.XBeeResponse;
import javax.swing.SwingConstants;
import javax.swing.JList;
import javax.swing.JTextArea;


public class GUI {

    private JFrame frame;
    private JTable detectionTable;
    private JTable radioTable;
    private JTextField txtSerialportinpu;
    private JTextField textField;
    private JLabel lblLastPhoto;
    private JTextArea infoTextArea;
    
    final HorseyTime ht;
    private JTable heartbeatTable;
    /**
     * Launch the application.
     */
    public static void main(final String[] args) {
        EventQueue.invokeLater(new Runnable() {

            public void run() {
                try {
                    GUI window = new GUI(new HorseyTime(args));
                    window.frame.setVisible(true);
                } catch(Exception e) {
                    e.printStackTrace();
                }
            }
        });
    }

    /**
     * Create the application.
     */
    public GUI(HorseyTime ht) {
        this.ht = ht;
        initialize();
        
    }

    /**
     * Initialize the contents of the frame.
     */
    private void initialize() {
        frame = new JFrame();
        frame.setBounds(100, 100, 450, 463);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        
        JTabbedPane tabbedPane = new JTabbedPane(JTabbedPane.TOP);
        frame.getContentPane().add(tabbedPane, BorderLayout.NORTH);
        
        JPanel configPanel = new JPanel();
        tabbedPane.addTab("Config", null, configPanel, null);
        configPanel.setLayout(new GridLayout(0, 2, 0, 0));
        
        JLabel lblSerialPort = new JLabel("Serial Port");
        configPanel.add(lblSerialPort);
        
        txtSerialportinpu = new JTextField();
        txtSerialportinpu.setText(ht.getPort());
        configPanel.add(txtSerialportinpu);
        txtSerialportinpu.setColumns(10);
        
        JLabel lblNewLabel = new JLabel("Baud Rate");
        configPanel.add(lblNewLabel);
        
        textField = new JTextField();
        textField.setText(""+ht.getBaud());
        configPanel.add(textField);
        textField.setColumns(10);
        
        JButton btnInitXbee = new JButton("Init XBee");
        configPanel.add(btnInitXbee);
        
        btnInitXbee.addActionListener(new ActionListener() {
            
            public void actionPerformed(ActionEvent e) {
                try {
                    ht.closeXBee();
                    ht.setMockXBee(false);
                    ht.setBaud(Integer.parseInt(textField.getText()));
                    ht.setPort(txtSerialportinpu.getText());
                    XBee xbee = ht.getXBee();
                    xbee.sendAsynchronous(new AtCommand("ND"));
                    System.out.println("Send ND request");
                } catch(XBeeException e1) {
                    // TODO Auto-generated catch block
                    e1.printStackTrace();
                }
            }
        });
        
        JButton btnMockXBee = new JButton("Mock XBee");
        configPanel.add(btnMockXBee);
        
        btnMockXBee.addActionListener(new ActionListener() {
            
            public void actionPerformed(ActionEvent e) {
                try {
                    ht.closeXBee();
                    ht.setMockXBee(true);
                    ht.setBaud(Integer.parseInt(textField.getText()));
                    ht.setPort(txtSerialportinpu.getText());
                    XBee xbee = ht.getXBee();
                    xbee.sendAsynchronous(new AtCommand("MY"));
                    System.out.println("Send MY request");
                } catch(XBeeException e1) {
                    // TODO Auto-generated catch block
                    e1.printStackTrace();
                }
            }
        });
        
        JButton btnNodeDetect = new JButton("Node Detect");
        configPanel.add(btnNodeDetect);
        btnNodeDetect.addActionListener(new ActionListener() {
            
            public void actionPerformed(ActionEvent e) {
                try {
                    XBee xbee = ht.getXBee();
                    xbee.sendAsynchronous(new AtCommand("ND"));
                    System.out.println("Send ND request");
                } catch(XBeeException e1) {
                    // TODO Auto-generated catch block
                    e1.printStackTrace();
                }
            }
        });

        
        JButton closeNodeDetect = new JButton("Close XBee");
        configPanel.add(closeNodeDetect);
        closeNodeDetect.addActionListener(new ActionListener() {
            
            public void actionPerformed(ActionEvent e) {
                ht.closeXBee();
                System.out.println("Close XBee");
            }
        });
        
        JPanel detectPanel = new JPanel();
        tabbedPane.addTab("Detections", null, detectPanel, null);
        
        JScrollPane scrollPane = new JScrollPane();
        detectPanel.add(scrollPane);
        
        detectionTable = new JTable();
        scrollPane.setViewportView(detectionTable);
        
        JPanel lastPhoto = new JPanel();
        tabbedPane.addTab("Last Photo", null, lastPhoto, null);
        lastPhoto.setLayout(new BorderLayout(0, 0));
        
        JScrollPane scrollPane_4 = new JScrollPane();
        lastPhoto.add(scrollPane_4, BorderLayout.CENTER);
        
        lblLastPhoto = new JLabel("Last Photo");
        scrollPane_4.setViewportView(lblLastPhoto);
        
        JPanel photoPanel = new JPanel();
        tabbedPane.addTab("Photo", null, photoPanel, null);
        photoPanel.setLayout(new BorderLayout(0, 0));
        
        JScrollPane scrollPane_3 = new JScrollPane();
        photoPanel.add(scrollPane_3, BorderLayout.CENTER);
        
        JLabel lblPicture = new JLabel("Picture");
        lblPicture.setHorizontalAlignment(SwingConstants.CENTER);
        scrollPane_3.setViewportView(lblPicture);
        
        JPanel heartbeatPanel = new JPanel();
        tabbedPane.addTab("Heatbeats", null, heartbeatPanel, null);
        
        JScrollPane scrollPane_2 = new JScrollPane();
        heartbeatPanel.add(scrollPane_2);
        
        heartbeatTable = new JTable();
        scrollPane_2.setViewportView(heartbeatTable);
        
        JPanel Radios = new JPanel();
        tabbedPane.addTab("Radios", null, Radios, null);
        Radios.setLayout(new BorderLayout(0, 0));
        
        JScrollPane scrollPane_1 = new JScrollPane();
        Radios.add(scrollPane_1);
        
        radioTable = new JTable();
        scrollPane_1.setViewportView(radioTable);
        
        JPanel infoMsgPanel = new JPanel();
        tabbedPane.addTab("Messages", null, infoMsgPanel, null);
        infoMsgPanel.setLayout(new BorderLayout(0, 0));
        
        JScrollPane scrollPane_5 = new JScrollPane();
        infoMsgPanel.add(scrollPane_5, BorderLayout.CENTER);
        
        infoTextArea = new JTextArea();
        infoTextArea.setEditable(false);
        scrollPane_5.setViewportView(infoTextArea);
        
    }
    
    public JFrame getFrame() {
        return frame;
    }

    public JTable getDetectionTable() {
        return detectionTable;
    }

    
    public JTable getRadioTable() {
        return radioTable;
    }

    
    public JTable getHeartbeatTable() {
        return heartbeatTable;
    }
    
    public JLabel getLastPhotoLabel() {
        return lblLastPhoto;
    }

    
    public JTextArea getInfoTextArea() {
        return infoTextArea;
    }
    
}
