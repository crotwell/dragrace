

let datalink = seisplotjs.datalink


//let wp = require('seisplotjs-waveformplot');
// this global comes from the seisplotjs_waveformplot standalone js
let wp = seisplotjs.waveformplot;
let d3 = seisplotjs.d3;
let moment = seisplotjs.moment;

const doReplay = false

let net = 'CO';
//let staList = ['PI01', 'PI02', 'PI03', 'PI04', 'PI05', 'PI06', 'PI07', 'PI99'];
let staList = ['FL', 'NL', 'CT', 'NR', 'FR'];
let config = null;
let ipmap = new Map();
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
const REPLAY_INTERNAL_PORT = 6384;
const INTERNAL_PATH = '/datalink';
const EXTERNAL_HOST = "www.seis.sc.edu";
const EXTERNAL_PORT = 80;
const EXTERNAL_PATH = '/dragracews/datalink';
const REPLAY_PATH = '/replayracews/datalink';
const REPLAY_INTERNAL_PATH = '/datalink';
const AUTH_PATH = '/authracews/datalink'
let host = EXTERNAL_HOST;
let port = EXTERNAL_PORT;
let path = EXTERNAL_PATH;

if (doReplay) {
  path = REPLAY_PATH;
  staList = ['XB02', 'XB03', 'XB05', 'XB08', 'XB10'];
}

    //PI status color change with  differences in maxacc packet time
    //const StrugDur = moment.duration(3 'minutes');
    //const DeadDur = moment.duration(6 'minutes');
    const StrugDur = moment.duration(10, 'seconds');
    const DeadDur = moment.duration(20, 'seconds');

//host="127.0.0.1";
//port=6382;

let datalinkUrl = wsProtocol+"//"+host+(port==80?'':':'+port)+path;
console.log("URL: "+datalinkUrl);
//let writeDatalinkUrl = wsProtocol+"//"+host+(port==80?'':':'+port)+path
let writeDatalinkUrl = wsProtocol+"//"+INTERNAL_HOST+(INTERNAL_PORT==80?'':':'+INTERNAL_PORT)+INTERNAL_PATH;
if (doReplay) {
  writeDatalinkUrl = wsProtocol+"//"+INTERNAL_HOST+(REPLAY_INTERNAL_PORT==80?'':':'+REPLAY_INTERNAL_PORT)+REPLAY_INTERNAL_PATH;
}

let jwtToken = null;
let jwtTokenPromise = null;
let jwtTokenUrl = protocol+"//"+host+(port==80?'':':'+port)+'/authrace/dutytoken.jwt';
if (protocol == 'https:') {
  // only try to get token if https
  //writeDatalinkUrl =  wsProtocol+"//"+host+(port==80?'':':'+port)+AUTH_PATH;
  writeDatalinkUrl = datalinkUrl
  jwtTokenPromise = fetch(jwtTokenUrl, {
    credentials: 'same-origin'
  }).then(function(response) {
    if(response.ok) {
      return response.text();
    }
    throw new Error('Network response for jwt token was not ok.');
  }).then(function(jwtText) {
    jwtToken = jwtText.trim();
    jwtTokenPromise = null;
    if (jwtToken.length === 0) {
      throw new Error('jwt token length is zero.');
    }
    console.log(`got jwt: ${jwtToken}`);
  }).catch(function(error) {
    console.log('There has been a problem with fetch jwt token: ', error.message);
  });
}

let equalizer = new Equalizer("div.equalizer");
d3.select('#stationChoice')
  .selectAll("option")
  .data(staList)
  .enter()
    .append("option")
    .text(function(d) {return d;});

d3.selectAll('.textHost').text(host);

let accelMaxValues = new Map();
let prevAccelValue = new Map();
let dlConn = null;
let allSeisPlots = new Map();
let allTraces = new Map();
let markers = [];
let svgParent = wp.d3.select('div.realtime');
let margin = {top: 20, right: 20, bottom: 50, left: 60};
let needsRedraw = new Set();

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

let packetCount = 0;

let handleMaxAccSeismogram = function(seismogram) {
  let codes = seismogram.codes();
  //let seismogram = wp.miniseed.createSeismogram([miniseed]);
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
  let startMark = { markertype: 'predicted', name: "Start"+displayName, time: moment.utc(trig.startTime) };
  markers.push(startMark);
  //Gabby & Emma tried to make two trigger flags appear at 3 seconds apart
  let endMark = { markertype: 'predicted', name: displayName, time:  moment.utc(trig.endTime) };
  markers.push(endMark);
  for (let sp of allSeisPlots.values()) {
    sp.appendMarkers( [ startMark,endMark ]);
  }

};


// update equilizer, but only as fast as the browser can handle redraws
let drawEquilizer = function() {
  d3.select("div.piStatus").selectAll(`span`).classed('struggling', false).classed('good', false);
  accelMaxValues.forEach((maxaccJson, streamId, map) => {
    // turn all into string
    //let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
    //let maxaccJson = JSON.parse(s);
    let scaleAcc = Math.round(100*maxaccJson.maxacc/2); // 2g = 100px

    let now = moment.utc();
    let packtime = moment.utc(maxaccJson.end_time);
      //var duration = moment.duration(now,diff(packtime));

    if ( ! prevAccelValue[streamId] || prevAccelValue[streamId] !== scaleAcc) {
      // only update if the value changed
      prevAccelValue[streamId] = scaleAcc;
      staSpan = d3.select("div.oldEqualizer").select(`span.${maxaccJson.station}`);
      staSpan.select("div").transition().style("height", `${scaleAcc}px`);
    }

//determine time intervals and associate class names

    let statpi = d3.select("div.piStatus");

    if(now.subtract(StrugDur).isBefore(packtime)){
      statpi.select(`span.${maxaccJson.station}`).classed('struggling', false).classed('good', true);
    } else if(now.subtract(DeadDur).isBefore(packtime)){
      statpi.select(`span.${maxaccJson.station}`).classed('struggling', true).classed('good', false);
    } else {
      statpi.select(`span.${maxaccJson.station}`).classed('struggling', false).classed('good', false);
    }


  });
  // lather, rinse, repeat...
  window.requestAnimationFrame(drawEquilizer);
};
// start drawing:
window.requestAnimationFrame(drawEquilizer);

let dlMaxAccelerationCallback = function(dlPacket) {

    let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
    let maxaccJson = JSON.parse(s);

    let seismogram = makeSeismogram(maxaccJson);
    let trace = allTraces.get(seismogram.codes());
    if(trace){
      let oldSeis = trace.segments[trace.segments.length-1];
      let delta = moment.duration(.375, 'seconds');
      if (seismogram.start.isAfter(oldSeis.end) && seismogram.start.subtract(delta).before(oldSeis.end)){
        oldSeis.y.push(maxaccJson.maxacc);
      }else{
        trace.append(seismogram);
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
    equalizer.updateEqualizer(accelMaxValues);
}


let dlPacketPeakCallback = function(dlPacket) {
    // turn all into string
    let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
    let maxacc = JSON.parse(s);
    let scaleAcc = Math.round(100*maxacc.maxacc/2); // 2g = 100px
    let staSpan = d3.selectAll("div.oldEqualizer").selectAll(`span.${maxacc.station}`);
    staSpan.selectAll("div").transition().style("height", `${scaleAcc}px`).style("background-color", "yellow");
    //console.log(`maxacc: ${maxacc.station}  ${maxacc.maxacc}  ${scaleAcc}`)
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
  } else if (dlPacket.streamId.endsWith("ZMAXCFG")) {
    dlPacketConfigCallback(dlPacket);
  } else if (dlPacket.streamId.endsWith("IP")) {
    dlPacketIPCallback(dlPacket);
  }
};

let doDatalinkConnect = function() {
  let dlPromise = null;
  if (dlConn && dlConn.isConnected()) {
    try {
      dlConn.endStream();
    }catch(err) {
        d3.select("div.triggers").append("p").text(`Error endStream ${err}`);
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
  dlPromise.then(serverId => {
    d3.select("div.triggers").append("p").text(`Connect to ${serverId}`);
    if (staCode){
      return dlConn.awaitDLCommand("MATCH", `(${staCode}.*(_|\.)HNZ/MSEED)|(.*/MTRIG)|(.*/MAXACC)|(.*/ZMAXCFG)|(.*/IP)`);
    } else {
      return dlConn.awaitDLCommand("MATCH", `(.*/MTRIG)|(.*/MAXACC)|(.*/ZMAXCFG)|(.*/IP)`)
    }
  }).then(response => {
    d3.select("div.triggers").append("p").text(`MATCH response: ${response}`);
    return dlConn.awaitDLCommand(`POSITION AFTER ${datalink.momentToHPTime(timeWindow.start)}`);
  }).then(response => {
    d3.select("div.triggers").append("p").text(`POSITION response: ${response}`);
    dlConn.stream();
  }).catch(err => {
    d3.select("div.triggers").append("p").text(`Unable to connect: ${err}`);
    if (dlConn) {
      dlConn.close();
    }
    throw err;
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
        "startTime":moment.utc(trig.time).subtract(15, 'seconds').toISOString(),
        "endTime":moment.utc(trig.time).add(15, 'seconds').toISOString(),
        "creation": trigtime.toISOString(),
        "override": {
            "modtime": trigtime.toISOString(),
            "value": "enable"
        }
    };
  let dlTriggerConn = new datalink.DataLinkConnection(writeDatalinkUrl, dlTriggerCallback, errorFn);
  dlTriggerConn.connect().then(serverId => {
    d3.select("div.triggers").append("p").text(`Connect to ${serverId}`);
    if (jwtTokenPromise === null && jwtToken) {
      return dlTriggerConn.awaitDLCommand(`AUTHORIZATION`, jwtToken);
    } else {
      d3.select("div.triggers").append("p").text(`Unable to send trigger, not auth`);
      throw new Error(`Unable to send trigger, not auth. jwt: ${jwtToken != null} ${jwtToken}`);
    }
  }).then(authResponse => {
    d3.select("div.triggers").append("p").text(`AUTH ack: ${authResponse}`);
    if ( ! authResponse.startsWith("OK")) {
      throw new Error(`AUTH ack: ${authResponse}`);
    }
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
  if (console.error) {
    console.error(error, error.stack);
  } else {
    alert(error.message);
  }
  d3.select("div.triggers").append("p").text(`Error: ${error}`);
  doDisconnect(true);
  dlConn = null; // force a complete reconnection next time
};

//go into config file and grab info to place in href html pi status
let dlPacketConfigCallback = function(dlPacket) {
  if (! config || dlPacket.hppacketend > datalink.momentToHPTime(moment.utc().subtract(20, 'seconds'))){


    let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
    let currConfig = JSON.parse(s);

    let statpi = d3.select("div.piStatus");
    for (let [PIkey,PILoc] of Object.entries(currConfig.Loc)) {
      if (PILoc !== "NO"){
        let oldTheta = null;
        if (config && config.LocInfo[PILoc]) {
          oldTheta = config.LocInfo[PILoc].Angles.Theta;
        }
        let theta = currConfig.LocInfo[PILoc].Angles.Theta;
        if (oldTheta !== theta) {
          console.log(`config packet, theta change ${PILoc}  ${PIkey} ${theta}`);
          statpi.select("span."+PILoc).attr(`title`,`PI=${PIkey},Theta=${theta}, IP=${ipmap.get(PIkey)}`);
        }
      }
    }
    config = currConfig; // save for next time
  }
}
let dlPacketIPCallback = function(dlPacket) {
  if (dlPacket.hppacketend > datalink.momentToHPTime(moment.utc().subtract(20, 'seconds'))){

    if (config){
      let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
      let ipjson = JSON.parse(s);
      // only do update if the IP has changed
      if ( ! ipmap.has(ipjson.station) || ipmap.get(ipjson.station) !== ipjson.ip) {
        console.log(`ip packet ${ipjson.station}  ${ipjson.ip}`);
        ipmap.set(ipjson.station,ipjson.ip);
        let PIkey = ipjson.station;
        let PILoc = config.Loc[ipjson.station]
        let theta = config.LocInfo[PILoc].Angles.Theta;
        let statpi = d3.select("div.piStatus");
        statpi.select("span."+PILoc).attr(`title`,`PI=${PIkey},Theta=${theta}, IP=${ipmap.get(PIkey)}`);
      }
    }
  }
}

let animationCallback = function() {
  needsRedraw.forEach(sp => {
    sp.draw();
  });

  window.requestAnimationFrame(animationCallback);
}
window.requestAnimationFrame(animationCallback);
//
let staCode = null
doDatalinkConnect()
