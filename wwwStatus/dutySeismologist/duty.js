

let datalink = seisplotjs.datalink;
let seisGraphMax = 2.0;   //max

// this global comes from the seisplotjs_waveformplot standalone js
let d3 = seisplotjs.d3;
let moment = seisplotjs.moment;
let util = seisplotjs.util; // make sure util rsvp error handler already registered

seisplotjs.RSVP.on('error', function(reason, label) {
  if (label) {
    console.error(label);
  }

  console.assert(false, reason);
  // eslint-disable-next-line no-console
  console.assert(false, reason);
  d3.select("#errormessage span").text(`${label?label:""} ${reason} ${reason.name} ${reason.message}`);
  d3.select("div.triggers").append("p").text(`Error: ${reason.name} ${reason.message}`);
});

const doReplay = false
const do1SPS = false

let net = 'CO';
//let staList = ['PI01', 'PI02', 'PI03', 'PI04', 'PI05', 'PI06', 'PI07', 'PI99'];
let staList = ['FL', 'NL', 'FL0','FL60','FL330','FL660','FL1K','FL4G'];
//monday = 1
//friday = 5
//saturday = 6
//sunday = 7
let classList = [];
let heatNumber = 1;
let prevHeat= "";

let today = moment()
  if(today.weekday() === 5){
    classList = ['FRIDAY','Sportsman-Qualifying','Top-Alcohol-Qualifying-Session',
    'Midway-Open','Competition-Qualifying-Session','Top-Alcohol-Qualifying-Session',
    'Pro-Mod-Qualifying-Session','Pro-Stock-Qualifying-Session','Nitro-Qualifying-Session',
    'Pro-Mod-Qualifying-Session','Pro-Stock-Qualifying Session','Nitro-Qualifying-Session','Secure-Track'];
  }else if(today.weekday() === 6){
    classList=['SATURDAY','Sportsman-Eliminations','Midway-Open','Competition-Qualifying-Session',
    'Top-Alcohol-Eliminations-R1','Competition-Eliminations-R1','Pro-Mod-Qualifying-Session',
    'Pro-Stock-Qualifying-Session','Nitro-Qualifying-Session','Pro-Mod-Qualifying Session',
    'Pro-Stock-Qualifying-Session','Nitro-Qualifying-Session','Top-Alcohol-Eliminations-R2',
    'Competition-Eliminations-R2','Sportsman-Eliminations','Competition-Eliminations-R3',
    'Sportsman-Eliminations','Secure-Track'];
  }else if(today.weekday() === 7){
    classList=['SUNDAY','Midway-Open','Pre-Race-Walk','Nitro-Eliminations-R1','Pro-Stock-Eliminations-R1',
    'Pro-Mod-Eliminations-R1','Nitro-Eliminations-R2','Pro-Stock-Eliminations-R2','Pro-Mod-Eliminations-R2',
    'Top-Alcohol-Eliminations-Semi-Final','Competition-Eliminations-Semi-Final','Sportsman-Eliminations-Semi-Final',
    'Nitro-Elimination-Semi-Final','Pro-Stock-Elimination-Semi-Final','Pro-Mod-Eliminations-Semi-Final',
    'Sportsman Eliminations-Finals','Competition-Eliminations-Final','Top-Alcohol-Eliminations-Finals','Jr-Dragsters',
    'Parade-of-Champions','Pro-Mod-Eliminations-Final','Pro-Stock-Eliminations-Final','Nitro-Elimination-Final'];
  }else{
    classList=['Not Race Day','Test1','Test2','Test3'];
}

let config = null;
let ipmap = new Map();
let redrawInProgress = false;
let clockOffset = 0; // should get from server somehow
let duration = seisplotjs.moment.duration(5, 'minutes');
let maxSteps = -1; // max num of ticks of the timer before stopping, for debuging
let timeWindow = new seisplotjs.util.StartEndDuration(null, null, duration, clockOffset);
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
const LINODE_HOST = 'li75-105.members.linode.com'
const LINODE_PATH = '/datalinkws';
let host = LINODE_HOST;
let port = EXTERNAL_PORT;
let path = LINODE_PATH;
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

let liveEqualizer = new Equalizer("div.liveEqualizer");

d3.select('#classChoice')
  .selectAll("option")
  .data(classList)
  .enter()
    .append("option")
    .text(function(d) {return d;});


d3.selectAll('.textHost').text(host);

let accelMaxValues = liveEqualizer.createZeros();
let prevAccelValue = new Map();
let dlConn = null;
let allSeisPlots = new Map();
let allTraces = new Map();
let markers = [];
let svgParent = d3.select('div.realtime');
let margin = {top: 5, right: 20, bottom: 40, left: 60};
let needsRedraw = new Set();

let paused = false;
let stopped = false;
let numSteps = 0;




//go into sidebar buttons and deactivate
let togglebutton = function(heatdiv) {
  d3.select("div.sidebar").selectAll("div").select(".panel").style("display","none");
  d3.select("div.sidebar").selectAll("div").select("button").classed("active", false);

    heatdiv.select("button").classed("active", true);
    heatdiv.select(".panel").style("display","block");
};
d3.select("div.class1 button.heatcollapse").on("click", function(d) {
  console.log("buttonclick "+d);
   let heatdiv = d3.select("div.class1");
   togglebutton(heatdiv);


});
d3.select("div.class2 button.heatcollapse").on("click", function(d) {
  console.log("buttonclick "+d);
   let heatdiv = d3.select("div.class2");
   togglebutton(heatdiv);

});

//end trying to make heat buttons work

let packetCount = 0;

let handleMaxAccSeismogram = function(seismogram) {
  let codes = seismogram.codes();
  if (allSeisPlots.has(codes)) {
    if (allTraces.has(codes) && allTraces.get(codes)) {
      let sdd = allTraces.get(codes);
      if (sdd) {
        sdd.seismogram.append(seismogram);
      } else {
        sdd = seisplotjs.seismogram.SeismogramDisplayData.fromSeismogram(seismogram);
      }
      const littleBitLarger = new seisplotjs.util.StartEndDuration(moment.utc(timeWindow.start).subtract(60, 'second'),
                              moment.utc(timeWindow.end).add(180, 'second'));

      const newTrace = sdd.seismogram.trim(littleBitLarger);
      if (newTrace) {
        sdd.seismogram = newTrace;
        allTraces.set(codes, sdd);
        allSeisPlots.get(codes).calcScaleDomain();
      } else {
        // trim removed all data, nothing left in window
        allTraces.delete(codes);
        allSeisPlots.get(codes).remove(sdd);
      }
    } else {
      let sdd = seisplotjs.seismogram.SeismogramDisplayData.fromSeismogram(seismogram);
      allSeisPlots.get(codes).append(sdd);
      needsRedraw.add(allSeisPlots.get(codes))
    }
//      allSeisPlots.get(codes).trim(timeWindow);
  } else {
    if (svgParent && ! svgParent.empty()){
      svgParent.select("p.waitingondata").remove();
      let seisDiv = svgParent.append('div').classed(codes, true);
  //    seisDiv.append('p').text(codes);
      let plotDiv = seisDiv.append('div');
      let seisPlotConfig = new seisplotjs.seismographconfig.SeismographConfig();
      seisPlotConfig.connectSegments = true;
      //seisPlotConfig.drawingType = seisplotjs.seismographconfig.DRAW_BOTH_ALIGN;
      seisPlotConfig.lineWidth = 2;
      seisPlotConfig.title= [codes]
      //seisPlotConfig.xLabel = codes;
      seisPlotConfig.margin = margin ;
      seisPlotConfig.maxHeight = 200 ;
      seisPlotConfig.doRMean = false ;
      seisPlotConfig.fixedYScale = [-.1, seisGraphMax] ;
      seisPlotConfig.yScaleFormat = ".1f";
      seisPlotConfig.wheelZoom = false;
      let sdd = seisplotjs.seismogram.SeismogramDisplayData.fromSeismogram(seismogram);
      sdd.timeWindow = timeWindow;
      sdd.addMarkers(markers);
      let seisPlot = new seisplotjs.seismograph.Seismograph(plotDiv, seisPlotConfig, sdd);
      seisPlot.svg.classed('realtimePlot', true).classed('overlayPlot', false);
      seisPlot.draw();
      allSeisPlots.set(codes, seisPlot);
      allTraces.set(codes, sdd);
    }
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
  for (let sp of allTraces.values()) {
    sp.addMarkers( [ startMark,endMark ]);
  }

};


// update equilizer and seis plots, but only as fast as the browser can handle redraws
let animationDrawLoop = function() {
  if ( ! paused) {
    liveEqualizer.updateEqualizer(accelMaxValues);

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
console.log(`dlMaxAccelerationCallback ${dlPacket}`)
    let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
    let maxaccJson = JSON.parse(s);

    let seismogram = makeSeismogram(maxaccJson);
    let sdd = allTraces.get(seismogram.codes());
    if(sdd){
      let trace = sdd.seismogram;
      let delta = moment.duration(.5, 'seconds');
      let lastSeg = trace.segments[trace.segments.length-1];

      if (lastSeg.numPoints < 100 && seismogram.startTime.isAfter(trace.endTime) && seismogram.startTime.subtract(delta).isBefore(trace.endTime)){
        let appendData = new Float32Array(lastSeg.numPoints+1);
        lastSeg.y.forEach((d,i) => appendData[i] = d);
        appendData[appendData.length-1] = maxaccJson.maxacc;
        let cloneSeg = lastSeg.cloneWithNewData(appendData)
        trace.segments[trace.segments.length-1] = cloneSeg;
        trace.findStartEnd();
      }else{
        trace.append(seismogram);
      }
      const littleBitLarger = new seisplotjs.util.StartEndDuration(moment.utc(timeWindow.start).subtract(60, 'second'),
                              moment.utc(timeWindow.end).add(180, 'second'));

      const newTrace = trace.trim(littleBitLarger);
      if (! newTrace) {
        console.log(`trace trim returned null`);
      } else {
        sdd.seismogram = newTrace;
      }
      sdd.timeWindow = new seisplotjs.util.StartEndDuration(sdd.startTime, seismogram.endTime);

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
  } else {
    console.log(`Unknown datalink stream id: ${dlPacket.streamId}`);
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
    dlConn = new datalink.DataLinkConnection(datalinkUrl, dlCallback, handleError);
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
      dlConn = new datalink.DataLinkConnection(datalinkUrl, dlCallback, handleError);
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

  if (svgParent && ! svgParent.empty()){
    svgParent.selectAll("*").remove();
    if (wsProtocol == 'wss:' && host == IRIS_HOST) {
      svgParent.append("h3").attr('class', 'waitingondata').text("IRIS currently does not support connections from https pages, try from a http page instead.");
    } else {
      svgParent.append("p").attr('class', 'waitingondata').text("waiting on first data");
    }
  }

  doDisconnect(false);
  doPause(false);
};


d3.select("button#trigger").on("click", function(d) {
  d3.select("#errormessage span").text("");// clear old error
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

  let dlTriggerConn = new datalink.DataLinkConnection(writeDatalinkUrl, dlTriggerCallback, handleError);
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
    if ( authResponse.type !== "OK") {
      throw new Error(`AUTH ack: ${authResponse}`);
    }
    d3.select("div.triggers").append("p").text(`Send Trigger: ${JSON.stringify(trigger)}`);
    return dlTriggerConn.writeAck(`XX_MANUAL_TRIG_${dutyOfficer}/MTRIG`,
      trigtime,
      trigtime,
      datalink.stringToUint8Array(JSON.stringify(trigger)));
  }).then(ack => {
    dlTriggerConn.close();
    d3.select("div.triggers").append("p").text(`Send trigger ack: ${ack}`);
  }).catch(err => handleError(err));
});

d3.select("button#pause").on("click", function(d) {
  doPause( ! paused);
});

d3.select("button#disconnect").on("click", function(d) {
  d3.select("#errormessage span").text("");// clear old error
  doDisconnect( ! stopped);
});

let doPause = function(value) {
  console.log("Pause..."+paused+" -> "+value);
  paused = value;
  if (paused) {
    d3.select("button#pause").text("Play");
  } else {
    d3.select("button#pause").text("Pause");
  }
}

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

let timerInterval = 250;
if (svgParent && ! svgParent.empty()){
  let rect = svgParent.node().getBoundingClientRect();
  timerInterval = duration.asMilliseconds()/
                    (rect.width-margin.left-margin.right);
}
while (timerInterval < 100) { timerInterval *= 2;}
console.log(`redraw interval: ${timerInterval}`)
let timer = seisplotjs.d3.interval(function(elapsed) {
  if ( paused || redrawInProgress) {
    return;
  }
  redrawInProgress = true;
  window.requestAnimationFrame(timestamp => {
    try {
      timeWindow = new seisplotjs.util.StartEndDuration(null, null, duration, clockOffset);
      allSeisPlots.forEach(function(value, key) {
          value.seismographConfig.fixedTimeScale = timeWindow;
          value.calcTimeScaleDomain();
          value.draw();
      });
    } catch(err) {
      console.assert(false, err);
    }
    redrawInProgress = false;
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

let handleError = function(error) {
  if (console.error) {
    console.error(`${error.name} ${error.message}`, error.stack);
  } else {
    alert(error.message);
  }
  d3.select("#errormessage span").text(`${error.name} ${error.message}`);
  d3.select("div.triggers").append("p").text(`Error: ${error.name} ${error.message}`);
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
        if ( ! currConfig.LocInfo[PILoc]) {
          console.warn(`missing station for config update: ${PILoc}, skipping...`);
          continue;
        }
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
        if (PILoc !== "NO" && config.LocInfo[PILoc]){
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
  let accText = staList.reduce((acc,s) => acc+` ${s}:${floatFormat(result.peakACC[s])}`, "")
  cR.select("div.maxacc").select("span").text(accText);

  if ( ! d3.select(".raceEqualizer").empty()) {
    d3.select(".raceEqualizer").select("svg").remove();
    let lastRaceEqualizer = new Equalizer(".raceEqualizer");
    let eqMap = createEqualizerMap(result)
    lastRaceEqualizer.updateEqualizer(eqMap);
  }
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
      d3.select('heatE').text(heatE);
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
