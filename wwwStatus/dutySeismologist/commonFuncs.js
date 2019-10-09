

let fetchCurrentResult = function() {
  return fetch(`https://www.seis.sc.edu/dragrace/www/results/MostRecentResult.json`)
  .then(function(response){
    if(response.ok) {
      return response.json();
    }
    throw new Error('Network response for MostRecentResult.json was not ok.');
  })
  .then(function(MRR) {
//    for (let c of classnames){
      let c = MRR.class;
      let h = MRR.heat;
      let day = MRR.day;
      return fetchHeatResult(day, c, h);
  });
};

let fetchClassnames = function(day) {
    return fetch(`https://www.seis.sc.edu/dragrace/www/results/${day}/classnames.json`)
    .then(function(response){
        if(response.ok) {
          return response.json();
        }
        throw new Error('Network response for classnames.json was not ok.');
    });
};

let fetchHeatnames = function(day, classname) {
    return fetch(`https://www.seis.sc.edu/dragrace/www/results/${day}/${classname}/heatnames.json`)
    .then(function(response){
        if(response.ok) {
          return response.json();
        }
        throw new Error('Network response for heatnames.json was not ok.');
    });
};

let fetchHeatResult = function(day, classname, heatname) {
    return fetch(`https://www.seis.sc.edu/dragrace/www/results/${day}/${classname}/${heatname}/results.json`)
    .then(function(response){
      if(response.ok) {
        return response.json();
      }
      throw new Error('Network response for result.json was not ok.');
    });
  };

createEqualizerMap = function(result){
  let dataset=new Map();
  dataset.set("FL",{'station':'FL','maxacc':result.peakACC_FL});
  dataset.set("NL",{'station':'NL','maxacc':result.peakACC_NL});
  // dataset.set("FL",{'station':'NR','maxacc':result.peakACC_NR});
  // dataset.set("FR",{'station':'FR','maxacc':result.peakACC_FR});
  dataset.set("FL0",{'station':'FL0','maxacc':result.peakACC_FL0});
  dataset.set("FL60",{'station':'FL60','maxacc':result.peakACC_FL60});
  dataset.set("FL330",{'station':'FL330','maxacc':result.peakACC_FL330});
  dataset.set("FL660",{'station':'FL660','maxacc':result.peakACC_FL660});
  dataset.set("FL1K",{'station':'FL1K','maxacc':result.peakACC_FL1K});
  dataset.set("FL4G",{'station':'FL4G','maxacc':result.peakACC_FL4G});




  return dataset;
}
