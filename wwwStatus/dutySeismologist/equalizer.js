
//make equalizer from maxacc json data
class Equalizer{
  constructor(selector, plotStations){
    this.plotStations = plotStations;
    this.selector = selector;
    this.d3 = seisplotjs.d3
    this.margin = {top: 20, right: 10, bottom: 20, left: 30};
    this.width = 330 - this.margin.left - this.margin.right;
    this.height = 400 - this.margin.top - this.margin.bottom;
    this.yScale = d3.scaleLinear()
    .domain([0,(3.5)])
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
  dataset.set("FL0",{'station':'FL0','maxacc':.0 });
  dataset.set("FL60",{'station':'FL60','maxacc':.0 });
  dataset.set("FL330",{'station':'FL330','maxacc':.0 });
  dataset.set("FL660",{'station':'FL660','maxacc':.0 });
  dataset.set("FL1K",{'station':'FL1K','maxacc':.0 });
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
    if( this.plotStations.includes(x.station)){
      dataset.push(x);
    }
    // if (x.station !== 'CT') {       // fix this with 'find' return if exists
    //   dataset.push(x);

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
      i = 1;                            //make the first Lane 1 lane 2 equalizer
    }else if (d.station === "FL0") {
      i = 4;
    }else if (d.station === "FL60") {
      i = 3;
    } else if (d.station === "FL330") {
      i = 2;
    }else if (d.station === "FL660") {
      i = 1;
    }else if (d.station === "FL1K") {
      i = 0;                              //make FL equalizer
    
    // }else if (d.station === "NR") {
    //   i = 2;
    // // }else if (d.station === "CT") {
    // //     i = 4;
    // }else if (d.station === "FR") {
    //   i = 3;
    // }else if (d.station === "FR") {
    //   i = 4;
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
