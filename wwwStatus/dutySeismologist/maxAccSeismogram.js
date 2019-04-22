let makeSeismogram = function(maxacc) {


let sampleRate = 4;

let seismogram = new seisplotjs.model.Seismogram([maxacc.maxacc,maxacc.maxacc],sampleRate,moment.utc(maxacc.end_time));
    seismogram.networkCode = "XX";
    seismogram.stationCode = maxacc.station;
    seismogram.locationCode = "  ";
    seismogram.channelCode = "ACC";
    seismogram.yUnit = "g";

return seismogram;



//allSeisPlots.get(seismogram.codes()).append(seismogram);
}
