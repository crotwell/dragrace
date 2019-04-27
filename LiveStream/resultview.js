

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
      });
    }
}


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
