#!/usr/bin/python3

# Simple demo of fifo mode on the MMA8451.
# Author: Philip Crotwell
import time
import queue
import threading
from datetime import datetime
import sys, os
from pathlib import Path
#import logging
#logging.basicConfig(filename='xbee.log',level=logging.DEBUG)

import board
import busio

import adafruit_mma8451
import RPi.GPIO as GPIO
from digi.xbee.devices import XBeeDevice
#from digi.xbee.devices import ZigBeeDevice
from digi.xbee.models.address import XBee16BitAddress
from digi.xbee.exception import TimeoutException

xbeeMutex = threading.Lock()

#baud = 9600
#baud = 57600
baud = 115200
CONTROLLER_ADDR = 0x00

pin = 18  # GPIO interrupt
#MAX_SAMPLES = 2000
MAX_SAMPLES = -1
#MAX_SAMPLES = 1



MAC_TTY = "/dev/tty.usbserial-DN04R2D1"
PI_S_TTY = "/dev/ttyS0"
PI_USB_TTY = "/dev/ttyUSB0"

mac_tty_file = Path(MAC_TTY)
pi_usb_tty_file = Path(PI_USB_TTY)
pi_s_tty_file = Path(PI_S_TTY)
port = ""
if mac_tty_file.exists():
    port = MAC_TTY
elif pi_usb_tty_file.exists():
    port = PI_USB_TTY
elif pi_s_tty_file.exists():
    port = PI_S_TTY
else:
    print("no tty file found")
    sys.exit(1)

# Initialize I2C bus.
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize MMA8451 module.
sensor = adafruit_mma8451.MMA8451(i2c)
# Optionally change the address if it's not the default:
#sensor = adafruit_mma8451.MMA8451(i2c, address=0x1C)

# Optionally change the range from its default of +/-4G:
sensor.range = adafruit_mma8451.RANGE_2G  # +/- 2G
#sensor.range = adafruit_mma8451.RANGE_4G  # +/- 4G (default)
#sensor.range = adafruit_mma8451.RANGE_8G  # +/- 8G

# Optionally change the data rate from its default of 800hz:
#sensor.data_rate = adafruit_mma8451.DATARATE_800HZ  #  800Hz (default)
#sensor.data_rate = adafruit_mma8451.DATARATE_400HZ  #  400Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_200HZ  #  200Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_100HZ  #  100Hz
sensor.data_rate = adafruit_mma8451.DATARATE_50HZ   #   50Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_12_5HZ # 12.5Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_6_25HZ # 6.25Hz
#sensor.data_rate = adafruit_mma8451.DATARATE_1_56HZ # 1.56Hz

def getSps():
    sps = 1
    if sensor.data_rate == adafruit_mma8451.DATARATE_200HZ:
        sps = 200
    elif sensor.data_rate == adafruit_mma8451.DATARATE_100HZ:
        sps = 100
    elif sensor.data_rate == adafruit_mma8451.DATARATE_50HZ:
        sps = 50
    return sps

def getGain():
    gain = 0
    if sensor.range == adafruit_mma8451.RANGE_2G:
        gain = 2
    elif sensor.range == adafruit_mma8451.RANGE_4G:
        gain = 4
    elif sensor.range == adafruit_mma8451.RANGE_8G:
        gain = 8
    return gain


before = time.perf_counter()
after = before
totalSamples = 0
sentSamples = 0
loops = 0
keepGoing = True
curFile = None
curFilename = None
startACQ = False
sps = 0
gain = 0

def dataCallback(now, status, samplesAvail, data):
    global totalSamples
    global keepGoing
    global before
    global pin
    item = now, status, samplesAvail, data
    dataQueue.put(item)
    totalSamples += samplesAvail
    if (MAX_SAMPLES != -1 and totalSamples > MAX_SAMPLES):
        after = time.perf_counter()
        delta = after-before
        print("time take for {0:d} loops is {1:3.2f}, {2:d} samples at {3:3.2f} sps, nomSps={4:d}".format(loops, delta, totalSamples, (totalSamples-1)/delta, getSps()))
        sensor.reset()
        GPIO.remove_event_detect(pin)
        keepGoing = False

def worker():
    global keepGoing
    global startACQ
    global dataQueue
    global infoQueue
    while keepGoing:
        try:
            if not infoQueue.empty():
                doSendInfoPacket(infoQueue.get(timeout=2))
                infoQueue.task_done()
            item = dataQueue.get(timeout=2)
            if item is None or not keepGoing:
                print("Worker exiting")
                dataQueue.task_done()
                break
            now, status, samplesAvail, data = item
            try:
                do_work(now, status, samplesAvail, data)
                dataQueue.task_done
            except TimeoutException as err:
                # try once more?
                #do_work(now, status, samplesAvail, data)
                print("TimeoutException sending packet")
                dataQueue.task_done()
        except queue.Empty:
            print("no data in queue??? startACQ={0:b}".format(startACQ))
    print("Worker exited")


def do_work(now, status, samplesAvail, data):
    global xbeeMutex
    global startACQ
    global totalSamples
    global sentSamples
    global loops
    global before
    global pin
    global keepGoing
    global after
    global sps
    loops += 1

    if status >= 128:
        print("overflow at loops={0:d}".format(loops))
    #preMsg = ""
    #if status >= 128:
    #    preMsg = "Overflow "
    #if status & 0x40 > 0:
    #    preMsg += "Watermark "
    #print("{0} load {1:d} samples: {2:b} {3:b}".format(preMsg, samplesAvail, (status & 128)>0, (status & 64)>0))
    dataOffset = 12
    dataPacket = bytearray(len(data)+dataOffset)
    dataPacket[0] = ord('A')
    dataPacket[1] = samplesAvail & 0xff;
    dataPacket[2:4] = now.year.to_bytes(2, byteorder='big')
    dataPacket[4:6] = now.timetuple().tm_yday.to_bytes(2, byteorder='big')
    dataPacket[6] = now.hour
    dataPacket[7] = now.minute
    dataPacket[8] = now.second
    dataPacket[9:11] = int(round(now.microsecond/1000)).to_bytes(2, byteorder='big')
    dataPacket[11] = sps
    dataPacket[dataOffset:dataOffset+len(data)] = data
    try:
        with xbeeMutex:
            device, remote = getXBee()
            if (device is not None and remote is not None and startACQ):
                    device.send_data(remote, dataPacket)
            elif not startACQ:
                print("no startACQ")
            else:
                print("xbee device or remote is None, skipping send packet")
    except Exception as eee:
        print("unable to send: {0}".format(eee))
    sentSamples += samplesAvail
    #if sentSamples % 6000 == 0:
    if loops % 18 == 0:
        print("sent data async samplesSent={0:d} of {1:d} {2}".format(sentSamples, totalSamples, now.strftime("%Y-%m-%d %H:%M:%S")))
        #print("{0:d} {1:d} {2:d}:{3:d}:{4:d}.{5:3.3f}    sps={6:d}  npts={7:d}".format(now.year, now.timetuple().tm_yday, now.hour, now.minute, now.second, now.microsecond/1000, sps, samplesAvail));
        #xData, yData, zData = sensor.demux(data)
        #for i in range(len(xData)):
        #    print("  {0:d} {1:d} {2:d}".format(xData[i], yData[i], zData[i]))
    if sentSamples > 1000000:
        sentSamples = 0
    sendToFile(now, dataPacket)

def getXBee():
    global port
    global baud
    global device, remote
    if (device is None):
        device, remote = initXBee(port, baud)
    if remote is None:
        controller16Addr = XBee16BitAddress.COORDINATOR_ADDRESS
        xnet = device.get_network()
        remote = xnet.get_device_by_16(controller16Addr)
    return device, remote

def sendToFile(now, dataPacket):
    global curFile
    global curFilename
    filename = now.strftime("data_%Y-%m-%d_%H")
    if curFilename != filename:
        if curFile != None:
            curFile.close()
        curFile = open(filename, "ab")
    curFile.write(dataPacket)

def xbee_status_callback(status):
    print("Modem status: %s" % status.description)

def xbee_received_callback(xbee_message):
    global startACQ
    global dataQueue
    address = xbee_message.remote_device.get_64bit_addr()
    data = xbee_message.data.decode("utf8")
    if data == "stop":
        startACQ = False
        sendInfoPacket("stopped")
    elif data == "start":
        startACQ = True
        sendInfoPacket("started")

    elif data == "status":
        if startACQ:
            sendInfoPacket("started")
        else:
            sendInfoPacket("stopped")
    elif data == "gain":
        sendInfoPacket("gain={0:d}".format(gain))
    elif data == "sps":
        sendInfoPacket("sps={0:d}".format(sps))
    elif data == "queue":
        sendInfoPacket("queue={0:d}".format(dataQueue.qsize()))
    elif data == "flush":
        dataQueue.clear()
        sendInfoPacket("flushed")
    print("Received data from %s: '%s'" % (address, data))

def sendInfoPacket(info):
    infoQueue.put(info)

def doSendInfoPacket(info):
    global xbeeMutex
    with xbeeMutex:
        device, remote = getXBee()
        if remote is not None:
            msg = "I{0} {1}".format(device.get_node_id(), info)
            bInfo = msg.encode('utf-8')
            device.send_data(remote, bInfo)
        else:
            print("can't send, remote is None")

def initXBee(port, baud):
    global CONTROLLER_ADDR
    print("Init XBee at {0}, {1:d}".format(port, baud))
    #device = ZigBeeDevice(port, baud)
    device = XBeeDevice(port, baud)
    device.open()
    device.add_modem_status_received_callback(xbee_status_callback)
    device.add_data_received_callback(xbee_received_callback)
    xnet = device.get_network()
    xnet.set_discovery_timeout(5)
    xnet.start_discovery_process()
    while xnet.is_discovery_running():
        time.sleep(0.5)
    controller16Addr = XBee16BitAddress.COORDINATOR_ADDRESS
    remote_device = xnet.get_device_by_16(controller16Addr)
    if remote_device is None:
        print("Could not find the remote device {0}".format(controller16Addr))
    print("init, nodeId= {0}".format(device.get_node_id()))
    return device, remote_device

dataQueue = queue.Queue()
infoQueue = queue.Queue()
sendThread = threading.Thread(target=worker)
sendThread.start()

device = None
remote = None

try:
    before = time.perf_counter()
    sensor.enableFifoBuffer(30, pin, dataCallback)
    sps = getSps()
    gain = getGain()

    if device == None:
        try:
            with xbeeMutex:
                device, remote = getXBee()
        except ValueError as err:
            print("Unable to init XBee at {0} {1:d}: {2}".format(port, baud, err))

    # Main loop to print the acceleration and orientation every second.
    while keepGoing:
        line = sys.stdin.readline()
        if (line.startswith("q")):
            keepGoing = False
            break
        time.sleep(0.1)
except ValueError as err:
    print("   error: {0}".format(err))
except RuntimeError as err:
    print("Other Error: {0}".format(err))
    os._exit(1)  # harsh but must use os._exit as other threads keep alive

print("Quiting")
if sensor is not None:
    print("reset sensor")
    sensor.reset()
    print("remove gpio interrupt pin")
    GPIO.remove_event_detect(pin)


time.sleep(0.1)
print("join queue to wait for xbee worker to finish")
#dataQueue.join() # wait until any remaining data is sent
if device is not None:
    print("close xbee")
    device.close()
