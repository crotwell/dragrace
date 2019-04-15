
//to dos: append miniseed and takes in miniseed and maxacc packet
//new maxacc dlCallback

//source: seisplotjs/miniseed.js version2.0 on crotwell

//create new header with specifics
//maxacc value comes from maxacc.station
//convert Btime?
header(new convertMSeed){
  header.staCode = 'maxacc.station';
  header.chanCode = 'ACC';
  header.sampRateFac = 4;
  header.locCode = '00';
  header.netCode = 'xx';
  header.startBTime = new BTime(start);
  header.start = header.startBTime.toMoment();
  header.numSamples = 1;
  header.sampMul = 1;
  header.end = model.moment.utc(header.start);
}

//create a datarecord to send the data
create dataRecord(header:convertMSeed,data:null)
dataRecord.decompData = maxacc.station;
//receive the data in a callback
let dlConvertMSeedCallback = function(convertMSeed) {
  convertMSeed(header.staCode);
};
//append the data to graph it as miniseed
append.(header.staCode);
