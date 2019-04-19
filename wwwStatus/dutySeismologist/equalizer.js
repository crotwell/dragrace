
//make equalizer from maxacc json data
class Equalizer{
  constructor(selector){
    this.selector = selector;
    this.d3 = seisplotjs.d3
    this.margin = 30;
    this.w = 330;
    this.h = 200; //px
    this.yScale = d3.scaleLinear()
    .domain([0,2])
    .range([0,this.h]);
    console.log(`yscaletest ${this.yScale(1)}`)
    this.yAxis = d3.axisLeft(this.yScale);
    this.yAxis.ticks(10);
    this.barPadding = 1;

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
    .call(this.yAxis);

  let bars = svg.append("g")
  .classed("bars",true)
  .attr("transform","translate(30,0)");
}

updateEqualizer(maxaccJson){
  let dataset = new Array();
  for (let x of maxaccJson.values()){
    dataset.push(x);

  }
  console.log(`dataset len: ${dataset.length}`)
  //console.log(`${dataset} this is the data`);
  //create a svg element before body taag and assigns a svg with height and width

let svg = d3.select(this.selector).select("svg");
let bars = svg.select("g.bars");
let that = this;
svg.selectAll("rect")//select in the page and correspond to data
  .data(dataset, function(d){
    return d.station;
  })
  .enter()
  .append("rect")
  //define NL... as numbers

  .attr("x",function(d){
    let i = -1;

    if (d.station === "FL") {
      i = 0;
    }else if (d.station === "NL") {
      i = 1;
    }else if (d.station === "NR") {
      i = 2;
    }else if (d.station === "FR") {
      i = 3;
    }else {
         console.log(`no station found ${d.station}`);
    }
console.log(`xxxxx ${d.station} maxacc= ${d.maxacc} i=${i}`)
    return i * (that.w / 4);
  })
  .attr("y", function(d){
    return that.h - that.yScale(d.maxacc); //height minus data value
  })
  .attr("width", that.w / dataset.length-that.barPadding)
  .attr("height",function(d){
    console.log(`height ${d.maxacc} ${that.yScale(d.maxacc)}`)
    return that.yScale(d.maxacc); // 2g = 100px according to yScale

    })
  .attr("fill",function(d){
    return "rgb( " + (d.maxacc * 255/2) + " , 0, 0 )";
  });
  }
}
