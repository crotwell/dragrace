

//let seedlink = require('seisplotjs-seedlink');
// this global comes from the seisplotjs_seedlink standalone js
let seedlink = seisplotjs.seedlink
let datalink = seisplotjs.datalink

//let wp = require('seisplotjs-waveformplot');
// this global comes from the seisplotjs_waveformplot standalone js
let wp = seisplotjs.waveformplot;
let d3 = seisplotjs.d3;
let moment = seisplotjs.moment;

let net = 'CO';
let staList = ['3605', 'PI01', 'PI04'];
d3.select('#stationChoice')
  .selectAll("option")
  .data(staList)
  .enter()
    .append("option")
    .text(function(d) {return d;});

let timerInProgress = false;
let clockOffset = 0; // should get from server somehow
let duration = 120;
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
let IRIS_HOST = "rtserve.iris.washington.edu";
let EEYORE_HOST = "dragrace.seis.sc.edu";
let EEYORE_PORT = 6383;
let DRAGRACE_HOST = "dragrace.seis.sc.edu";
let DRAGRACE_PORT = 6383;
let host = DRAGRACE_HOST;
let port = DRAGRACE_PORT;
//host="127.0.0.1";
//port=6382;

let seedlinkUrl = wsProtocol+"//"+host+(port==80?'':':'+port)+'/seedlink';
console.log("URL: "+seedlinkUrl);

let datalinkUrl = wsProtocol+"//"+host+(port==80?'':':'+port)+'/datalink';


d3.selectAll('.textHost').text(host);


let slConn = null;
let allSeisPlots = new Map();
let allTraces = new Map();
let markers = [];
let svgParent = wp.d3.select('div.realtime');
let margin = {top: 20, right: 20, bottom: 50, left: 60};

let paused = false;
let stopped = false;
let numSteps = 0;

wp.d3.select("button#load").on("click", function(d) {
  let selectEl = document.getElementById("stationChoice");
  let selectedIndex = selectEl.selectedIndex;
  let staCode = selectEl.options[selectedIndex].value;

  console.log("Load..."+staCode);
  doplot(staCode);
});

let dlTriggerCallback = function(dlPacket) {
  // turn all into string
  let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
  d3.select("div.triggers").append("p").text(`Trigger: ${s}`);
  let trig = JSON.parse(s)
  displayName = trig.dutyOfficer ? trig.dutyOfficer : "AutoTrigger";
  let mark = { markertype: 'predicted', name: displayName, time: moment.utc(trig.time) };
  markers.push(mark);
  for (let sp of allSeisPlots.values()) {
    sp.appendMarkers( [ mark ]);
  }
};

doplot = function(sta) {
  if (slConn) {slConn.close(); slConn = null;}
  doDisconnect(false);
  doPause(false);
  console.log("do plot, timeWindow: "+timeWindow.start+" "+timeWindow.end);

  d3.selectAll('.textStaCode').text(sta);
  d3.selectAll('.textNetCode').text(net);
  if (sta !== '3605') {
    net = "XX";
  } else {
    net = "CO";
  }
  let config = [
    'STATION '+sta+' '+net,
    'SELECT 00HH?.D',
    'STATION '+sta+' '+net,
    'SELECT 00HN?.D' ];
  config = [
      'STATION '+sta+' '+net,
      'SELECT 00HNZ.D' ];

  console.log(`before select ${net}.${sta}`);
  svgParent.selectAll("*").remove();
  if (wsProtocol == 'wss:' && host == IRIS_HOST) {
    svgParent.append("h3").attr('class', 'waitingondata').text("IRIS currently does not support connections from https pages, try from a http page instead.");
  } else {
    svgParent.append("p").attr('class', 'waitingondata').text("waiting on first data");
  }


  let callbackFn = function(slPacket) {
    let codes = slPacket.miniseed.codes();
    //console.log("seedlink: seq="+slPacket.sequence+" "+codes);
    let seismogram = wp.miniseed.createSeismogram([slPacket.miniseed]);
    if (allSeisPlots.has(codes) && allTraces.has(codes)) {
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
        console.log(`All data removed from trace ${codes}`);
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
      allSeisPlots.set(slPacket.miniseed.codes(), seisPlot);
      allTraces.set(codes, trace)
    }
  }

  slConn = new seedlink.SeedlinkConnection(seedlinkUrl, config, callbackFn, errorFn);
  slConn.setTimeCommand(timeWindow.start);
  slConn.setOnClose( closeEvent => {
    console.log(`doplot: Received webSocket close: ${closeEvent.code} ${closeEvent.reason}`);
    stopped = true;
    wp.d3.select("button#disconnect").text("Reconnect");
  });
  slConn.connect();


  dlConn = new datalink.DataLinkConnection(datalinkUrl, dlTriggerCallback, errorFn);
  dlConn.connect().then(serverId => {
    d3.select("div.triggers").append("p").text(`Connect to ${serverId}`);
    return dlConn.awaitDLCommand("MATCH", ".*/MTRIG");
  }).then(response => {
    return dlConn.awaitDLCommand(`POSITION AFTER ${datalink.momentToHPTime(timeWindow.start)}`, null);
  }).then(response => {
    d3.select("div.triggers").append("p").text(`MATCH response: ${response}`);
    dlConn.stream();
  });
};


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
  let dlTriggerConn = new datalink.DataLinkConnection(datalinkUrl, dlTriggerCallback, errorFn);
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
    if (slConn) {slConn.close();}
    wp.d3.select("button#disconnect").text("Reconnect");
  } else {
    if (slConn) {slConn.connect();}
    wp.d3.select("button#disconnect").text("Disconnect");
  }
}

let timerInterval = (timeWindow.end.valueOf()-timeWindow.start.valueOf())/
                    (parseInt(svgParent.style("width"))-margin.left-margin.right);
                    console.log("start time with interval "+timerInterval);
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
      slConn.close();
    }
  }
  timeWindow = wp.calcStartEndDates(null, null, duration, clockOffset);
  //console.log("reset time window for "+timeWindow.start+" "+timeWindow.end );
  window.requestAnimationFrame(timestamp => {
    allSeisPlots.forEach(function(value, key) {
        value.setPlotStartEnd(timeWindow.start, timeWindow.end);
        //console.log(`${key} tw: ${value.xScale.domain()}  width: ${value.width}  xScale range: ${value.xScale.range()}`);
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
};
