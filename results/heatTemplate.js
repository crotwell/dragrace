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
      let staList = Array.from(Object.keys(result.peakACC));
      let accText = staList.reduce((acc,s) => acc+` ${s}:${floatFormat(result.peakACC[s])}`, "");
      cR.select("div.maxacc").select("span").text(accText);

      let lastRaceEqualizer = new Equalizer("#lastRaceEqualizer");
      let eqMap = createEqualizerMap(result)
      lastRaceEqualizer.updateEqualizer(eqMap);
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
