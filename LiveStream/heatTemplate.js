let datalink = seisplotjs.datalink


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
let day = "Friday";
fetch(`http://www.seis.sc.edu/dragrace/www/results/data/${day}/classnames.json`)
  .then(function(response){
    return response.json();
  })
  .then(function(classnames) {
    for (let c of classnames){

      fetch(`http://www.seis.sc.edu/dragrace/www/results/data/${day}/${c}/heatnames.json`)
        .then(function(response){
          return response.json();
        })
        .then(function(heatnames) {
            for (let h of heatnames){

          fetch(`http://www.seis.sc.edu/dragrace/www/results/data/${day}/${c}/${h}/results.json`)
            .then(function(response){
              return response.json();
            })
            .then(function(trig) {
              d3.select("div.currentRace").select("div.start_time").text(`Start Time = ${trig.start}`);
              d3.select("div.currentRace").select("div.end_time").text(`End Time = ${trig.end}`);
              d3.select("div.currentRace").select("div.race_class").text(`Class = ${trig.class}`);
              d3.select("div.currentRace").select("div.race_heat").text(`Heat = ${trig.heat}`);
              d3.select("div.currentRace").select("div.dutyOfficer").text(`Duty Officer = ${trig.officer}`);

            });
          }
        });
      }
    });
})
