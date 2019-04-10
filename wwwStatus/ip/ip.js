
let datalink = seisplotjs.datalink


//let wp = require('seisplotjs-waveformplot');
// this global comes from the seisplotjs_waveformplot standalone js

let d3 = seisplotjs.d3;
let moment = seisplotjs.moment;


let dlConn = null;

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

let protocol = 'http:';
if ("https:" == document.location.protocol) {
  protocol = 'https:'
}
let wsProtocol = 'ws:';
if (protocol == 'https:') {
  wsProtocol = 'wss:';
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

let doDisconnect = function(value) {

    if (dlConn) {dlConn.close();}

}


let errorFn = function(error) {
  if (console.error) {
    console.error(error, error.stack);
  } else {
    alert(error.message);
  }
  d3.select("div.message").append("p").text(`Error: ${error}`);
  doDisconnect(true);
};

let datalinkUrl = wsProtocol+"//"+host+(port==80?'':':'+port)+path;
console.log("URL: "+datalinkUrl);
//let writeDatalinkUrl = wsProtocol+"//"+host+(port==80?'':':'+port)+path
let writeDatalinkUrl = wsProtocol+"//"+INTERNAL_HOST+(INTERNAL_PORT==80?'':':'+INTERNAL_PORT)+INTERNAL_PATH;



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
    return dlConn.awaitDLCommand("MATCH", `(.*/IP)`)


  }).then(response => {
    d3.select("div.message").append("p").text(`MATCH response: ${response}`);
    dlConn.stream();
  });
  return dlPromise;
}

let ipJsonList = [];



let drawIP = function(ipJsonList) {
  let ipParas = d3.select("div.ip").selectAll("p")
    .data(ipJsonList, function(d) { return d.time; });

  let ipEnter = ipParas.enter()
    .append("p").text(function(d,i){
      let PIkey = d.station;
      let ip = d.ip;
      let piTime = d.time;
      return `PI=${PIkey}, IP=${ip}, pitime:${piTime} serverTime: ${moment.utc().toISOString()}`;
    });
  let ipMerge = ipParas.merge(ipEnter);
  let ipExit = ipParas.exit().transition().remove();
}

let dlPacketIPCallback = function(dlPacket) {

      let s = makeString(dlPacket.data, 0, dlPacket.dataSize);
      let ipjson = JSON.parse(s);
      ipJsonList.unshift(ipjson);// adds to beginning
      if (ipJsonList.length > 15) {
        ipJsonList.pop(); //removes last element
      }
      drawIP(ipJsonList);
      // only do update if the IP has changed

      // let PIkey = ipjson.station;
      // let ip = ipjson.ip;
      // let piTime = ipjson.time;
      // d3.select("div.ip").insert("p",":first-child").text(`PI=${PIkey}, IP=${ip}, pitime:${piTime} serverTime: ${moment.utc().toISOString()}`);
    }




let dlCallback = function(dlPacket) {
    if (dlPacket.streamId.endsWith("IP")) {
    dlPacketIPCallback(dlPacket);
  }
};





doDatalinkConnect()
