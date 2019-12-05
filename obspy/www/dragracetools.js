
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

let raceResults = null;

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
  let race = findRace(timeRange);
  let allResultsPromise;
  if (raceResults && raceResults.race === race) {
    allResultsPromise = Promise.resolve(raceResults.results);
  } else {
    resultsUrl = `http://www.seis.sc.edu/dragdata/${race.name}/results/allResults.json`
    allResultsPromise = seisplotjs.util.doFetchWithTimeout(resultsUrl)
      .then(response => response.json());
  }
  return allResultsPromise
    .then(allResults => {
      for (r of allResults) {
        r.Trigger_Info.startTime = seisplotjs.moment.utc(r.Trigger_Info.startTime);
        r.Trigger_Info.time = seisplotjs.moment.utc(r.Trigger_Info.time);
        r.Trigger_Info.endTime = seisplotjs.moment.utc(r.Trigger_Info.endTime);
        r.timeRange = new seisplotjs.util.StartEndDuration(r.Trigger_Info.startTime, r.Trigger_Info.endTime);
      }
      raceResults = {
        'results': allResults,
        'race': race
      };
      return allResults.filter( r => r.timeRange.overlaps(timeRange));
    });
}

function markersForResults(results) {
  let out = [];
  results.forEach(r => {
    out.push({
      type: 'predicted',
      name: r.Trigger_Info.heat,
      time: seisplotjs.moment.utc(r.Trigger_Info.startTime),
      description: `${r.Day_Name} ${r.Trigger_Info.class} ${r.Trigger_Info.heat}`
    });
    out.push({
      type: 'predicted',
      name: r.Trigger_Info.heat,
      time: seisplotjs.moment.utc(r.Trigger_Info.endTime),
      description: `${r.Day_Name} ${r.Trigger_Info.class} ${r.Trigger_Info.heat}`
    });
  });
  return out;
}


/**
 * Override plotDataset to also plot markers for heats.
 */
class DragraceViewObsPy extends ViewObsPy {


  createPlot(seisId, plottype, seisChanQuakeFilter) {
    return super.createPlot(seisId, plottype, seisChanQuakeFilter)
    .then(seis => {
      this.dragracePlotMarkers(seisId, plottype, seisChanQuakeFilter);
    });
  }

  dragracePlotMarkers(seisId, plottype, seisChanQuakeFilter) {
    let timeRange = null;
    if ( ! this.obspyData.has('dataset')) {
      console.log(`no dataset in processedData`);
      return;
    }
    const dataset = this.obspyData.get('dataset');
    console.log(`dataset size ${dataset.data.relationships.seismograms.data.length}`)
    dataset.data.relationships.seismograms.data.forEach(d => {
      const seisUrl = `/seismograms/${d.id}`;
      if (this.obspyData.has(seisUrl)) {
        let seismogram = this.obspyData.get(seisUrl);
        if (timeRange) {
          timeRange = timeRange.union(seismogram.timeRange);
        } else {
          timeRange = seismogram.timeRange;
        }
      } else {
        console.warn(`processedData doesn't have ${seisUrl}`)
        console.log(Array.from(this.processedData.keys()))
      }
    });
    return loadResults(timeRange).then(results => {
      console.log(`Got ${results.length} results for ${timeRange}`);
      results.forEach(r => {console.log(`result: ${r.Trigger_Info.startTime} ${r.Trigger_Info.heat}`)});
      let markers = markersForResults(results);
      console.log(`markers ${markers.length}`)
      dataset.data.relationships.seismograms.data.forEach(d => {
        let graph = this.processedData.get(`/seismograph/${d.id}`);
        if (graph) {
          graph.seisDataList.forEach(sdd => sdd.addMarkers(markers));
          graph.seismographConfig.doMarkers=true;
          graph.draw();
          graph.seisDataList.forEach(sdd => console.log(`sdd markers: ${sdd.markerList.length}`));
        }
      });
      return markers;
    });

  }


}
