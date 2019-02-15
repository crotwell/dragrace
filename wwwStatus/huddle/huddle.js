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


const SENSORS_GRAVITY_EARTH     = 9.80665;
const EPISENSOR_4G_Q330_SENSITIVITY = new seisplotjs.model.InstrumentSensitivity(213909.0, 0, "m/s/s", "count")
const EPISENSOR_2G_Q330_SENSITIVITY = new seisplotjs.model.InstrumentSensitivity(427692.8, 0, "m/s/s", "count")
const MMA8451_2G_SENSITIVITY = new seisplotjs.model.InstrumentSensitivity(4096.0/SENSORS_GRAVITY_EARTH, 0, "m/s/s", "count")



function loadData() {
  let hash = {}
  hash.svgParent = seisplotjs.d3.select("div.seismograms");
  hash.svgParent.selectAll('div').remove();
  seisplotjs.d3.select("div.fftplot").selectAll("svg").remove();
  seisplotjs.d3.select("#minmax").selectAll("li").remove();
  seisplotjs.d3.select("div.message").selectAll("p").remove();
  seisplotjs.d3.select("div.message").append("p").classed("loading", true).text("Loading Data...");
  hash.stations = document.getElementsByName('sta')[0].value.split(',');
  // dayOfY and hour need 0 if not 3/2 digits
  hash.doNow = document.getElementsByName('doNow')[0].checked;
  hash.year = document.getElementsByName('year')[0].value;
  hash.month = document.getElementsByName('month')[0].value;
  hash.day = document.getElementsByName('day')[0].value;
  hash.hour = document.getElementsByName('hour')[0].value;
  hash.min = parseInt(document.getElementsByName('min')[0].value, 0);
  hash.sec = parseFloat(document.getElementsByName('sec')[0].value, 0);
  hash.durMin = parseFloat(document.getElementsByName('dur')[0].value, 10);
  hash.channels = document.getElementsByName('channels')[0].value.split(',');
  hash.doRMean = document.getElementsByName('doRMean')[0].checked;
  hash.doGain = document.getElementsByName('doGain')[0].checked;
  hash.doTaper = document.getElementsByName('doTaper')[0].checked;
  hash.doFFT = document.getElementsByName('doFFT')[0].checked;
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
    start.second(0);
    start.millisecond(hash.sec*1000);
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
  let protocol = 'http:';
  if ("https:" == document.location.protocol) {
    protocol = 'https:'
  }
  const host = document.location.hostname;
  let subdir = "mseed"
  if (host === 'www.seis.sc.edu') {
    subdir = "dragrace";
  }
  let mseedQ = new seisplotjs.seedlink.MSeedArchive(
    `${protocol}//${host}/${subdir}`,
    "%n/%s/%Y/%j/%n.%s.%l.%c.%Y.%j.%H");
  hash.traceMap = mseedQ.loadTraces(hash.chanTR);
  return seisplotjs.RSVP.hash(hash)
  .then(hash => {
    if (hash.doGain) {
      let outMap = new Map()
      hash.traceMap.forEach((value, key) => {
        // 2G for MMA8451 (14 bit) => gain = 4096 counts per 9.8 m/s/s
        let instSensitivity = MMA8451_2G_SENSITIVITY;
        if (key.startsWith("CO")) {
          // assume episensor, 2G => gain = 427692.8 counts per m/s/s
          // assume episensor, 4G => gain = 213909.0 counts per m/s/s
          instSensitivity = EPISENSOR_4G_Q330_SENSITIVITY;
        }
        let trace = seisplotjs.filter.gainCorrect(instSensitivity, value)
        outMap.set(key, trace);

      });
      hash.traceMap = outMap;
    }
    return seisplotjs.RSVP.hash(hash);
  }).then(hash => {
    if (hash.doRMean) {
      let outMap = new Map()
      hash.traceMap.forEach((value, key) => {
        let trace = seisplotjs.filter.rMean(value)
        outMap.set(key, trace);
      });
      hash.traceMap = outMap;
    }
    return hash;
  }).then(hash => {
      if (hash.traceMap.size == 0) {
        seisplotjs.d3.select("div.message").append("p").text("No Data Found").style("color", "red");
        console.log("data from miniseedArchive found none");
        return hash;
      }
      seisplotjs.d3.select("div.message").selectAll("p.loading").remove();

      console.log(`HASH doOverlay: ${hash.doOverlay}`)
      if (hash.doOverlay) {
              let plotDiv = hash.svgParent.append("div");
              plotDiv.style("position", "relative");
              plotDiv.style("width", "100%");
              plotDiv.style("height", "450px");
        let seisPlotConfig = new wp.SeismographConfig();
        if (hash.doRMean) {
          seisPlotConfig.doRMean = hash.doRMean;
        }

        let traceList = []
        hash.traceMap.forEach((value, key) => {
          traceList.push(value);
          seisPlotConfig.ySublabelIsUnits = true;
          seisPlotConfig.ySublabel = "";
          //seisPlotConfig.ySublabel += ` ${value.yUnit}`;
        });
        let seisPlot = new wp.CanvasSeismograph(plotDiv,
            seisPlotConfig,
            traceList, hash.timeWindow.start, hash.timeWindow.end);
        seisPlot.draw();

      } else {

        let seisPlotList = []
        hash.traceMap.forEach((trace, key) => {
          if (hash.doFFT) {
            let plotDiv = hash.svgParent.append("div");
            let trimTrace = trace.trim(hash.timeWindow);
            let dataArray;

            // this is bad as gaps may be present
            dataArray = trimTrace.seisArray.reduce((acc, s) => {
              return acc.concat(s.y);
            }, []);
            if (hash.doTaper) {
              let taperWidth = 0.05;
              let taperType = seisplotjs.filter.taper.HANNING;
              let w = Math.floor(dataArray.length * taperWidth);
              let coeff = seisplotjs.filter.taper.getCoefficients(taperType, w);
              const omega = coeff[0];
              const f0 = coeff[1];
              const f1 = coeff[2];
              for(let i = 0; i < w; i++) {
                const taperFactor = (f0 - f1 * Math.cos(omega * i));
                dataArray[i] = dataArray[i] * taperFactor;
                dataArray[dataArray.length - i - 1] = dataArray[dataArray.length - i - 1] * taperFactor;
              }

            }
            let fftOut = seisplotjs.filter.calcDFT(dataArray, dataArray.length );
            let fftSvg = wp.createSimpleFFTPlot(fftOut, "div.fftplot", trace.sampleRate);
            // wrong, but works
            let margin = {top: 20, right: 20, bottom: 30, left: 50};
            const styleWidth = 900;
            let width = +styleWidth - margin.left - margin.right;

            fftSvg.select("g")
              .append("g")
                .attr("transform", "translate("+margin.left+width/2+","+  margin.top + ")")
              .append("text")
                .attr("fill", "#000")
                .attr("y", 0)
                .attr("x", width/2)
                .attr("dy", "0.71em")
                .attr("text-anchor", "middle")
                .text(key);
          } else {
            let plotDiv = hash.svgParent.append("div");
            plotDiv.style("position", "relative");
            plotDiv.style("width", "100%");
            plotDiv.style("height", "450px");
            let seisPlotConfig = new wp.SeismographConfig();
            seisPlotConfig.disableWheelZoom = false;
            seisPlotConfig.doRMean = hash.doRMean;
            seisPlotConfig.ySublabelIsUnits = true;
            seisPlotConfig.ySublabel = "";
            //seisPlotConfig.doGain = hash.doGain;
            seisPlotConfig.xLabel = key;
            //seisPlotConfig.ySublabel = `${trace.yUnit}`;
            let seisPlot = new wp.CanvasSeismograph(plotDiv,
                seisPlotConfig,
                trace, hash.timeWindow.start, hash.timeWindow.end);
            seisPlot.draw();
            seisPlotList.push(seisPlot);
          }
        });
      }
      return hash;
    }).then(hash => {
      hash.traceMap.forEach((trace, key) => {
        minMaxMean = seisplotjs.filter.minMaxMean(trace);
        seisplotjs.d3.select("#minmax").append("li").text(`${key}   ${minMaxMean.min}     ${minMaxMean.max}      ${minMaxMean.mean}`);
      });
      return hash;
  });
}
