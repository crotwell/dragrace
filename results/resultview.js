

let d3 = seisplotjs.d3;
let moment = seisplotjs.moment;
let datalink = seisplotjs.datalink


let updateClassHeat = function(day, classname, heatname) {
  if (day) {
    let cR = d3.select("div.currentRace");
    cR.select("span.dayName").select("a").attr("href", d =>  {
        let url = new URL(window.location);
        let searchParams = new URLSearchParams(url.search);
        searchParams.delete("class");
        searchParams.delete("heat");
        url.search = searchParams.toString();
        return url.toString();
      }).text(day);
  }
  if (classname) {
    if (heatname) {
      let result = fetchHeatResult(day, classname, heatname)
          .then(function(result) {
            console.log(`fetchHeatResult ${day}, ${classname}, ${heatname} ${result}`);
            heatResult = result;
            let floatFormat = d3.format(".2f");
            let cR = d3.select("div.currentRace");
            cR.select("span.dayName").select("a").attr("href", d =>  {
                let url = new URL(window.location);
                let searchParams = new URLSearchParams(url.search);
                searchParams.delete("class");
                searchParams.delete("heat");
                url.search = searchParams.toString();
                return url.toString();
              }).text(`${result.Day_Name}`);
            cR.select("div.start_time").select("span").text(`${result.Trigger_Info.startTime}`);
            cR.select("div.end_time").select("span").text(`${result.Trigger_Info.endTime}`);
            cR.select("div.race_class").select("span").text(`${result.Trigger_Info.class}`);
            cR.select("div.race_class").select("a").attr("href", d =>  {
                let url = new URL(window.location);
                let searchParams = new URLSearchParams(url.search);
                searchParams.set("class", result.Trigger_Info.class);
                searchParams.delete("heat");
                url.search = searchParams.toString();
                return url.toString();
              });
            let heatDiv = cR.select("div.race_heat");
            heatDiv.select("span").text(`${result.Trigger_Info.heat}`);
            cR.select("div.dutyOfficer").select("span").text(`${result.Trigger_Info.dutyOfficer}`);

            let max = Math.max(...Object.values(result.peakACC));
            console.log(`max peakAcc: ${max}`)
            let staList = Array.from(Object.keys(result.peakACC));
            let accText = staList.reduce((acc,s) => acc+` ${s}:${floatFormat(result.peakACC[s])}`, "")
            accText = `max: ${floatFormat(max)} of ${accText}}`
            cR.select("div.maxacc").select("span").text(accText);

            let eqMap = createEqualizerMap(result)
            lastRaceEqualizer.updateEqualizer(eqMap);
            loadSeismograms(result);
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
      } else {
        fetchHeatnames(day, classname)
        .then(function(heatnames) {
          console.log(`heatnames: len=${heatnames.length}`);
          for (let h of heatnames) {
            console.log(`heat: ${h}`);
          }
          d3.select("div.navlist").selectAll("div").data(heatnames)
          .join("div")
            .append("a").attr("href", d =>  {
              let url = new URL(window.location);
              let searchParams = new URLSearchParams(url.search);
              searchParams.set("heat", d);
              url.search = searchParams.toString();
              return url.toString();
            })
            .text(d => { return d;});
        }).catch(function(err) {
            console.error(err);
        });
      }
    } else {
      fetchClassnames(day)
      .then(function(classnames) {
        console.log(`classnames: len=${classnames.length}`);
        for (let c of classnames) {
          console.log(`class: ${c}`);
        }
        d3.select("div.navlist").selectAll("div").data(classnames)
        .join("div")
          .append("a").attr("href", d =>  {
            let url = new URL(window.location);
            let searchParams = new URLSearchParams(url.search);
            searchParams.set("class", d);
            searchParams.delete("heat");
            url.search = searchParams.toString();
            return url.toString();
          })
          .text(d => { return d;});
      }).catch(function(err) {
          console.error(err);
      });
    }
}

let loadSeismograms = function(result) {
  let staList = ['FL','NL', 'FL0', 'FL4G', 'FL60', 'FL330', 'FL660', 'FL1K'];
  let chanList = ['HNM', 'HNX', 'HNY', 'HNZ'];
  let protocol = 'http:';
  if ("https:" == document.location.protocol) {
    protocol = 'https:'
  }
  const host = document.location.hostname;
  let subdir = ""
  if (host === 'www.seis.sc.edu') {
    subdir = "dragrace";
  }
  let mseedQ = new seisplotjs.mseedarchive.MSeedArchive(
    `${protocol}//${host}/${subdir}`,
    "%n/%s/%Y/%j/%n.%s.%l.%c.%Y.%j.%H");

  let net = new seisplotjs.stationxml.Network("XX");
  let LOC = "00";
  let chanTR = [];
  for (let sta of staList) {
    let staObj = new seisplotjs.stationxml.Station(net, sta);
    for (let chan of chanList) {
      let chanObj = new seisplotjs.stationxml.Channel(staObj, chan, LOC);
      let timeWindow = new seisplotjs.util.StartEndDuration(moment(result.Trigger_Info.startTime),
          moment(result.Trigger_Info.endTime));
      chanTR.push(seisplotjs.seismogram.SeismogramDisplayData.fromChannelAndTimeWindow(
            chanObj, timeWindow));
    }
  }
  return mseedQ.loadSeismograms(chanTR)
  .then(sddList => {
    resultsSddList = sddList;
    let seisPlotConfig = new seisplotjs.seismographconfig.SeismographConfig();
    seisPlotConfig.doRMean = false;
    let maxaccsSeisPlotConfig = seisPlotConfig.clone();
    let seisDiv = seisplotjs.d3.select("div.seismograms");

    sddList.forEach(sdd => {
      console.log(`traceMap: ${sdd.channel.codes()}`);
      // let subDiv = seisDiv.append("div");
      // let seisPlot = new wp.CanvasSeismograph(subDiv,
      //     seisPlotConfig,
      //     trace, moment(result.Trigger_Info.startTime),
      //     moment(result.Trigger_Info.endTime));
      // seisPlot.draw();
    });
    let staVecMax = new Map();
    let traceMax = 0;
    let maxaccMax = 0;
    for (let sta of staList) {
      let m = sddList.find(sdd => sdd.channel.station.stationCode === sta && sdd.channel.channelCode === "HNM");
      if (m) {
        maxaccMax = Math.max(maxaccMax, Math.abs(m.min),Math.abs(m.max));
      }
      let x = sddList.find(sdd => sdd.channel.station.stationCode === sta && sdd.channel.channelCode === "HNX");
      let y = sddList.find(sdd => sdd.channel.station.stationCode === sta && sdd.channel.channelCode === "HNY");
      let z = sddList.find(sdd => sdd.channel.station.stationCode === sta && sdd.channel.channelCode === "HNZ");

      let max = 0;
      if (x && y && z){
        traceMax = Math.max(traceMax,  Math.abs(x.min),Math.abs(x.max));
        traceMax = Math.max(traceMax,  Math.abs(y.min),Math.abs(y.max));
        traceMax = Math.max(traceMax,  Math.abs(z.min),Math.abs(z.max));
        for (let s=0; s<x.seismogram.segments.length; s++) {
          for (let i=0; i<x.seismogram.segments[s].y.length; i++) {
            let vec = x.seismogram.segments[s].y[i]*x.seismogram.segments[s].y[i]
            +y.seismogram.segments[s].y[i]*y.seismogram.segments[s].y[i]
            +z.seismogram.segments[s].y[i]*z.seismogram.segments[s].y[i];
            if (vec > max) {
              max = vec;
            }
          }
        }
      }
      staVecMax.set(sta, Math.round(Math.sqrt(max)));
      console.log(`${sta}  max: ${max}`);
    }
    maxaccsSeisPlotConfig.fixedYScale = [ -1*maxaccMax, maxaccMax];
    seisPlotConfig.fixedYScale = [ -1*traceMax, traceMax];
    for (let sta of staList) {
      let staDiv = seisDiv.append("div").classed(sta, true);
      for (let chan of chanList) {
        let k = `XX.${sta}.00.${chan}`;
        let sdd = sddList.find(sdd => sdd.channel.station.stationCode === sta && sdd.channel.channelCode === chan);

        console.log(`${k}  trace: ${sdd}`);
        if (sdd) {
          let subDiv = staDiv.append("div").classed(chan, true);
          let seisPlotConfigClone = seisPlotConfig.clone();
          if (chan.endsWith('HNM')) {
            seisPlotConfigClone = maxaccsSeisPlotConfig.clone();
            seisPlotConfigClone.xLabel = `${sta} ${chan} chan:${sdd.max} `;
          } else {
            seisPlotConfigClone.xLabel = `${sta} ${chan} chan:${sdd.max} staVec:${staVecMax.get(sta)}`;
          }
          let seisPlot = new seisplotjs.seismograph.Seismograph(subDiv,
              seisPlotConfigClone,
              sdd);
          seisPlot.draw();
          allSeisPlots.forEach(sp => seisPlot.linkXScaleTo(sp));
          allSeisPlots.forEach(sp => seisPlot.linkYScaleTo(sp));
          allSeisPlots.push(seisPlot);
        }
      }
    }

  });
};

let plotTimeAdjust = function(adjType) {
  console.log(`plotTimeAdjust(${adjType})`)
  for (let seisplot of allSeisPlots) {
    let s = moment.utc(seisplot.xScale.domain()[0]);
    let e = moment.utc(seisplot.xScale.domain()[1]);
    console.log(`s: ${s.toISOString()}   e: ${e.toISOString()}`)
    let dur = moment.duration(e.diff(s));
    let halfDur = moment.duration(dur.asMilliseconds()/2);//milliseconds
    let quarterDur = moment.duration(halfDur.asMilliseconds()/2);//milliseconds

    console.log(`dur: ${dur.seconds()}   quarter: ${quarterDur.seconds()}`);
    if (adjType === "zoomLeft") {
      s.add(quarterDur);
      e.add(quarterDur);
      seisplot.setPlotStartEnd(s,e);
    } else if (adjType === "zoomIn") {
      s.add(quarterDur);
      e.subtract(quarterDur);
      seisplot.setPlotStartEnd(s,e);
      console.log(`After:${s} ${e}  ${seisplot.xScale.domain()}`)
    } else if (adjType === "zoomOut") {
      s.subtract(quarterDur);
      e.add(quarterDur);
      seisplot.setPlotStartEnd(s,e);
      console.log(`After:${s} ${e}  ${seisplot.xScale.domain()}`)
    } else if (adjType === "zoomRight") {
      s.subtract(quarterDur);
      e.subtract(quarterDur);
      seisplot.setPlotStartEnd(s,e);
    }

  }
};

d3.select("button#replay").on("click", function(d) {
  replayEqualizer(lastRaceEqualizer, heatResult, resultsSddList);
});

// equalizer scale buttons
const updateYScale = function(gValue) {
  seisGraphMax = gValue;
  if (lastRaceEqualizer) {
    lastRaceEqualizer.updateMaxG(gValue);
  }
  allSeisPlots.forEach(function(value, key) {
      value.seismographConfig.fixedYScale = [-0.1, gValue*4096];
      value.calcAmpScaleDomain();
      value.draw();
  });
}
d3.select("button#halfG").on("click", function(d) {
  console.log("buttonclick "+d);
  updateYScale(0.5);
});
d3.select("button#oneAndHalfG").on("click", function(d) {
  console.log("buttonclick "+d);
  updateYScale(1.5);
});
d3.select("button#twoG").on("click", function(d) {
  console.log("buttonclick "+d);
  updateYScale(2.0);
});
d3.select("button#threeG").on("click", function(d) {
  console.log("buttonclick "+d);
  updateYScale(3.0);
});


console.log(window.location);
let url = new URL(window.location);
let params = (new URL(document.location)).searchParams;
let day = params.get('day');
if ( ! day) {
  day = moment().format("dddd");
}
let classname = params.get('class');
let heatname = params.get('heat');
let lastRaceEqualizer = new Equalizer("div.raceEqualizer");
let allSeisPlots = [];
let resultsSddList = [];
console.log(`class: ${classname}  heat: ${heatname}`);
updateClassHeat(day, classname, heatname);
