
const replayEqualizer = function(equalizer, result, sddList) {
  if ( ! equalizer) {console.log("need equalizer for replay");}
  if ( ! result) {console.log("need result for replay");}
  if ( ! sddList) {console.log("need sddList for replay");}
  let startTime = moment.utc(result.Trigger_Info.startTime);
  let endTime = moment.utc(result.Trigger_Info.endTime);
  console.log(`replayEqualizer  ${startTime} ${endTime}`);
  replayEqualizerStep(equalizer, result, sddList, startTime, endTime);
}

const replayEqualizerStep = function(equalizer, result, sddList, time, endTime) {
  let stepData = equalizer.createZeros();
  sddList.forEach(sdd => {
    let d = stepData.get(sdd.seismogram.stationCode);
    d.end_time = time;
    let seg = sdd.seismogram.segments.find(seg => seg.startTime.isSameOrBefore(time)
                                                  && seg.endTime.isSameOrAfter(time));
    if (seg) {
      let idx = Math.ceil(time.diff(seg.startTime)/1000 * seg.sampleRate);
      d.maxacc = seg.yAtIndex(idx) / 4096;
    }
  });
  equalizer.updateEqualizer(stepData);
  time.add(250, 'milliseconds');
  if (time.isSameOrBefore(endTime)) {
    window.setTimeout(replayEqualizerStep, 250, equalizer, result, sddList, time, endTime);
  } else {
    let eqMap = createEqualizerMap(result)
    equalizer.updateEqualizer(eqMap);
  }
}
