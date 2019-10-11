

let fetchCurrentResult = function() {
  return fetch(`https://li75-105.members.linode.com/www/results/MostRecentResult.json`,
      {cache: "no-cache"}
    ).then(function(response){
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
    return fetch(`https://li75-105.members.linode.com/www/results/${day}/classnames.json`,
        {cache: "no-cache"}
      ).then(function(response){
        if(response.ok) {
          return response.json();
        }
        throw new Error('Network response for classnames.json was not ok.');
    });
};

let fetchHeatnames = function(day, classname) {
    return fetch(`https://li75-105.members.linode.com/www/results/${day}/${classname}/heatnames.json`,
        {cache: "no-cache"}
      ).then(function(response){
        if(response.ok) {
          return response.json();
        }
        throw new Error('Network response for heatnames.json was not ok.');
    });
};

let fetchHeatResult = function(day, classname, heatname) {
    return fetch(`https://li75-105.members.linode.com/www/results/${day}/${classname}/${heatname}/results.json`)
    .then(function(response){
      if(response.ok) {
        return response.json();
      }
      throw new Error('Network response for result.json was not ok.');
    });
  };

createEqualizerMap = function(result){
  let dataset=new Map();
  for (let [s, value] of Object.entries(result.peakACC)) {
    dataset.set(s, {'station':s,'maxacc':value});
  }
console.log(`createEqualizerMap  ${dataset}`)
  return dataset;
}
