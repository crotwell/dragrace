
//let seedlink = require('seisplotjs-seedlink');
// this global comes from the seisplotjs_seedlink standalone js
let seedlink = seisplotjs.seedlink

//let wp = require('seisplotjs-waveformplot');
// this global comes from the seisplotjs_waveformplot standalone js
let wp = seisplotjs.waveformplot;
let d3 = seisplotjs.d3;

let net = 'CO';
let staList = ['XB01', 'XB03', 'XB05', 'XB08', 'XB10'];
d3.select('#stationChoice')
  .selectAll("option")
  .data(staList)
  .enter()
    .append("option")
    .text(function(d) {return d;});

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
let IRIS_HOST = "rtserve.iris.washington.edu";
let EEYORE_HOST = "eeyore.seis.sc.edu";
let EEYORE_PORT = 6383;
let host = IRIS_HOST;
let port = 80;
host='localhost';
port=8081;
let seedlinkUrl = wsProtocol+"//"+host+(port==80?'':':'+port)+'/seedlink';
console.log("URL: "+seedlinkUrl);


d3.selectAll('.textHost').text(host);

let slConn = null;
let allSeisPlots = new Map();
let svgParent = wp.d3.select('div.realtime');
let margin = {top: 20, right: 20, bottom: 50, left: 60};

let paused = false;
let stopped = false;
let numSteps = 0;

wp.d3.select("button#load").on("click", function(d) {
  var selectEl = document.getElementById("stationChoice");
  var selectedIndex = selectEl.selectedIndex;
  var staCode = selectEl.options[selectedIndex].value;

  console.log("Load..."+staCode);
  doplot(staCode);
});

doplot = function(sta) {
  if (slConn) {slConn.close(); slConn = null;}
  doDisconnect(false);
  doPause(false);
  console.log("do plot, timeWindow: "+timeWindow.start+" "+timeWindow.end);

  d3.selectAll('.textStaCode').text(sta);
  d3.selectAll('.textNetCode').text(net);

  let config = [
    'STATION '+sta+' '+net,
    'SELECT 00HH?.D',
    'STATION '+sta+' '+net,
    'SELECT 00HN?.D' ];

  console.log("before select");
  svgParent.selectAll("*").remove();
  if (wsProtocol == 'wss:' && host == IRIS_HOST) {
    svgParent.append("h3").attr('class', 'waitingondata').text("IRIS currently does not support connections from https pages, try from a http page instead.");
  } else {
    svgParent.append("p").attr('class', 'waitingondata').text("waiting on first data");
  }


  let callbackFn = function(slPacket) {
    let codes = slPacket.miniseed.codes();
    console.log("seedlink: seq="+slPacket.sequence+" "+codes);
    let seismogram = wp.miniseed.createSeismogram([slPacket.miniseed]);
    if (allSeisPlots.get(codes)) {
      allSeisPlots.get(codes).trim(timeWindow);
      allSeisPlots.get(codes).append(seismogram);
    } else {
      svgParent.select("p.waitingondata").remove();
      let seisDiv = svgParent.append('div').attr('class', codes);
  //    seisDiv.append('p').text(codes);
      let plotDiv = seisDiv.append('div').attr('class', 'realtimePlot');
      let seisPlot = new wp.Seismograph(plotDiv, [seismogram], timeWindow.start, timeWindow.end);
      seisPlot.svg.classed('realtimePlot', true).classed('overlayPlot', false)
      seisPlot.disableWheelZoom();
      seisPlot.setXSublabel(codes);
      seisPlot.setMargin(margin );
      seisPlot.draw();
      allSeisPlots.set(slPacket.miniseed.codes(), seisPlot);
    }
  }

  slConn = new seedlink.SeedlinkConnection(seedlinkUrl, config, callbackFn, errorFn);
  slConn.setTimeCommand(timeWindow.start);
  slConn.connect();
};


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
if (timerInterval < 200) { timerInterval = 200;}
console.log("start time with interval "+timerInterval);
let timer = wp.d3.interval(function(elapsed) {
  if ( paused) {
    return;
  }
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
  allSeisPlots.forEach(function(value, key) {
      value.setPlotStartEnd(timeWindow.start, timeWindow.end);
  });
}, timerInterval);

let errorFn = function(error) {
  console.log("error: "+error);
  svgParent.select("p").text("Error: "+error);
};
