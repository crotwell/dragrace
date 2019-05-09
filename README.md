#dragrace
Using an MMA8451 accelerometer and a Raspberry Pi to record ground shaking at a drag race.

# Year 2

Year two switched from XBee to wired internet as the throughput of the XBee was not quite enough to handle the data volume. The python running on the Pis now sends
data directly to the the IRIS [ringserver](https://github.com/iris-edu/ringserver)
via a [datalink](https://github.com/iris-edu/libdali) connection, optionally sending
just the max acceleration 4 times a second instead of the full 3 channel 200 sample per second data. A web based "duty seismologist" page for manually triggering of
the creation of max acceleration results for individual races and viewing of them.
The viewing of the raw data via an "equalizer" display was a big hit.

---

# Year 1

# dragrace
Using an MMA8451 accelerometer, Raspberry Pi and XBee to record ground shaking at drag races.

# Sensor Node

The sensor node is a Raspberry Pi connected to a MMA8451 accelerometer breakout board from [Adafruit](https://www.adafruit.com/product/2019) and a XBee series 2 radio via a [Sparkfun](https://www.sparkfun.com/products/11697) XBee Explorer Dongle.
This also makes use of a [modified](https://github.com/crotwell/Adafruit_CircuitPython_MMA8451) version of the MMA8451 python software from [Adafruit_CircuitPython](https://github.com/adafruit/Adafruit_CircuitPython_MMA8451) to enable access to the FIFO buffer.
This uses [python3](https://www.python.org/).

# Central Archive

The central archive is a laptop with the controller node XBee controlled by a java application that receives the data, transforms it from the raw byte array into Miniseed and writes to a directory. A IRIS [ringserver](https://github.com/iris-edu/ringserver) scans the directory, reads in the miniseed and makes it available over http.
This was cobbled together from some old code relating to timing of horses the cross country portion of horse trials. That never actually worked, but provided a lot of the code that was needed for this, reuse, reuse, reuse, and hence for the oddly named package.
It is built using [Gradle](http://gradle.org).

# www Status

A collection of web pages with javascript allow viewing of the data in a web browser using the seedlink websocket available in the embedded http service within ringserver. These allow viewing of a past hour of data or realtime data as it arrives. This uses the [seisplotjs 2.0](https://github.com/crotwell/seisplotjs) javascript library to parse and plot the waveform data.

# Future work

Currently timing is a weak link, as it simply the clock on the Raspberry Pi, hopefully synced prior to deployment via NTP over the wifi connection. Improving this to either allow setting the Pi's clock from the central archiver via the XBee, or a hardware clock would help with timing.

Better web status pages would also help a lot.
