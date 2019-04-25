
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

        return fetch(`https://www.seis.sc.edu/dragrace/www/results/${day}/${c}/${h}/results.json`)
    })
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
  dataset.set("NR",{'station':'NR','maxacc':result.peakACC_NR});
  dataset.set("FR",{'station':'FR','maxacc':result.peakACC_FR});
  return dataset;
}
