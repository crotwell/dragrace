

let datalink = seisplotjs.datalink;
let seisGraphMax = 2.0;

//let wp = require('seisplotjs-waveformplot');
// this global comes from the seisplotjs_waveformplot standalone js
let wp = seisplotjs.waveformplot;
let d3 = seisplotjs.d3;
let moment = seisplotjs.moment;

const doReplay = false
const do1SPS = false

let net = 'CO';
//let staList = ['PI01', 'PI02', 'PI03', 'PI04', 'PI05', 'PI06', 'PI07', 'PI99'];
let staList = ['FL', 'NL', 'CT', 'NR', 'FR'];
//monday = 1
//friday = 5
//saturday = 6
//sunday = 7
let classList = [];
let heatNumber = 1;
let prevHeat= "";

let today = moment()
  if(today.weekday() === 5){
    classList = ['FRIDAY','Funny-Car','Sportsman-Qualifying','Competition-Eliminator-Qualifying Sessions','Midway-Open','Top-Alcohol-Qualifying-Session','Factory-Stock-Showdown-Qualifying','Mountain-Motor-Pro-Stock-Qualifying-Session','Pro-Mod-Qualifying-Session','Pro-Stock-Motorcycle-Qualifying-Session','Nitro-Qualifying-Session','Top-Alcohol-Qualifying-Session','Factory-Stock-Showdown-Qualifying','Mountain-Motor-Pro-Stock-Qualifying-Session','Pro-Mod-Qualifying-Session','Pro-Stock-Motorcycle-Qualifying Session','Nitro-Qualifying-Session','Secure-Track'];
  }else if(today.weekday() === 6){
    classList=['SATURDAY','Sportsman-Eliminations','Midway-Open','Competition-Eliminator','Super-Comp','Super-Gas','Super-Stock','Top-Alcohol-Qualifying-Session','Factory-Stock-Showdown-Qualifying','Mountain-Motor-Pro-Stock-Qualifying-Session','Pro-Mod-Qualifying-Session','Pro-Stock-Motorcycle-Qualifying-Session','Nitro-Qualifying-Session','Top-Alcohol-Eliminations','Factory-Stock-Showdown','Pro-Mod-Qualifying-Session','Pro-Stock-Motorcycle-Qualifying-Session','Nitro-Qualifying-Session','Mountain Motor-Pro-Stock-Qualifying-////Session','Top-Alcohol-Eliminations','Secure-Track'];
  }else if(today.weekday() === 7){
    classList=['SUNDAY','Nitro-Eliminations','Pro-Stock-Motorcycle-Eliminations','Pro-Mod-Eliminations','Mountain-Motor-Pro-Stock','Factory-Stock-Showdown','Competition-Eliminator','Sportsman-Eliminations','Top-Alcohol-Eliminations','Factory-Stock-Showdown','Competition-Eliminator','Sportsman-Eliminations','Nitro-Eliminations','Pro-Stock-Motorcycle-Eliminations','Pro-Mod-Eliminations','Mountain-Motor-Pro-Stock','Sportsman-Eliminations','Competition-Eliminator','Factory-Stock-Showdown','Top-Alcohol-Eliminations','Parade-of-Champions','Mountain-Motor-Pro-Stock','Pro-Mod-Eliminations','Pro-Stock-Motorcycle-Eliminations','Nitro-Eliminations'];
  }else{
  classList=['UNKNOWN','Test1','test-2'];
  console.log("we have wrong dates")
}

let config = null;
let ipmap = new Map();
let timerInProgress = false;
let clockOffset = 0; // should get from server somehow
let duration = 300;
let maxSteps = -1; // max num of ticks of the timer before stopping, for debuging
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
const AUTH_1SPS_PATH = '/auth1spsws/datalink'
let host = EXTERNAL_HOST;
let port = EXTERNAL_PORT;
let path = EXTERNAL_PATH;
if (do1SPS) {
  path = AUTH_1SPS_PATH;
}

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
  if ( do1SPS) {
    writeDatalinkUrl = wsProtocol+"//"+host+(port==80?'':':'+port)+AUTH_PATH;
  } else {
    writeDatalinkUrl = datalinkUrl;
  }
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

d3.select('#classChoice')
  .selectAll("option")
  .data(classList)
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
let margin = {top: 5, right: 20, bottom: 40, left: 60};
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

let dlMSeedCallback = function(dlPacket) {
  handleMSeed(dlPacket.miniseed);
};

let dlTriggerCallback = function(dlPacket) {
  // turn all into string
  let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
  d3.select("div.triggers").append("p").text(`Trigger: ${s}`);
  let trig = JSON.parse(s)
  displayName = trig.dutyOfficer ? trig.dutyOfficer : "AutoTrigger";
  displayHeat = trig.heat ? trig.heat : "AutoTrigger";
  let startMark = { markertype: 'predicted', name: "ST_"+displayName, time: moment.utc(trig.startTime) };
  markers.push(startMark);
  //Gabby & Emma tried to make two trigger flags appear at 3 seconds apart
  let endMark = { markertype: 'predicted', name: displayHeat, time:  moment.utc(trig.endTime) };
  markers.push(endMark);
  for (let sp of allSeisPlots.values()) {
    sp.appendMarkers( [ startMark,endMark ]);
  }

};


// update equilizer and seis plots, but only as fast as the browser can handle redraws
let animationDrawLoop = function() {
  if ( ! paused) {
    equalizer.updateEqualizer(accelMaxValues);

    d3.select("div.piStatus").selectAll(`span`).classed('struggling', false).classed('good', false);
    accelMaxValues.forEach((maxaccJson, streamId, map) => {
      let now = moment.utc();
      let packtime = moment.utc(maxaccJson.end_time);
      let statpi = d3.select("div.piStatus");

      if(now.subtract(StrugDur).isBefore(packtime)){
        statpi.select(`span.${maxaccJson.station}`).classed('struggling', false).classed('good', true);
      } else if(now.subtract(DeadDur).isBefore(packtime)){
        statpi.select(`span.${maxaccJson.station}`).classed('struggling', true).classed('good', false);
      } else {
        statpi.select(`span.${maxaccJson.station}`).classed('struggling', false).classed('good', false);
      }
    });

    needsRedraw.forEach(sp => {
      sp.draw();
    });
    needsRedraw.clear();
  }
  // lather, rinse, repeat...
  window.requestAnimationFrame(animationDrawLoop);
};
// start drawing:
window.requestAnimationFrame(animationDrawLoop);

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
    return dlConn.awaitDLCommand(`POSITION AFTER ${datalink.momentToHPTime(timeWindow.end.subtract(60, 'second'))}`);
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
  let heatE = document.getElementsByName('heatE')[0].value;
  heatE = heatE.replace(/\W/, '');
  heatE = heatE.replace(/_/, '');
  heatE = heatE.toUpperCase();

  let classChoiceE = document.getElementById('classChoice');
  let classChoice = classChoiceE.options[classChoiceE.selectedIndex].text;
  let trigger = {
        "type": "manual",
        "dutyOfficer": dutyOfficer,
        "heat":heatE,
        "class":classChoice,
        "time": trigtime.toISOString(),
        "startTime":moment.utc(trigtime).subtract(20, 'seconds').toISOString(),
        "endTime":moment.utc(trigtime).add(20, 'seconds').toISOString(),
        "creation": trigtime.toISOString(),
        "override": {
            "modtime": trigtime.toISOString(),
            "value": "enable"
        }
    };
  // update heat to next number
    updateHeatNumber(heatE);

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
        let theta = 0;
        if (PILoc !== "NO"){
          theta = config.LocInfo[PILoc].Angles.Theta;
        }
        let statpi = d3.select("div.piStatus");
        statpi.select("span."+PILoc).attr(`title`,`PI=${PIkey},Theta=${theta}, IP=${ipmap.get(PIkey)}`);
      }
    }
  }
}

updateCurrentResult = function(result) {
  let c = result.Trigger_Info.class;
  let h = result.Trigger_Info.heat;
  let day = result.Day_Name;
  let floatFormat = d3.format(".2f");
  let cR = d3.select("div.currentRace");
  cR.select("span.dayName").text(`${result.Day_Name}`);
  cR.select("div.start_time").select("span").text(`${result.Trigger_Info.startTime}`);
  cR.select("div.end_time").select("span").text(`${result.Trigger_Info.endTime}`);
  cR.select("div.race_class").select("span").text(`${result.Trigger_Info.class}`);
  let heatDiv = cR.select("div.race_heat");
  heatDiv.select("span").text(`${result.Trigger_Info.heat}`);
  heatDiv.select("a").attr("href", `https://www.seis.sc.edu/dragrace/www/results/${day}/${c}/${h}/results.json`);
  //d3.select("div.currentRace").select("div.race_heat").text(`Heat = ${result.Trigger_Info.heat}`);
  cR.select("div.dutyOfficer").select("span").text(`${result.Trigger_Info.dutyOfficer}`);
  let datasetNow = [result.peakACC_FL,result.peakACC_NL,result.peakACC_NR,result.peakACC_FR];
  let accText = `${floatFormat(result.peakACC_FL)}, ${floatFormat(result.peakACC_NL)}, ${floatFormat(result.peakACC_NR)}, ${floatFormat(result.peakACC_FR)}`
  cR.select("div.maxacc").select("span").text(accText);
  return result;
}

updateHeatNumber = function(heatE) {
    prevHeat = heatE;
    const heatRegex = /(.*\D)(\d+)/;
    let matchinfo = heatRegex.exec(heatE);
    if (matchinfo){
      let prefix = matchinfo[1];
      let num = parseInt(matchinfo[2]) +1;
      console.log(`updateHeatNumber prefix: ${prefix}  num: ${num}`)
      heatE = `${prefix}${num}`
      document.getElementsByName('heatE')[0].value = heatE;
    }
}

// update first time, also set heat
fetchCurrentResult()
    .then(function(result) {
      if (result && result.Trigger_Info.heat) {
        updateHeatNumber(result.Trigger_Info.heat);
      }
      return result;
    })
    .then(function(result) {
      return updateCurrentResult(result);
    });

// timer to update most recent result, every 10 seconds
window.setInterval(()=>{
  fetchCurrentResult()
      .then(function(result) {
        return updateCurrentResult(result);
      }).catch(function(err){
        console.error(`Trouble getting current race: ${err}`);
        d3.select("div.currentRace").select("div.start_time").select("span").text("");
        d3.select("div.currentRace").select("div.end_time").select("span").text("");
        d3.select("div.currentRace").select("div.race_class").select("span").text("");
        let heatDiv = d3.select("div.currentRace").select("div.race_heat");
        heatDiv.select("span").text("");
        heatDiv.select("a").attr("href", "").text("");
        d3.select("div.currentRace").select("div.dutyOfficer").select("span").text("");
        d3.select("div.currentRace").select("div.maxacc").select("span").text("");

      });
}, 10*1000);

//
let staCode = null
doDatalinkConnect()
