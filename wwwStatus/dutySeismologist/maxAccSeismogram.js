let makeSeismogram = function(maxacc) {


let sampleRate = 4;

let seismogram = seisplotjs.seismogram.Seismogram.createFromContiguousData([maxacc.maxacc], sampleRate, moment.utc(maxacc.start_time));
    seismogram.networkCode = "XX";
    seismogram.stationCode = maxacc.station;
    seismogram.locationCode = "  ";
    seismogram.channelCode = "ACC";
    seismogram.yUnit = "g";

return seismogram;



//allSeisPlots.get(seismogram.codes()).append(seismogram);
}
