
const odsp = seisplotjs.filter.OregonDSP;
const d3 = seisplotjs.d3;


d3.select("button#load").on("click", function(d) {
  createFIR();
});

let createFIR = function() {

  // order N => 2N+1 coeff
  let N = parseInt(document.getElementsByName('N')[0].value);
  // top of pass band, scale 0-1 by nyquist
  let OmegaP=parseFloat(document.getElementsByName('OmegaP')[0].value);
  // weight given to passband ripple?
  let Wp=parseFloat(document.getElementsByName('Wp')[0].value);
  // bottom of stop band, must be > OmegaP
  let OmegaS=parseFloat(document.getElementsByName('OmegaS')[0].value);
  // Weight given to stopband ripple?
  let Ws=parseFloat(document.getElementsByName('Ws')[0].value);

  let firLp = new odsp.filter.fir.equiripple.EquirippleLowpass(N, OmegaP, Wp, OmegaS, Ws);

  d3.select("h3.coefficients").selectAll("*").remove();
  d3.select("h3.coefficients").text(`FIR Coefficients: N: ${N} => ${2*N+1}  OmegaP: ${OmegaP} Wp: ${Wp}  OmegsS: ${OmegaS} Ws: ${Ws}`)

  let coeffDisplay = d3.select("div.coefficients").select("ul").selectAll("li")
    .data(firLp.getCoefficients())
    .text(function(d) { return d; });
  coeffDisplay.enter().append("li").text(d=> d);
  coeffDisplay.exit().remove();

  const NumPoints = 256;
  const plotWidth = 512;
  const plotHeight = 512;
  const margin = {top: 20, right: 30, bottom: 30, left: 40};
  let width = plotWidth - margin.left - margin.right;
  let height = plotHeight - margin.top - margin.bottom;

  let inData = new Array(NumPoints-firLp.getCoefficients().length);
  inData.fill(0.0);
  inData[inData.length/2-1] = 1.0
  for (let i=0; i<inData.length; i++) {
    inData[i] = 1-2*Math.random();
  }
  outData = firLp.filter(inData);
  filterDelay = (firLp.getCoefficients().length-1)/2
  reoutData = firLp.filter(outData.slice(filterDelay));

  //
  // let impulseDisplay = d3.select("div.impulse").select("ul").selectAll("li")
  //   .data(outData)
  //   .text(function(d) { return d; });
  // impulseDisplay.enter().append("li").text(d=> d);
  // impulseDisplay.exit().remove();

  let plotSvg = d3.select("div.plot").select("svg.timeseries");
  plotSvg.attr("width", plotWidth).attr("height", plotHeight);
  let xScale = d3.scaleLinear().range([0, width]).domain([0, NumPoints]);
  let yScale = d3.scaleLinear().range([height, 0]).domain([-1, 1]);

  lineFunc = d3.line()
        .curve(d3.curveLinear)
        .x(function(d, i) {return xScale(i); })
        .y(function(d) {return yScale(d); });

  plotSvg.selectAll("*").remove();
  plotSvg.append("g").classed("in", true).attr("transform", "translate(" + margin.left + "," + margin.top + ")")
    .append("path").attr("d", lineFunc(inData));
  plotSvg.append("g").classed("out", true).attr("transform", "translate(" + margin.left + "," + margin.top + ")")
    .append("path").attr("d", lineFunc(outData.slice(filterDelay)));
    plotSvg.append("g").classed("reout", true).attr("transform", "translate(" + margin.left + "," + margin.top + ")")
      .append("path").attr("d", lineFunc(reoutData.slice(filterDelay)));



  let xAxis = d3.axisBottom(xScale);
  let yAxis = d3.axisLeft(yScale);
  plotSvg.append("g").attr("transform", "translate("+margin.left+"," + margin.top + ")")
  .call(yAxis);
  plotSvg.append("g").attr("transform", "translate(" +margin.left  + ","+(margin.top +height)+")")
  .call(xAxis);

// FFT plots

  let fftSvg = d3.select("div.plot").select("svg.fft");
  fftSvg.attr("width", plotWidth).attr("height", plotHeight);
  let xScaleFFT = d3.scaleLog().range([0, width]).domain([1.0/NumPoints/2, 1]);
  let yScaleFFT = d3.scaleLinear().range([height, 0]).domain([-1, 1]);

  let inDataFFT = seisplotjs.filter.calcDFT(inData, inData.length);
  let outDataFFT = seisplotjs.filter.calcDFT(outData, outData.length);
  for(let i=0; i<10;i++) {
    console.log(`fft out: ${outDataFFT[i]}  ${outDataFFT[outDataFFT.length-1-i]}`)
  }

  seisplotjs.waveformplot.simpleOverlayFFTPlot([inDataFFT, outDataFFT], "div.fft", 1);
//simpleLogPlot(inDataFFT, outDataFFT, "div.fft", 1);

  // lineFunc = d3.line()
  //       .curve(d3.curveLinear)
  //       .x(function(d, i) {console.log(`x ${i} ${xScale(i)}`);return xScale(i); })
  //       .y(function(d) {console.log(`y ${d} ${yScale(d)}`);return yScale(d); });
  //
  // plotSvg.selectAll("*").remove();
  // plotSvg.append("g").classed("in", true).attr("transform", "translate(" + margin.left + "," + margin.top + ")")
  //   .append("path").attr("d", lineFunc(inData));
  // plotSvg.append("g").classed("out", true).attr("transform", "translate(" + margin.left + "," + margin.top + ")")
  //   .append("path").attr("d", lineFunc(outData.slice(filterDelay)));
  //   plotSvg.append("g").classed("reout", true).attr("transform", "translate(" + margin.left + "," + margin.top + ")")
  //     .append("path").attr("d", lineFunc(reoutData.slice(filterDelay)));
  //
  //
  //
  // let xAxis = d3.axisBottom(xScale);
  // let yAxis = d3.axisLeft(yScale);
  // plotSvg.append("g").attr("transform", "translate("+margin.left+"," + margin.top + ")")
  // .call(yAxis);
  // plotSvg.append("g").attr("transform", "translate(" +margin.left  + ","+(margin.top +height)+")")
  // .call(xAxis);

}



function simpleLogPlot(fft, fftB, cssSelector, sps) {

    let T = 1/sps;
    let ampLength = fft.length/2 +1;
    let fftReal = fft.slice(0, ampLength);
    let fftImag = new Array(ampLength);
    fftImag[0] = 0;
    fftImag[fftImag.length-1] = 0;
    for (let i=1; i< fft.length/2; i++) {
      fftImag[i] = fft[fft.length - i];
    }
    let fftAmp = new Array(fftReal.length);
    for (let i=0; i< fftReal.length; i++) {
      fftAmp[i] = Math.hypot(fftReal[i], fftImag[i]);
    }

    fftAmp = fftAmp.slice(1);

    //B data
    fftReal = fftB.slice(0, ampLength);
    fftImag = new Array(ampLength);
    fftImag[0] = 0;
    fftImag[fftImag.length-1] = 0;
    for (let i=1; i< fftB.length/2; i++) {
      fftImag[i] = fftB[fftB.length - i];
    }
    let fftBAmp = new Array(fftReal.length);
    for (let i=0; i< fftReal.length; i++) {
      fftBAmp[i] = Math.hypot(fftReal[i], fftImag[i]);
    }

    fftBAmp = fftBAmp.slice(1);

    let svg = d3.select(cssSelector).select("svg");

    svg.selectAll("*").remove();

    let margin = {top: 20, right: 20, bottom: 30, left: 50},
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom,
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

let x = d3.scaleLog()
    .rangeRound([0, width]);

let y = d3.scaleLog()
    .rangeRound([height, 0]);

let line = d3.line()
    .x(function(d, i) { return x((i+1)*T); })
    .y(function(d, i) { return y(d); });

  x.domain([T, fftAmp.length*T]);
//  x.domain(d3.extent(fftAmp, function(d, i) { return i; }));
  let extent = d3.extent(fftAmp, function(d, i) { return d; });
  let extentB = d3.extent(fftBAmp, function(d, i) { return d; });
  extent = d3.extent([extent[0], extent[1], extentB[0], extentB[1]], function(d, i) { return d; })
  y.domain(extent);
  if (y.domain()[0] === y.domain()[1]) {
    y.domain( [ y.domain()[0]/2, y.domain()[1]*2]);
  }
  console.log(`fft y scale domain: ${y.domain()}`)

  g.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x))
    .append("text")
      .attr("fill", "#000")
      .attr("y", 0)
      .attr("x", width/2)
      .attr("dy", "0.71em")
      .attr("text-anchor", "end")
      .text("Hertz");

//    .select(".domain")
//      .remove();

  g.append("g")
      .call(d3.axisLeft(y))
    .append("text")
      .attr("fill", "#000")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", "0.71em")
      .attr("text-anchor", "end")
      .text("Amp");

  g.append("path")
      .datum(fftAmp)
      .attr("fill", "none")
      .attr("stroke", "steelblue")
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round")
      .attr("stroke-width", 1.5)
      .attr("d", line);

  g.append("path")
      .datum(fftBAmp)
      .attr("fill", "none")
      .attr("stroke", "seagreen")
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round")
      .attr("stroke-width", 1.5)
      .attr("d", line);

}
