
// seisplotjs comes from the seisplotjs standalone bundle
var wp = seisplotjs.waveformplot;
var traveltime = seisplotjs.traveltime;
var fdsnevent = seisplotjs.fdsnevent;
var fdsnstation = seisplotjs.fdsnstation;
var miniseed = seisplotjs.miniseed;
var RSVP = fdsnstation.RSVP;
var USGS = "earthquake.usgs.gov";
var IRIS = "service.iris.edu";

fdsnstation.RSVP.on('error', function(reason) {
  console.assert(false, reason);
});
var protocol = 'http:';
if ("https:" == document.location.protocol) {
  protocol = 'https:'
}
console.log("Protocol: "+protocol);

//var seismograph;


//############ Change stuff here ##############
var staList = [ 'XB03', 'XB08', 'XB05', 'XB10'];
staList = [ 'UNKNW'];
var chanList = ['HNZ', 'HNX', 'HNY'];
var jday = 281;
var hour = 17;
//########################################


var dayDir = 'Day_'+jday;



var parseAndPlot = function(arrayB, svgDiv) {

    console.log("file loaded "+arrayB.byteLength);
    let miniseed = wp.miniseed;
    let dataRecords = [];
    if (arrayB.byteLength > 0) {
      dataRecords = miniseed.parseDataRecords(arrayB);
    }
    console.log("found "+dataRecords.length+" "+arrayB.byteLength);
    let byChannel = miniseed.byChannel(dataRecords);
    let keys = Array.from(byChannel.keys());
    let segments = [];
    for(let i=0; i<keys.length; i++) {
      let key = keys[i];
      segments.push(miniseed.merge(byChannel.get(key)));
    }
    // gain correction
    for(let seisA of segments) {
      for(let seis of seisA) {
        console.log("seisi "+seis);
        for(let n=0; n<seis.y.length; n++) {
          seis.y[n] = seis.y[n]/4096*9.80665;
        }
        seis.yUnit = 'm/s^2';
        inst =
      }
    }
    //let svgParent = wp.d3.select("div.seismograms");
    let svgParent = svgDiv;
    let seismograph;
    if (segments.length > 0) {
      //svgParent.selectAll("p").remove();
      let s = segments[0];
      let svgDiv = svgParent.append("div");
      let startDate = null;
      let endDate = null;
      svgDiv.classed("svg-container-wide", true);
      if ( ! seismograph) {
        seismograph = new wp.Seismograph(svgDiv, s);
        //seismograph.svg.classed("overlayPlot", true);// for css styling
      } else {
        seismograph.append(s);//append first one
      }
      for ( let i=1; i< segments.length; i++) {
        seismograph.append(segments[i]);
      }
      seismograph.draw();
    } else {
      svgParent.append('p').text("No Data");
    }
}

var doFetch = function(mseedName, svgDiv) {
  return fetch(mseedName)
  .then(request => {
            if (request.ok && request.status == 200) {
              return request.arrayBuffer();
            } else {
              throw new Error("no data returned: "+request.status);
            }
          })
          .then(arrayB => {
            parseAndPlot(arrayB, svgDiv);
          }).catch(err => {
            let svgParent = wp.d3.select("div.seismograms");
            svgParent.append('p').text("No Data for "+mseedName);
            svgParent.append('p').text(err);
            console.assert(true, err);
          });
}

for( let s of staList) {
for (let c of chanList) {
  let seisDiv = wp.d3.select("div.seismograms");
    console.log("appending div for station "+s+"."+c)
    let svgParent = seisDiv.append('div')
    svgParent.classed(true, s+"."+c);
  svgParent.append("p").text("channel: "+s+"."+c);
    // already in Data
    let mseedName = dayDir+'/'+s+'.'+c+'_'+jday+'_'+hour+'.mseed';
    doFetch(mseedName, svgParent);
  }
}
