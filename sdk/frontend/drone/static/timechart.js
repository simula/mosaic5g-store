function timechart(g, width, height, duration) {

    var x_values = [];
    var y_values = [];

    var x = d3.scaleLinear()
	    .range([0, width])
	    .domain([duration, 0]),
	// y = d3.scaleLinear().range([height, 0]),
	y = d3.scaleSqrt()
	    .range([height, 0])
	    .domain([1,50000000]),
	z = d3.scaleOrdinal(d3.schemeCategory10);

    var x_axis = g.append("g")
            .attr("class", "axis x")
     	    .attr("transform", "translate(0," + height + ")")
     	    .call(d3.axisBottom(x)
		  .ticks(5)
		  .tickSize(2)
		  .tickPadding(1));
    var y_axis = g.append("g")
    	    .attr("class", "axis y")
	    .attr("transform", "translate(" + width + ")")
    	    .call(d3.axisRight(y)
		  .tickFormat(d3.format('.2s'))
		  .tickValues([1000000, 2000000, 4000000,8000000,16000000, 32000000])
		  .tickSize(-width)
		 );

    var paths = g.append("g").attr("class", "linepath");
    
    var line = d3.line()
            // .curve(d3.curveBasis)
	    .curve(d3.curveMonotoneX)
	    .x(function(_, i) { return x(x_values[x_values.length-1] - x_values[i]);})
	    .y(function(d, i) { return y(Math.max(d,1));});

    function append(time, sample) {
	while (y_values.length < sample.length) {
	    var data = {
		values: d3.range(x_values.length).map(function(d) { return undefined;})
	    };
	    data.path = paths.append('path')
		.data([data.values])
		.style('stroke', z(y_values.length));
	    y_values.push(data);
	}
	x_values.push(time);
	// Prune off too old values (at least one sample remains)
	var dropoff = time - duration;
	while (x_values[0] < dropoff) {
	    x_values.shift();
	    for (i = 0; i < y_values.length; ++i)
		y_values[i].values.shift();
	}
	for (var i = 0; i < y_values.length; ++i) {
	    y_values[i].values.push(sample[i]);
	    y_values[i].path.attr('d', line);
	}
    }

    return {
	append: append
    };
}
