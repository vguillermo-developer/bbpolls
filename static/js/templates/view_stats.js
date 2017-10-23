$(document).ready(function(){

	var margin = {top: 60, right: 40, bottom: 60, left: 200},
	    width = 960 - margin.left - margin.right,
	    height = 420 - margin.top - margin.bottom;

	var x = d3.scale.ordinal()
	    .domain(dimensions.map(function(d) { return d.name; }))
	    .rangePoints([0, width]);

	var line = d3.svg.line()
	    .defined(function(d) { return !isNaN(d[1]); });

	var yAxis = d3.svg.axis()
	    .orient("left");

	var svg = d3.select("#parallel_coordinates").append("svg")
	    .attr("width", width + margin.left + margin.right)
	    .attr("height", height + margin.top + margin.bottom)
	  .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	var dimension = svg.selectAll(".dimension")
	    .data(dimensions)
	  .enter().append("g")
	    .attr("class", "dimension")
	    .attr("transform", function(d) { return "translate(" + x(d.name) + ")"; });

	d3.csv(csv_path, function(data) {
	  // dimensions.forEach(function(dimension) {
	  //   dimension.scale.domain(dimension.type === Number
	  //       ? d3.extent(data, function(d) { return +d[dimension.name]; })
	  //       : data.map(function(d) { return d[dimension.name]; }).sort());
	  // });

	  svg.append("g")
	      .attr("class", "background")
	    .selectAll("path")
	      .data(data)
	    .enter().append("path")
	      .attr("d", draw);

	  svg.append("g")
	      .attr("class", "foreground")
	    .selectAll("path")
	      .data(data)
	    .enter().append("path")
	      .attr("d", draw);

	  dimension.append("g")
	      .attr("class", "axis")
	      .each(function(d) { d3.select(this).call(yAxis.scale(d.scale)); })
	    .append("text")
	      .attr("class", "title")
	      .attr("text-anchor", "middle")
	      .attr("y", -9)
	      .text(function(d) { return d.name; });

	  // Rebind the axis data to simplify mouseover.
	  svg.select(".axis").selectAll("text:not(.title)")
	      .attr("class", "label")
	      .data(data, function(d) { return d.name || d; });

	  var projection = svg.selectAll(".axis text,.background path,.foreground path")
	      .on("mouseover", mouseover)
	      .on("mouseout", mouseout);

	  function mouseover(d) {
	    svg.classed("active", true);
	    projection.classed("inactive", function(p) { return p !== d; });
	    projection.filter(function(p) { return p === d; }).each(moveToFront);
	  }

	  function mouseout(d) {
	    svg.classed("active", false);
	    projection.classed("inactive", false);
	  }

	  function moveToFront() {
	    this.parentNode.appendChild(this);
	  }
	});

	function draw(d) {
	  return line(dimensions.map(function(dimension) {
	    return [x(dimension.name), dimension.scale(d[dimension.name])];
	  }));
	}
  
})