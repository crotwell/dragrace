//function and call on a refresh button

fetchCurrentResult()
    .then(function(result) {
      let d3 = seisplotjs.d3;
      let moment = seisplotjs.moment;
      let datalink = seisplotjs.datalink;
      let today = moment().format("dddd");

      let floatFormat = d3.format(".2f");
      let cR = d3.select("div.currentRace");
      cR.select("span.dayName").text(`${result.Day_Name}`);
      cR.select("div.start_time").select("span").text(`${result.Trigger_Info.startTime}`);
      cR.select("div.end_time").select("span").text(`${result.Trigger_Info.endTime}`);
      cR.select("div.race_class").select("span").text(`${result.Trigger_Info.class}`);
      let heatDiv = cR.select("div.race_heat");
      heatDiv.select("span").text(`${result.Trigger_Info.heat}`);
      cR.select("div.dutyOfficer").select("span").text(`${result.Trigger_Info.dutyOfficer}`);
      let datasetNow = [result.peakACC_FL,result.peakACC_NL,result.peakACC_NR,result.peakACC_FR];
      let accText = `max: ${floatFormat(Math.max(...datasetNow))} of ${floatFormat(result.peakACC_FL)}, ${floatFormat(result.peakACC_NL)}, ${floatFormat(result.peakACC_NR)}, ${floatFormat(result.peakACC_FR)}`
      cR.select("div.maxacc").select("span").text(accText);

      let flEqualizer = new Equalizer("#lastRaceFLequalizer", ["FL1K", "FL660", "FL330", "FL60", "FL0"]);
      let eqMap = createEqualizerMap(result)
      flEqualizer.updateEqualizer(eqMap);
      let laneEqualizer = new Equalizer("#lastRaceLaneEqualizer", ["FL", "NL"]);
      laneEqualizer.updateEqualizer(eqMap);
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

    createEqualizerMap = function(result){
      let dataset=new Map();
      dataset.set("FL",{'station':'FL','maxacc':result.peakACC_FL});
      dataset.set("NL",{'station':'NL','maxacc':result.peakACC_NL});
      dataset.set("NR",{'station':'NR','maxacc':result.peakACC_NR});
      dataset.set("FR",{'station':'FR','maxacc':result.peakACC_FR});
      dataset.set("FL1K",{'station':'FL1K','maxacc':result.peakACC_FL1K});
      return dataset;
    }
