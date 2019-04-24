//let datalink = seisplotjs.datalink


//let wp = require('seisplotjs-waveformplot');
// this global comes from the seisplotjs_waveformplot standalone js
let d3 = seisplotjs.d3;
let moment = seisplotjs.moment;



let trig = {
  "start":"20190419T15:43:22Z",
  "end":"20190419T15:55:22Z",
  "class":"funnyCars",
  "heat":"one",
  "officer":"Gabby"
};
let day = "Wednesday";
fetch(`http://www.seis.sc.edu/dragrace/www/results/${day}/classnames.json`)
  .then(function(response){
    return response.json();
  })
  .then(function(classnames) {
    for (let c of classnames){

      fetch(`http://www.seis.sc.edu/dragrace/www/results/${day}/${c}/heatnames.json`)
        .then(function(response){
          return response.json();
        })
        .then(function(heatnames) {
            for (let h of heatnames){

          fetch(`http://www.seis.sc.edu/dragrace/www/results/${day}/${c}/${h}/results.json`)
            .then(function(response){
              return response.json();
            })
            .then(function(result) {
              d3.select("div.currentRace").select("div.start_time").text(`Start Time = ${result.Trigger_Info.startTime}`);
              d3.select("div.currentRace").select("div.end_time").text(`End Time = ${result.Trigger_Info.endTime}`);
              d3.select("div.currentRace").select("div.race_class").text(`Class = ${result.Trigger_Info.class}`);
              d3.select("div.currentRace").select("div.race_heat").text(`Heat = ${result.Trigger_Info.heat}`);
              d3.select("div.currentRace").select("div.dutyOfficer").text(`Duty Officer = ${result.Trigger_Info.dutyOfficer}`);
              let datasetNow = [result.peakACC_FL,result.peakACC_NL,result.peakACC_NR,result.peakACC_FR];
              d3.select("div.currentRace").select("div.maxacc").text(`Ground Acceleration = ${datasetNow[1]}`);
              let equalizer = new Equalizer("div.equalizer");
              let eqMap = createEqualizerMap(result)
              equalizer.updateEqualizer(eqMap);



            });
          }
        });
      }
    });

    createEqualizerMap = function(result){
      let dataset=new Map();
      dataset.set("FL",{'station':'FL','maxacc':result.peakACC_FL});
      dataset.set("NL",{'station':'NL','maxacc':result.peakACC_NL});
      dataset.set("NR",{'station':'NR','maxacc':result.peakACC_NR});
      dataset.set("FR",{'station':'FR','maxacc':result.peakACC_FR});
      return dataset;
    }
