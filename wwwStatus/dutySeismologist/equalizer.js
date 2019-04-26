
//make equalizer from maxacc json data
class Equalizer{
  constructor(selector){
    this.selector = selector;
    this.d3 = seisplotjs.d3
    this.margin = {top: 20, right: 10, bottom: 20, left: 30};
    this.width = 330 - this.margin.left - this.margin.right;
    this.height = 400 - this.margin.top - this.margin.bottom;
    this.yScale = d3.scaleLinear()
    .domain([0,(2.0)])
    .range([this.height, 0]);
    console.log(`yscaletest ${this.yScale(1)}`)
    this.yAxis = d3.axisLeft(this.yScale).ticks(10, "0.1f");
    // this.yAxis = d3.axisLeft(this.yScale);
    // this.yAxis.ticks(10);
    this.barPadding = 1;
    //test

    this.createEqualizer(selector);
    this.updateEqualizer(this.createZeros());
  }
createZeros(){
  let dataset=new Map();
  dataset.set("FL",{'station':'FL','maxacc':.0 });
  dataset.set("NL",{'station':'NL','maxacc':.0 });
  dataset.set("CT",{'station':'CT','maxacc':.0 });
  dataset.set("NR",{'station':'NR','maxacc':.0 });
  dataset.set("FR",{'station':'FR','maxacc':.0 });
  return dataset;
}

createEqualizer(selector){
  let svg = d3.select(selector).append("svg")
    .attr("width", this.width + this.margin.left + this.margin.right)
    .attr("height", this.height + this.margin.top + this.margin.bottom)
  .append("g")
    .classed("main", true)
    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");

  svg.append("g")
    .attr("class","axisLeft")
    .call(this.yAxis);

  let bars = svg.append("g")
  .classed("bars",true);
}

updateEqualizer(allmaxaccJson){
  let dataset = new Array();
  for (let x of allmaxaccJson.values()){
    dataset.push(x);

  }
  //create a svg element before body taag and assigns a svg with height and width

let svg = d3.select(this.selector).select("svg").select("g.main");
let bars = svg.select("g.bars");
let that = this;

bars.selectAll("rect")//select in the page and correspond to data
  .data(dataset, function(d){
    return d.station;
  })
  .join("rect")
  //.append("rect")
  //define NL... as numbers

  .attr("x",function(d){
    let i = 99;

    if (d.station === "FL") {
      i = 0;
    }else if (d.station === "NL") {
      i = 1;
    }else if (d.station === "NR") {
      i = 2;
    // }else if (d.station === "CT") {
    //     i = 4;
    }else if (d.station === "FR") {
      i = 3;
    }else if (d.station === "FR") {
      i = 4;
    }else {
         console.log(`no station found ${d.station}`);
    }
    return i * (that.width / 5);
  })
  .attr("y", function(d){
    return that.yScale(d.maxacc); //height minus data value
  })
  .attr("width", that.width / 5-that.barPadding)
  .attr("height",function(d){
    return that.height-that.yScale(d.maxacc); // 2g = 100px according to yScale

    })
  .attr("fill",function(d){
    return "rgb( " + (Math.round(d.maxacc * 255/0.2)) + " , 0, 0 )";//255/0.2
  });
  }
}
