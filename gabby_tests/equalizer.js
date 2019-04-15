
let d3 = seisplotjs.d3
var dataset = [5,15,20,25,5]
var w = 200;
var h = 100;
var barPadding = 1;
//create a svg element before body taag and assigns a svg with height and width
var svg = d3.select("div")
.append("svg")
.attr("width",w)
.attr("height",h);

svg.selectAll("rect")//select in the page and correspond to data
.data(dataset)
.enter()
.append("rect")
.attr("x",function(d, i){
  return i * (w / dataset.length);
})
.attr("y", function(d){
  return h - d; //height minus data value
})
.attr("width", w / dataset.length - barPadding)
.attr("height",function(d){
  return d;
})
.attr("fill",function(d){
  return "rgb( " + (d * 10) + " , 0, 0 )";
});
