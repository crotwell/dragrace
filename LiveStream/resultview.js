

let wp = seisplotjs.waveformplot;
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
            console.log(`fetchHeatResult ${day}, ${classname}, ${heatname} ${result}`)
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
            let datasetNow = [result.peakACC_FL,result.peakACC_NL,result.peakACC_NR,result.peakACC_FR];
            let accText = `max: ${floatFormat(Math.max(...datasetNow))} of ${floatFormat(result.peakACC_FL)}, ${floatFormat(result.peakACC_NL)}, ${floatFormat(result.peakACC_NR)}, ${floatFormat(result.peakACC_FR)}`
            cR.select("div.maxacc").select("span").text(accText);

            let equalizer = new Equalizer("div.equalizer");
            let eqMap = createEqualizerMap(result)
            equalizer.updateEqualizer(eqMap);
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
  let staList = ['FL','NL','NR','FR'];
  let chanList = ['HNX', 'HNY', 'HNZ'];
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

  let net = new seisplotjs.model.Network("XX");
  let LOC = "00";
  let chanTR = [];
  for (let sta of staList) {
    let staObj = new seisplotjs.model.Station(net, sta);
    for (let chan of chanList) {
      let chanObj = new seisplotjs.model.Channel(staObj, chan, LOC);
      chanTR.push({
            channel: chanObj,
            startTime: moment(result.Trigger_Info.startTime),
            endTime: moment(result.Trigger_Info.endTime)
          });
    }
  }
  mseedQ.loadTraces(chanTR)
  .then(traceMap => {
    let seisPlotConfig = new wp.SeismographConfig();
    seisPlotConfig.doRMean = false;
    let seisDiv = seisplotjs.d3.select("div.seismograms");

    traceMap.forEach((trace, key) => {
      console.log(`traceMap: ${key}`);
      // let subDiv = seisDiv.append("div");
      // let seisPlot = new wp.CanvasSeismograph(subDiv,
      //     seisPlotConfig,
      //     trace, moment(result.Trigger_Info.startTime),
      //     moment(result.Trigger_Info.endTime));
      // seisPlot.draw();
    });
    let staMax = new Map();
    let traceMax = 0;
    for (let sta of staList) {
      let x = traceMap.get(`XX.${sta}.00.HNX`);
      let y = traceMap.get(`XX.${sta}.00.HNY`);
      let z = traceMap.get(`XX.${sta}.00.HNZ`);
      let max = 0;
      if (x && y && z){
        for (let s=0; s<x.segments.length; s++) {
          for (let i=0; i<x.segments[s].y.length; i++) {
            traceMax = Math.max(traceMax, Math.max(...x.segments[s].y));
            traceMax = Math.max(traceMax, Math.max(...y.segments[s].y));
            traceMax = Math.max(traceMax, Math.max(...z.segments[s].y));
            let vec = x.segments[s].y[i]*x.segments[s].y[i]
            +y.segments[s].y[i]*y.segments[s].y[i]
            +z.segments[s].y[i]*z.segments[s].y[i];
            vec = Math.sqrt(vec);
            if (vec > max) {
              max = vec;
            }
          }
        }
      }
      staMax.set(sta, max);
      console.log(`${sta}  max: ${max}`);
    }
    seisPlotConfig.fixedYScale([ -1*traceMax, traceMax]);
    for (let sta of staList) {
      let staDiv = seisDiv.append("div").classed(sta, true);
      for (let chan of chanList) {
        let k = `XX.${sta}.00.${chan}`;
        let trace = traceMap.get(k);
        console.log(`${k}  trace: ${trace}`);
        if (trace) {
          let subDiv = staDiv.append("div").classed(chan, true);
          let seisPlotConfigClone = seisPlotConfig.clone();
          seisPlotConfigClone.xLabel = `${sta} ${chan} ${staMax.get(sta)}`;
          let seisPlot = new wp.CanvasSeismograph(subDiv,
              seisPlotConfigClone,
              trace, moment(result.Trigger_Info.startTime),
              moment(result.Trigger_Info.endTime));
          seisPlot.draw();
        }
      }
    }

  });
};


console.log(window.location);
let url = new URL(window.location);
let params = (new URL(document.location)).searchParams;
let day = params.get('day');
if ( ! day) {
  day = moment().format("dddd");
}
let classname = params.get('class');
let heatname = params.get('heat');
console.log(`class: ${classname}  heat: ${heatname}`);
updateClassHeat(day, classname, heatname);
