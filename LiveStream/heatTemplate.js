let datalink = seisplotjs.datalink


//let wp = require('seisplotjs-waveformplot');
// this global comes from the seisplotjs_waveformplot standalone js
let wp = seisplotjs.waveformplot;
let d3 = seisplotjs.d3;
let moment = seisplotjs.moment;



let trig = {
  "start":"20190419T15:43:22Z",
  "end":"20190419T15:55:22Z",
  "class":"funnyCars",
  "heat":"one",
  "officer":"Gabby"
};

fetch('http://www.seis.sc.edu/dragrace/www/results/data/Friday/TopFuel/Heat1/trigger.json')
  .then(function(response){
    return response.json();
  })
  .then(function(trig) {
    wp.d3.select("div.currentRace").select("div.start_time").attr(`title`,`Start Time = ${`start`}`);
    wp.d3.select("div.currentRace").select("div.end_time").attr(`title`,`End Time = ${`end`}`);
    wp.d3.select("div.currentRace").select("div.race_class").attr(`title`,`Class = ${`class`}`);
    wp.d3.select("div.currentRace").select("div.race_heat").attr(`title`,`Heat = ${`heat`}`);
    wp.d3.select("div.currentRace").select("div.dutyOfficer").attr(`title`,`Duty Officer = ${`officer`}`);

  })
