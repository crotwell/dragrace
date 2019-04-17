
//make equalizer from maxacc json data

let makeEqualizer = function(maxaccJson){
  let d3 = seisplotjs.d3
  let margin = 30;
  let w = 330;
  let h = 200;
  let yScale = d3.scaleLinear().domain([0,2]).range([0,h]);
  let yAxis = d3.axisLeft(yScale);
  let dataset = maxaccJson.values();

  let barPadding = 1;
  //create a svg element before body taag and assigns a svg with height and width
  let svg = d3.select("div.equalizer")
  .append("svg")
  .attr("width",w)
  .attr("height",h)
  .append("g")
    .attr("class","axisLeft")
    .call(yAxis);

  let bars = svg.append("g")
  .attr("transform","translate(30,0)");

  bars.selectAll("rect")//select in the page and correspond to data
  .data(dataset)
  .enter()
  .append("rect")
  //define NL... as numbers

  .attr("x",function(d){
    let i = -1;
    if (d.station === "FL") {
      i = 0
    }else if (d.station === "NL") {
      i = 1;
    }else if (d.station === "NR") {
      i = 2;
    }else if (d.station === "FR") {
      i = 3;
    }else {
         console.log(`no station found ${d.station}`);
    }

    return i * (w / 4);
  })
  .attr("y", function(d){
    return h - d; //height minus data value
  })
  .attr("width", w / dataset.length - barPadding)
  .attr("height",function(d){
    return yScale(d.maxacc); // 2g = 100px according to yScale
    })
  .attr("fill",function(d){
    return "rgb( " + (d * 10) + " , 0, 0 )";
  });
}
