// @flow
// test radial transverse plotStartDate



// just to get flow working...
//import * as seisplotjs from '../../src/index';

// seisplotjs comes from the seisplotjs standalone bundle
let wp = seisplotjs.waveformplot
let d3 = wp.d3;
let traveltime = seisplotjs.traveltime;
let fdsnevent = seisplotjs.fdsnevent;
let fdsnstation = seisplotjs.fdsnstation;
let miniseed = seisplotjs.miniseed;
let filter = seisplotjs.filter;


fdsnstation.RSVP.on('error', function(reason) {
  console.assert(false, reason);
});

function loadData() {
  let hash = {}
  hash.svgParent = seisplotjs.d3.select("div.seismograms");
  hash.svgParent.selectAll('div').remove();
  hash.stations = document.getElementsByName('sta')[0].value.split(',');
  // dayOfY and hour need 0 if not 3/2 digits
  hash.doNow = document.getElementsByName('doNow')[0].checked;
  hash.year = document.getElementsByName('year')[0].value;
  hash.month = document.getElementsByName('month')[0].value;
  hash.day = document.getElementsByName('day')[0].value;
  hash.hour = document.getElementsByName('hour')[0].value;
  hash.min = parseInt(document.getElementsByName('min')[0].value, 0);
  hash.sec = parseInt(document.getElementsByName('sec')[0].value, 0);
  hash.durMin = parseFloat(document.getElementsByName('dur')[0].value, 10);
  hash.channels = document.getElementsByName('channels')[0].value.split(',');
  hash.doRmean = document.getElementsByName('doRmean')[0].checked;
  hash.doGain = document.getElementsByName('doGain')[0].checked;
  hash.doTen = document.getElementsByName('doTen')[0].checked;
  hash.doOverlay = document.getElementsByName('doOverlay')[0].checked;
  let clockOffset = 0;

  if (hash.doNow) {
    end = moment.utc();
    start = null;
  } else {
    let isoStr = `${hash.year}-${hash.month}-${hash.day}T${hash.hour}:${hash.min}:00`;
    seisplotjs.d3.select("#error").text(isoStr);
    start = moment.utc();
    start.year(hash.year);
    start.month(hash.month-1);
    start.date(hash.day);
    start.hour(hash.hour);
    start.minute(hash.min);
    start.second(hash.sec);
    start.millisecond(0);
    end = null;
  }
  hash.timeWindow = seisplotjs.fdsndataselect.calcStartEndDates(start, end, hash.durMin*60, clockOffset);
  seisplotjs.d3.select("#start").text(hash.timeWindow.start.toISOString());
  seisplotjs.d3.select("#end").text(hash.timeWindow.end.toISOString());
  console.log("Gain: "+hash.doGain);
  hash.chanTR = [];


  let netCO = new seisplotjs.model.Network("CO");
  let netXX = new seisplotjs.model.Network("XX");
  let LOC = "00";
  for (let sta of hash.stations) {
    let net = netXX;
    if (sta === "3605") { net = netCO;}
    let staObj = new seisplotjs.model.Station(net, sta);
    for (let chan of hash.channels) {
      let chanObj = new seisplotjs.model.Channel(staObj, chan, LOC);
      hash.chanTR.push({
            channel: chanObj,
            startTime: hash.timeWindow.start,
            endTime: hash.timeWindow.end
          });
    }
  }

  let mseedQ = new seisplotjs.seedlink.MSeedArchive(
    "http://dragrace.seis.sc.edu/mseed",
    "%n/%s/%Y/%j/%n.%s.%l.%c.%Y.%j.%H");
  hash.traceMap = mseedQ.loadTraces(hash.chanTR);
  return seisplotjs.RSVP.hash(hash)
  .then(hash => {

      if (hash.traceMap.size == 0) {
        hash.svgParent.append("p").text("No Data Found").style("color", "red");
        console.log("data from miniseedArchive found none");

      }




      console.log(`HASH doOverlay: ${hash.doOverlay}`)
      if (hash.doOverlay) {
              let plotDiv = hash.svgParent.append("div");
              plotDiv.style("position", "relative");
              plotDiv.style("width", "100%");
              plotDiv.style("height", "450px");
        let seisPlotConfig = new wp.SeismographConfig();
        let traceList = []
        hash.traceMap.forEach((value, key) => {
          traceList.push(value)
        });
        let seisPlot = new wp.CanvasSeismograph(plotDiv,
            seisPlotConfig,
            traceList, hash.timeWindow.start, hash.timeWindow.end);
        seisPlot.draw();

      } else {

        let seisPlotList = []
        hash.traceMap.forEach((value, key) => {

          let plotDiv = hash.svgParent.append("div");
          plotDiv.style("position", "relative");
          plotDiv.style("width", "100%");
          plotDiv.style("height", "450px");
          let seisPlotConfig = new wp.SeismographConfig();
          seisPlotConfig.disableWheelZoom = false;
          seisPlotConfig.doRMean = hash.doRMean;
          seisPlotConfig.doGain = hash.doGain;
          seisPlotConfig.xLabel = key;
          let seisPlot = new wp.CanvasSeismograph(plotDiv,
              seisPlotConfig,
              value, hash.timeWindow.start, hash.timeWindow.end);
          seisPlot.draw();
          seisPlotList.push(seisPlot);
        });
      }

  });
}
