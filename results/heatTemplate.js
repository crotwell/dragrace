//function and call on a refresh button



//let datalink = seisplotjs.datalink


//let wp = require('seisplotjs-waveformplot');
// this global comes from the seisplotjs_waveformplot standalone js
let wp = seisplotjs.waveformplot;
let d3 = seisplotjs.d3;
let moment = seisplotjs.moment;
let datalink = seisplotjs.datalink
let seisGraphMax = 0.5;


let accelMaxValues = new Map();
let prevAccelValue = new Map();
let dlConn = null;
let allSeisPlots = new Map();
let allTraces = new Map();
let markers = [];
let svgParent = wp.d3.select('div.realtime');
let margin = {top: 5, right: 20, bottom: 40, left: 60};
let needsRedraw = new Set();

let paused = false;
let stopped = false;
let numSteps = 0;

let clockOffset = 0; // should get from server somehow
let duration = 300;
let timeWindow = seisplotjs.fdsndataselect.calcStartEndDates(null, null, duration, clockOffset);


const EXTERNAL_HOST = "www.seis.sc.edu";
const EXTERNAL_PORT = 80;
const EXTERNAL_PATH = '/dragracews/datalink';
let host = EXTERNAL_HOST;
let port = EXTERNAL_PORT;
let path = EXTERNAL_PATH;


let liveequalizer = new Equalizer("div.liveequalizer");
console.log("created live equlizer");

let protocol = 'http:';
if ("https:" == document.location.protocol) {
  protocol = 'https:'
}
let wsProtocol = 'ws:';
if (protocol == 'https:') {
  wsProtocol = 'wss:';
}

let datalinkUrl = wsProtocol+"//"+host+(port==80?'':':'+port)+path;
console.log("URL: "+datalinkUrl);



let doDatalinkConnect = function() {
  let dlPromise = null;
  if (dlConn && dlConn.isConnected()) {
    try {
      dlConn.endStream();
    }catch(err) {
        d3.select("div.message").append("p").text(`Error endStream ${err}`);
        dlConn = null;
    }
  }
  if ( ! dlConn) {
    console.log(`doDatalinkConnect dlConn is null`);
    dlConn = new datalink.DataLinkConnection(datalinkUrl, dlCallback, errorFn);
    dlPromise = dlConn.connect();
  } else {
    console.log(`doDatalinkConnect dlConn exists, reuse`);
    try {
      if (dlConn.isConnected()) {
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
    d3.select("div.message").append("p").text(`Unable to connect: ${err}`);
    dlConn.close();
    return null;
  }).then(serverId => {
    d3.select("div.message").append("p").text(`Connect to ${serverId}`);
    return dlConn.awaitDLCommand("MATCH", `(.*/MAXACC)`)


  }).then(response => {
    d3.select("div.message").append("p").text(`MATCH response: ${response}`);
    dlConn.stream();
  });
  return dlPromise;
}

let dlMaxAccelerationCallback = function(dlPacket) {

    let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
    let maxaccJson = JSON.parse(s);

    let seismogram = makeSeismogram(maxaccJson);
    let trace = allTraces.get(seismogram.codes());
    if(trace){
      let oldSeis = trace.segments[trace.segments.length-1];
      let delta = moment.duration(.5, 'seconds');
      if (seismogram.start.isAfter(oldSeis.end) && seismogram.start.subtract(delta).isBefore(oldSeis.end)){
        oldSeis.y.push(maxaccJson.maxacc);
      }else{
        trace.append(seismogram);
        const littleBitLarger = {'start': moment.utc(timeWindow.start).subtract(60, 'second'),
                                'end': moment.utc(timeWindow.end).add(180, 'second')};
        const newTrace = trace.trim(littleBitLarger);
        if (! newTrace) {
          console.log(`trace trim returned null`);
        } else {
          allTraces.set(seismogram.codes(), newTrace);
          allSeisPlots.get(seismogram.codes()).replace(trace, newTrace);
        }
      }
      // if we are not paused, let timer animationLoop redraw
      // so we don't have to redraw for every packet
      // if paused, then schedule a redraw the next time is comes
      // around on the guitar
      if (paused) {
        needsRedraw.add(allSeisPlots.get(seismogram.codes()));
      }
    }else{
      handleMaxAccSeismogram(seismogram);
    }
    accelMaxValues.set(dlPacket.streamId, maxaccJson);
}

let dlCallback = function(dlPacket) {
    if (dlPacket.streamId.endsWith("MAXACC")) {
    dlMaxAccelerationCallback(dlPacket);
  }
};


let handleMaxAccSeismogram = function(seismogram) {
  if ( svgParent.empty()) {
    return;
  }
  let codes = seismogram.codes();
  //let seismogram = wp.miniseed.createSeismogram([miniseed]);
  if (allSeisPlots.has(codes)) {
    if (allTraces.has(codes) && allTraces.get(codes)) {
      const oldTrace = allTraces.get(codes);
      if (oldTrace) {
        oldTrace.append(seismogram);
      } else {
        oldTrace = new seisplotjs.model.Trace(seismogram)
      }
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
      needsRedraw.add(allSeisPlots.get(codes))
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
    seisPlotConfig.connectSegments = true;
    seisPlotConfig.lineWidth = 2;
    seisPlotConfig.xLabel = codes;
    seisPlotConfig.margin = margin ;
    seisPlotConfig.maxHeight = 200 ;
    seisPlotConfig.doRMean = false ;
    seisPlotConfig.fixedYScale = [-.1, seisGraphMax] ;
    seisPlotConfig.yScaleFormat = ".1f";
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
  if (console.error) {
    console.error(error, error.stack);
  } else {
    alert(error.message);
  }
  doDisconnect(true);
  dlConn = null; // force a complete reconnection next time
};

let doDisconnect = function(value) {
  console.log("disconnect..."+stopped+" -> "+value);
  stopped = value;
  if (stopped) {
    if (dlConn) {dlConn.close();}
    d3.select("button#disconnect").text("Reconnect");
  } else {
    doDatalinkConnect().then( () => {
      d3.select("button#disconnect").text("Disconnect");
    });
  }
}


// update equilizer and seis plots, but only as fast as the browser can handle redraws
let animationDrawLoop = function() {
  if ( ! paused) {
    liveequalizer.updateEqualizer(accelMaxValues);
  }
  // lather, rinse, repeat...
  window.requestAnimationFrame(animationDrawLoop);
};
// start drawing:
window.requestAnimationFrame(animationDrawLoop);

doDatalinkConnect()


let today = moment().format("dddd");
fetchCurrentResult()
    .then(function(result) {
      let floatFormat = d3.format(".2f");
      let cR = d3.select("div.currentRace");
      cR.select("span.dayName").text(`${result.Day_Name}`);
      cR.select("div.start_time").select("span").text(`${result.Trigger_Info.startTime}`);
      cR.select("div.end_time").select("span").text(`${result.Trigger_Info.endTime}`);
      cR.select("div.race_class").select("span").text(`${result.Trigger_Info.class}`);
      let heatDiv = cR.select("div.race_heat");
      heatDiv.select("span").text(`${result.Trigger_Info.heat}`);
      cR.select("div.dutyOfficer").select("span").text(`${result.Trigger_Info.dutyOfficer}`);
      let datasetNow = [result.peakACC_FL,result.peakACC_NL,result.peakACC_NR,result.peakACC_FR];
      let accText = `max: ${floatFormat(Math.max(...datasetNow))} of ${floatFormat(result.peakACC_FL)}, ${floatFormat(result.peakACC_NL)}, ${floatFormat(result.peakACC_NR)}, ${floatFormat(result.peakACC_FR)}`
      cR.select("div.maxacc").select("span").text(accText);

      let equalizer = new Equalizer("div.equalizer");
      let eqMap = createEqualizerMap(result)
      equalizer.updateEqualizer(eqMap);
    }).catch(function(err) {
      console.error(err);
      d3.select("div.currentRace").select("div.start_time").select("span").text("");
      d3.select("div.currentRace").select("div.end_time").select("span").text("");
      d3.select("div.currentRace").select("div.race_class").select("span").text("");
      let heatDiv = d3.select("div.currentRace").select("div.race_heat");
      heatDiv.select("span").text("");
      d3.select("div.currentRace").select("div.dutyOfficer").select("span").text("");
      d3.select("div.currentRace").select("div.maxacc").select("span").text("");

    });

    createEqualizerMap = function(result){
      let dataset=new Map();
      dataset.set("FL",{'station':'FL','maxacc':result.peakACC_FL});
      dataset.set("NL",{'station':'NL','maxacc':result.peakACC_NL});
      dataset.set("NR",{'station':'NR','maxacc':result.peakACC_NR});
      dataset.set("FR",{'station':'FR','maxacc':result.peakACC_FR});
      return dataset;
    }
