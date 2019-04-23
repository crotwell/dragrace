let fakeData= {
  "topFuel": {
    "heat 1": ["racer1", "racer2", "racer3", "racer4"],
    "heat 2": ["racer1", "racer2", "racer3", "racer4"],
    "heat 3": ["racer1", "racer2", "racer3", "racer4"],
    "heat 4": ["racer1", "racer2", "racer3", "racer4"],
    "heat 5": ["racer1", "racer2", "racer3", "racer4"],
    },
  "funnyCar": {
    "heat 1": ["racer1", "racer2", "racer3", "racer4"],
    "heat 2": ["racer1", "racer2", "racer3", "racer4"],
    "heat 3": ["racer1", "racer2", "racer3", "racer4"],
    "heat 4": ["racer1", "racer2", 'racer3', "racer4"],
    "heat 5": ["racer1", "racer2", "racer3", "racer4"],
    },
  "motorcycle": {
      "heat 1": ["racer1", "racer2", "racer3", "racer4"],
      "heat 2": ["racer1", "racer2", "racer3", "racer4"],
      "heat 3": ["racer1", "racer2", "racer3", "racer4"],
      "heat 4": ["racer1", "racer2", "racer3", "racer4"],
      "heat 5": ["racer1", "racer2", "racer3", "racer4"],
    },
};


let togglebutton = function(heatdiv) {
  wp.d3.select("div.sidebar").selectAll("div").select(".panel1").style("display","none");
  wp.d3.select("div.sidebar").selectAll("div").select("button").classed("active", false);

    heatdiv.select("button").classed("active", true);
    heatdiv.select(".panel1").style("display","block");
};
wp.d3.select("div.class1 button.heatcollapse").on("click", function(d) {
  console.log("buttonclick "+d);
   let heatdiv = wp.d3.select("div.class1");
   togglebutton(heatdiv);


});
wp.d3.select("div.class2 button.heatcollapse").on("click", function(d) {
  console.log("buttonclick "+d);
   let heatdiv = wp.d3.select("div.class2");
   togglebutton(heatdiv);

});



let fakeData = function(schedule) {
  let ipParas = d3.select("div.panel1").selectAll("p")
    .data(schedule, function(d) { return d.time; });

  let ipEnter = ipParas.enter()
    .append("p").text(function(d,i){
      let PIkey = d.station;
      let ip = d.ip;
      let piTime = d.time;
      return `PI=${PIkey}, IP=${ip}, pitime:${piTime} serverTime: ${moment.utc().toISOString()}`;
    });
  let ipMerge = ipParas.merge(ipEnter);
  let ipExit = ipParas.exit().transition().remove();
}


doDatalinkConnect()
