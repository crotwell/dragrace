
//make equalizer from maxacc json data
class Equalizer{
  constructor(selector){
    this.selector = selector;
    this.d3 = seisplotjs.d3
    this.margin = 30;
    this.w = 330;
    this.h = 200;
    this.yScale = d3.scaleLinear().domain([0,2]).range([0,this.h]);
    this.yAxis = d3.axisLeft(this.yScale);
    this.yAxis.ticks(10);
    this.barPadding = 1;

    this.createEqualizer(selector);
  }

createEqualizer(selector){
  let svg = d3.select(selector)
  .append("svg")
  .attr("width",this.w)
  .attr("height",this.h);

  svg.append("g")
    .attr("class","axisLeft")
    .call(this.yAxis);

  let bars = svg.append("g")
  .classed("bars",true)
  .attr("transform","translate(30,0)");
}

updateEqualizer(maxaccJson){
  let dataset = maxaccJson.values();
  console.log(`${dataset} this is the data`);
  //create a svg element before body taag and assigns a svg with height and width

let svg = d3.select("div.equalizer").select("svg");
let bars = svg.select("g.bars");

  bars.selectAll("rect")//select in the page and correspond to data
  .data(dataset);
  bars.enter()
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

    return i * (this.w / 4);
  })
  .attr("y", function(d){
    return this.h - d; //height minus data value
  })
  .attr("width", this.w / dataset.length-this.barPadding)
  .attr("height",function(d){
    return this.yScale(d.maxacc); // 2g = 100px according to yScale
    })
  .attr("fill",function(d){
    return "rgb( " + (d * 10) + " , 0, 0 )";
  });
  }
}
