

let datalink = seisplotjs.datalink

//let wp = require('seisplotjs-waveformplot');
// this global comes from the seisplotjs_waveformplot standalone js
let wp = seisplotjs.waveformplot;
let d3 = seisplotjs.d3;
let moment = seisplotjs.moment;

let net = 'CO';
let staList = ['3605', 'PI01', 'PI03', 'PI04', 'PI06', 'PI07', 'PI99'];
d3.select('#stationChoice')
  .selectAll("option")
  .data(staList)
  .enter()
    .append("option")
    .text(function(d) {return d;});

let timerInProgress = false;
let clockOffset = 0; // should get from server somehow
let duration = 300;
let maxSteps = -1; // max num of ticks of the timer before stopping, for debugin
let timeWindow = seisplotjs.fdsndataselect.calcStartEndDates(null, null, duration, clockOffset);
let protocol = 'http:';
if ("https:" == document.location.protocol) {
  protocol = 'https:'
}
let wsProtocol = 'ws:';
if (protocol == 'https:') {
  wsProtocol = 'wss:';
}


//
// Note: currently rtserve.iris does not support wss, and so this will
// not work from https pages as you cannot use non-encrypted (ws)
// loaded from a https web page
//
const IRIS_HOST = "rtserve.iris.washington.edu";
const INTERNAL_HOST = "dragrace.seis.sc.edu";
const INTERNAL_PORT = 6383;
const INTERNAL_PATH = '/datalink';
const EXTERNAL_HOST = "www.seis.sc.edu";
const EXTERNAL_PORT = 80;
const EXTERNAL_PATH = '/dragracews/datalink';
let host = EXTERNAL_HOST;
let port = EXTERNAL_PORT;
let path = EXTERNAL_PATH;

    //PI status color change with  differences in maxacc packet time
    //const StrugDur = moment.duration(3 'minutes');
    //const DeadDur = moment.duration(6 'minutes');
    const StrugDur = moment.duration(10, 'seconds');
    const DeadDur = moment.duration(20, 'seconds');

//host="127.0.0.1";
//port=6382;

let datalinkUrl = wsProtocol+"//"+host+(port==80?'':':'+port)+path;
console.log("URL: "+datalinkUrl);
let writeDatalinkUrl = wsProtocol+"//"+INTERNAL_HOST+(INTERNAL_PORT==80?'':':'+INTERNAL_PORT)+INTERNAL_PATH;

d3.selectAll('.textHost').text(host);

let accelMaxValues = new Map();
let prevAccelValue = new Map();
let dlConn = null;
let allSeisPlots = new Map();
let allTraces = new Map();
let markers = [];
let svgParent = wp.d3.select('div.realtime');
let margin = {top: 20, right: 20, bottom: 50, left: 60};

let paused = false;
let stopped = false;
let numSteps = 0;




//go into sidebar buttons and deactivate
let togglebutton = function(heatdiv) {
  wp.d3.select("div.sidebar").selectAll("div").select(".panel").style("display","none");
  wp.d3.select("div.sidebar").selectAll("div").select("button").classed("active", false);

    heatdiv.select("button").classed("active", true);
    heatdiv.select(".panel").style("display","block");
};
wp.d3.select("div.class1 button.heatcollapse").on("click", function(d) {
  console.log("buttonclick "+d);
   let heatdiv = wp.d3.select("div.class1");
   togglebutton(heatdiv);


});
wp.d3.select("div.class2 button.heatcollapse").on("click", function(d) {
  console.log("buttonclick "+d);
   let heatdiv = wp.d3.select("div.class2");
   togglebutton(heatdiv);

});

//end trying to make heat buttons work
wp.d3.select("button#load").on("click", function(d) {
  let selectEl = document.getElementById("stationChoice");
  let selectedIndex = selectEl.selectedIndex;
  staCode = selectEl.options[selectedIndex].value;

  console.log("Load..."+staCode);
  doplot(staCode);
});

let packetCount = 0;

let handleMSeed = function(miniseed) {
  let codes = miniseed.codes();
  let seismogram = wp.miniseed.createSeismogram([miniseed]);
  if (allSeisPlots.has(codes)) {
    if (allTraces.has(codes)) {
      const oldTrace = allTraces.get(codes);
      oldTrace.append(seismogram);
      const littleBitLarger = {'start': moment.utc(timeWindow.start).subtract(60, 'second'),
                              'end': moment.utc(timeWindow.end).add(180, 'second')};
      const newTrace = oldTrace.trim(littleBitLarger);
      if (newTrace) {
        allTraces.set(codes, newTrace);
        allSeisPlots.get(codes).replace(oldTrace, newTrace);
        allSeisPlots.get(codes).calcScaleDomain();
      } else {
        // trim removed all data, nothing left in window
        allTraces.delete(codes);
        allSeisPlots.get(codes).remove(oldTrace);
      }
    } else {
      let newTrace = new seisplotjs.model.Trace(seismogram);
      allSeisPlots.get(codes).append(newTrace);
    }
//      allSeisPlots.get(codes).trim(timeWindow);
  } else {
    svgParent.select("p.waitingondata").remove();
    let seisDiv = svgParent.append('div').attr('class', codes);
//    seisDiv.append('p').text(codes);
    let plotDiv = seisDiv.append('div').attr('class', 'realtime');
    plotDiv.style("position", "relative");
    plotDiv.style("width", "100%");
    plotDiv.style("height", "150px");
    let trace = new seisplotjs.model.Trace(seismogram);
    let seisPlotConfig = new wp.SeismographConfig();
    seisPlotConfig.xSublabel = codes;
    seisPlotConfig.margin = margin ;
    seisPlotConfig.maxHeight = 200 ;
    let seisPlot = new wp.CanvasSeismograph(plotDiv, seisPlotConfig, [trace], timeWindow.start, timeWindow.end);
    seisPlot.svg.classed('realtimePlot', true).classed('overlayPlot', false)
    seisPlot.disableWheelZoom();
    seisPlot.setHeight(150);
    seisPlot.appendMarkers(markers);
    seisPlot.draw();
    allSeisPlots.set(codes, seisPlot);
    allTraces.set(codes, trace)
  }
}

let dlMSeedCallback = function(dlPacket) {
  handleMSeed(dlPacket.miniseed);
};

let dlTriggerCallback = function(dlPacket) {
  // turn all into string
  let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
  d3.select("div.triggers").append("p").text(`Trigger: ${s}`);
  let trig = JSON.parse(s)
  displayName = trig.dutyOfficer ? trig.dutyOfficer : "AutoTrigger";
  let startMark = { markertype: 'predicted', name: "Start"+displayName, time: moment.utc(trig.time).subtract(15, 'seconds') };
  markers.push(startMark);
  //Gabby & Emma tried to make two trigger flags appear at 3 seconds apart
  let endMark = { markertype: 'predicted', name: displayName, time: moment.utc(trig.time) };
  markers.push(endMark);
  for (let sp of allSeisPlots.values()) {
    sp.appendMarkers( [ startMark,endMark ]);
  }

};


// update equilizer, but only as fast as the browser can handle redraws
let drawEquilizer = function() {
  d3.select("div.equalizer").selectAll(`span`).classed('struggling', false).classed('good', false);
  accelMaxValues.forEach((dlPacket, streamId, map) => {
    // turn all into string
    let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
    let maxacc = JSON.parse(s);
    let scaleAcc = Math.round(100*maxacc.accel/2); // 2g = 100px


    if ( ! prevAccelValue[streamId] || prevAccelValue[streamId] !== scaleAcc) {
      // only update if the value changed
      prevAccelValue[streamId] = scaleAcc;
      let staSpan = d3.select("div.equalizer").select(`span.${maxacc.station}`);
      let color = staSpan.style("background-color");
	    console.log(`color: ${color}`);
      if (color == 'pink') {
        color = 'yellow';
      } else {
	color = 'pink';
      }
      staSpan.select("div").transition().style("height", `${scaleAcc}px`).style("background-color", color);;
    }

    let now = moment.utc();
    let packtime = moment.utc(maxacc.time);
      //var duration = moment.duration(now,diff(packtime));

//determine time intervals and associate class names

    let statpi = d3.select("div.piStatus");

    if(now.subtract(StrugDur).isBefore(packtime)){
      statpi.select(`span.${maxacc.station}`).classed('struggling', false).classed('good', true);
    } else if(now.subtract(DeadDur).isBefore(packtime)){
      statpi.select(`span.${maxacc.station}`).classed('struggling', true).classed('good', false);
    } else {
      statpi.select(`span.${maxacc.station}`).classed('struggling', false).classed('good', false);
  }


  });
  // lather, rinse, repeat...
  window.requestAnimationFrame(drawEquilizer);
};
// start drawing:
window.requestAnimationFrame(drawEquilizer);

let dlMaxAccelerationCallback = function(dlPacket) {
    accelMaxValues.set(dlPacket.streamId, dlPacket);
}

let dlPacketPeakCallback = function(dlPacket) {
    // turn all into string
    let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
    let maxacc = JSON.parse(s);
    let scaleAcc = Math.round(100*maxacc.accel/2); // 2g = 100px
    let staSpan = d3.selectAll("div.equalizer").selectAll(`span.${maxacc.station}`);
    staSpan.selectAll("div").transition().style("height", `${scaleAcc}px`).style("background-color", "yellow");
    //console.log(`maxacc: ${maxacc.station}  ${maxacc.accel}  ${scaleAcc}`)
}

let dlCallback = function(dlPacket) {
  if (dlPacket.streamId.endsWith("MSEED")) {
    dlMSeedCallback(dlPacket);
  } else if (dlPacket.streamId.endsWith("TRIG")) {
    dlTriggerCallback(dlPacket);
  } else if (dlPacket.streamId.endsWith("MAXACC")) {
    dlMaxAccelerationCallback(dlPacket);
  } else if (dlPacket.streamId.endsWith("PEAK")) {
    dlPacketPeakCallback(dlPacket);
  }
};

let doDatalinkConnect = function() {
  let dlPromise = null;
  if ( ! dlConn) {
    console.log(`doDatalinkConnect dlConn is null`);
    dlConn = new datalink.DataLinkConnection(datalinkUrl, dlCallback, errorFn);
    dlPromise = dlConn.connect();
  } else {
    console.log(`doDatalinkConnect dlConn exists, reuse`);
    try {
      if (dlConn.isConnected()) {
        dlConn.endStream();
        dlPromise = new seisplotjs.RSVP.Promise(function(resolve, reject) {
          resolve(`reuse connection...${dlConn.serverId}`);
        });
      } else {
        dlPromise = dlConn.connect();
      }
    } catch (err) {
      dlConn = new datalink.DataLinkConnection(datalinkUrl, dlCallback, errorFn);
      dlPromise = dlConn.connect();
    }
  }
  dlPromise.catch(err => {
    d3.select("div.triggers").append("p").text(`Unable to connect: ${err}`);
    dlConn.close();
    return null;
  }).then(serverId => {
    d3.select("div.triggers").append("p").text(`Connect to ${serverId}`);
    return dlConn.awaitDLCommand("MATCH", `(${staCode}.*\.HNZ/MSEED)|(.*/MTRIG)|(.*/MAXACC)`);
  }).then(response => {
    d3.select("div.triggers").append("p").text(`MATCH response: ${response}`);
    return dlConn.awaitDLCommand(`POSITION AFTER ${datalink.momentToHPTime(timeWindow.start)}`);
  }).then(response => {
    d3.select("div.triggers").append("p").text(`POSITION response: ${response}`);
    dlConn.stream();
  });
  return dlPromise;
}

doplot = function(sta) {
  if (dlConn && dlConn.isConnected()) {dlConn.endStream();}
  console.log(`do plot, timeWindow: ${timeWindow.start} ${timeWindow.end}  ${timeWindow.start.valueOf()}`);

  d3.selectAll('.textStaCode').text(sta);
  d3.selectAll('.textNetCode').text(net);
  if (sta !== '3605') {
    net = "XX";
  } else {
    net = "CO";
  }

  svgParent.selectAll("*").remove();
  if (wsProtocol == 'wss:' && host == IRIS_HOST) {
    svgParent.append("h3").attr('class', 'waitingondata').text("IRIS currently does not support connections from https pages, try from a http page instead.");
  } else {
    svgParent.append("p").attr('class', 'waitingondata').text("waiting on first data");
  }

  doDisconnect(false);
  doPause(false);
};

wp.d3.select("button#peak").on("click", function(d) {
  let trigtime = moment.utc()
  let dutyOfficer = document.getElementsByName('dutyofficer')[0].value;
  dutyOfficer = dutyOfficer.replace(/\W/, '');
  dutyOfficer = dutyOfficer.replace(/_/, '');
  dutyOfficer = dutyOfficer.toUpperCase();
  let trigger = {
        "type": "manual",
        "dutyOfficer": dutyOfficer,
        "time": trigtime.toISOString(),
        "creation": trigtime.toISOString(),
        "override": {
            "modtime": trigtime.toISOString(),
            "value": "enable"
        }
    };
  let dlTriggerConn = new datalink.DataLinkConnection(writeDatalinkUrl, dlTriggerCallback, errorFn);
  dlTriggerConn.connect().then(serverId => {
    d3.select("div.triggers").append("p").text(`Connect to ${serverId}`);
    d3.select("div.triggers").append("p").text(`Send Trigger: ${JSON.stringify(trigger)}`);
    return dlTriggerConn.writeAck(`XX_MANUAL_TRIG_${dutyOfficer}/MTRIG`,
      trigtime,
      trigtime,
      datalink.stringToUnit8Array(JSON.stringify(trigger)));
  }).then(ack => {
    dlTriggerConn.close();
    d3.select("div.triggers").append("p").text(`Send trigger ack: ${ack}`);
  });
});

wp.d3.select("button#trigger").on("click", function(d) {
  let trigtime = moment.utc()
  let dutyOfficer = document.getElementsByName('dutyofficer')[0].value;
  dutyOfficer = dutyOfficer.replace(/\W/, '');
  dutyOfficer = dutyOfficer.replace(/_/, '');
  dutyOfficer = dutyOfficer.toUpperCase();
  let trigger = {
        "type": "manual",
        "dutyOfficer": dutyOfficer,
        "time": trigtime.toISOString(),
        "creation": trigtime.toISOString(),
        "override": {
            "modtime": trigtime.toISOString(),
            "value": "enable"
        }
    };
  let dlTriggerConn = new datalink.DataLinkConnection(writeDatalinkUrl, dlTriggerCallback, errorFn);
  dlTriggerConn.connect().then(serverId => {
    d3.select("div.triggers").append("p").text(`Connect to ${serverId}`);
    d3.select("div.triggers").append("p").text(`Send Trigger: ${JSON.stringify(trigger)}`);
    return dlTriggerConn.writeAck(`XX_MANUAL_TRIG_${dutyOfficer}/MTRIG`,
      trigtime,
      trigtime,
      datalink.stringToUnit8Array(JSON.stringify(trigger)));
  }).then(ack => {
    dlTriggerConn.close();
    d3.select("div.triggers").append("p").text(`Send trigger ack: ${ack}`);
  });
});

wp.d3.select("button#pause").on("click", function(d) {
  doPause( ! paused);
});

wp.d3.select("button#disconnect").on("click", function(d) {
  doDisconnect( ! stopped);
});

let doPause = function(value) {
  console.log("Pause..."+paused+" -> "+value);
  paused = value;
  if (paused) {
    wp.d3.select("button#pause").text("Play");
  } else {
    wp.d3.select("button#pause").text("Pause");
  }
}

let doDisconnect = function(value) {
  console.log("disconnect..."+stopped+" -> "+value);
  stopped = value;
  if (stopped) {
    if (dlConn) {dlConn.close();}
    wp.d3.select("button#disconnect").text("Reconnect");
  } else {
    doDatalinkConnect().then( () => {
      wp.d3.select("button#disconnect").text("Disconnect");
    });
  }
}

let timerInterval = (timeWindow.end.valueOf()-timeWindow.start.valueOf())/
                    (parseInt(svgParent.style("width"))-margin.left-margin.right);
while (timerInterval < 100) { timerInterval *= 2;}
let timer = wp.d3.interval(function(elapsed) {
  if ( paused || timerInProgress) {
    return;
  }
  timerInProgress = true;
  if ( allSeisPlots.size > 1) {
    numSteps++;
    if (maxSteps > 0 && numSteps > maxSteps ) {
      console.log("quit after max steps: "+maxSteps);
      timer.stop();
      dlConn.close();
    }
  }
  timeWindow = wp.calcStartEndDates(null, null, duration, clockOffset);
  window.requestAnimationFrame(timestamp => {
    allSeisPlots.forEach(function(value, key) {
        value.setPlotStartEnd(timeWindow.start, timeWindow.end);
    });
    timerInProgress = false
  });

}, timerInterval);


function makeString(dataView , offset , length )  {
  let out = "";
  for (let i=offset; i<offset+length; i++) {
    let charCode = dataView.getUint8(i);
    if (charCode > 31) {
      out += String.fromCharCode(charCode);
    }
  }
  return out.trim();
}

let errorFn = function(error) {
  console.log("error: "+error);
  d3.select("div.triggers").append("p").text(`Error: ${error}`);
  doDisconnect(true);
};
