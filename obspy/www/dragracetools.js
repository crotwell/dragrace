
const AllChanList = ['HNZ', 'HNY', 'HNX']
const FALL2019 = {
  'name': 'Fall2019',
  'starttime': seisplotjs.moment.utc('2019-284T00:00:00Z'),
  'endtime': seisplotjs.moment.utc('2019-288T00:00:00Z'),
  'staList': ['NR', 'FL', 'FL0', 'FL4G', 'FL60', 'FL330', 'FL660', 'FL1K'],
  'chanList': AllChanList
}
FALL2019.timeRange = new seisplotjs.util.StartEndDuration(FALL2019.starttime, FALL2019.endtime);
const SPRING2019 = {
  'name': 'Spring2019',
  'starttime': seisplotjs.moment.utc('2019-115T00:00:00Z'),
  'endtime': seisplotjs.moment.utc('2019-119T00:00:00Z'),
  'staList': ['FR', 'NR', 'NL', 'FL'],
  'chanList': AllChanList
}
SPRING2019.timeRange = new seisplotjs.util.StartEndDuration(SPRING2019.starttime, SPRING2019.endtime);


function findRace(timeRange) {
  race = null;
  if (SPRING2019.timeRange.overlaps(timeRange)) {
      race = SPRING2019;
  } else if (FALL2019.timeRange.overlaps(timeRange)) {
      race = FALL2019;
  } else {
      throw new Error(`Can't figure out which race for dates ${timeRange.startTime} - ${timeRange.endTime}`)
  }
  return race;
}

function loadResults(timeRange) {
  if ( ! timeRange ) { return Promise.resolve([]);}
  let race = findRace(timeRange)
  resultsUrl = `http://www.seis.sc.edu/dragdata/${race.name}/results/allResults.json`
  return seisplotjs.util.doFetchWithTimeout(resultsUrl)
    .then(response => response.json())
    .then(allResults => {
      for (r of allResults) {
        r.Trigger_Info.startTime = seisplotjs.moment.utc(r.Trigger_Info.startTime);
        r.Trigger_Info.time = seisplotjs.moment.utc(r.Trigger_Info.time);
        r.Trigger_Info.endTime = seisplotjs.moment.utc(r.Trigger_Info.endTime);
        r.timeRange = new seisplotjs.util.StartEndDuration(r.Trigger_Info.startTime, r.Trigger_Info.endTime);
      }
      return allResults.filter( r => r.timeRange.overlaps(timeRange));
    });
}

function markersForResults(results) {
  let out = [];
  results.forEach(r => {
    out.push({
      type: 'predicted',
      name: r.Trigger_Info.heat,
      time: r.Trigger_Info.startTime,
      description: `${r.Day_Name} ${r.Trigger_Info.class} ${r.Trigger_Info.heat}`
    });
    out.push({
      type: 'predicted',
      name: r.Trigger_Info.heat,
      time: r.Trigger_Info.endTime,
      description: `${r.Day_Name} ${r.Trigger_Info.class} ${r.Trigger_Info.heat}`
    });
  });
  return out;
}


/**
 * Override plotDataset to also plot markers for heats.
 */
class DragraceViewObsPy extends ViewObsPy {

  plotDataset(dataset, plottype, seisChanQuakeFilter) {
    super.plotDataset(dataset, plottype, seisChanQuakeFilter);
    this.dragracePlotDataset(dataset, plottype, seisChanQuakeFilter);
  }

  dragracePlotDataset(dataset, plottype, seisChanQuakeFilter) {
    let timeRange = null;
    dataset.data.relationships.seismograms.data.forEach(d => {
      const seisUrl = `/seismograms/${d.id}`;
      if (this.processedData.has(seisUrl)) {
        let seismogram = this.processedData.get(seisUrl);
        if (timeRange) {
          timeRange = timeRange.union(seismogram.timeRange);
        } else {
          timeRange = seismogram.timeRange;
        }
      }
    });
    return loadResults(timeRange).then(results => {
      console.log(`Got ${results.length} results`);
      results.forEach(r => {console.log(`result: ${r.Trigger_Info.startTime} ${r.Trigger_Info.heat}`)});
      let markers = markersForResults(results);
      dataset.data.relationships.seismograms.data.forEach(d => {
        let graph = this.processedData.get(`/seismograph/${d.id}`);
        if (graph) {
          graph.seisDataList.forEach(sdd => sdd.addMarkers(markers));
          graph.drawMarkers();
        }
      });
      return markers;
    });
  }

}
