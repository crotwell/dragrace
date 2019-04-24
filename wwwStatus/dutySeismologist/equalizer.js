
//make equalizer from maxacc json data
class Equalizer{
  constructor(selector){
    this.selector = selector;
    this.d3 = seisplotjs.d3
    this.margin = 30;
    this.w = 330;
    this.h = 400; //px
    this.yScale = d3.scaleLinear()
    .domain([0,2])
    .range([0,this.h]);
    console.log(`yscaletest ${this.yScale(1)}`)
    this.yAxis = d3.axisLeft(this.yScale).ticks(8, "0.1f");
    // this.yAxis = d3.axisLeft(this.yScale);
    // this.yAxis.ticks(10);
    this.barPadding = 1;
    //test

    this.createEqualizer(selector);
    this.updateEqualizer(this.createZeros());
  }
createZeros(){
  let dataset=new Map();
  dataset.set("FL",{'station':'FL','maxacc':.10 });
  dataset.set("NL",{'station':'NL','maxacc':.5 });
  dataset.set("NR",{'station':'NR','maxacc':.3 });
  dataset.set("FR",{'station':'FR','maxacc':.1 });
  return dataset;
}

createEqualizer(selector){
  let svg = d3.select(selector)
  .append("svg")
  .attr("width",this.w)
  .attr("height",this.h);

  svg.append("g")
    .attr("class","axisLeft")
    .call(this.yAxis)
    .attr("transform","translate(30,0)");

  let bars = svg.append("g")
  .classed("bars",true)
  .attr("transform","translate(30,0)");
}

updateEqualizer(allmaxaccJson){
  let dataset = new Array();
  for (let x of allmaxaccJson.values()){
    dataset.push(x);

  }
  //create a svg element before body taag and assigns a svg with height and width

let svg = d3.select(this.selector).select("svg");
let bars = svg.select("g.bars");
let that = this;

svg.selectAll("rect")//select in the page and correspond to data
  .data(dataset, function(d){
    return d.station;
  })
  .join("rect")
  //.append("rect")
  //define NL... as numbers

  .attr("x",function(d){
    let i = -1;

    if (d.station === "FL") {
      i = 0;
    }else if (d.station === "NL") {
      i = 1;
    }else if (d.station === "NR") {
      i = 2;
    }else if (d.station === "CT") {
        i = 4;
    }else if (d.station === "FR") {
      i = 3;
    }else {
         console.log(`no station found ${d.station}`);
    }
    return i * (that.w / 5);
  })
  .attr("y", function(d){
    return that.h - that.yScale(d.maxacc); //height minus data value
  })
  .attr("width", that.w / 5-that.barPadding)
  .attr("height",function(d){
    return that.yScale(d.maxacc); // 2g = 100px according to yScale

    })
  .attr("fill",function(d){
    return "rgb( " + (Math.round(d.maxacc * 255/2)) + " , 0, 0 )";
  });
  }
}
