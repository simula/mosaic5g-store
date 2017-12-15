function topology(sources) {

    var LIST = [];

    var INFO_ENB = {
	icon: "enb-black",
	class: "enb"
    };
    
    var INFO_UE = {
	icon: "PHONE",
	class: "phone"
    };
    
    var INFO_RTC = {
	icon: "RTC",
	class: "rtc"
    };

    var INFO_APP = {
	//icon: "RTC",
	class: "sma"
    };
    
    function expandBottom(elem, params) {
	// Expand element height to the bottom of page (experimental)
	var body = d3.select("body").node();
	var rect = elem.getBoundingClientRect();
	var h = window.innerHeight;
	// Ad hoc: -20 for potential borders and margins -- not a
	// stable solution
	var vh = Math.max(200, (h - rect.top) - 20);
	d3.select(elem).style("height", vh + "px");
    }

    var show_id;
    
    function flat(obj) {
	var result = [];
	
	function flatten(prefix, obj) {
	    if (obj === null || typeof obj != 'object') {
		result.push([prefix, obj]);
	    } else if (Array.isArray(obj)) {
		for (var i in obj) {
		    flatten(prefix + '[' + i + ']', obj[i]);
		}
	    } else {
		var keys = Object.keys(obj);
		if (prefix) prefix += '.';
		for (var j in keys) {
		    var k = keys[j];
		    flatten(prefix + k, obj[k]);
		}
	    }
	}
	flatten('', obj);
	return result;
    }

    function closeConfig() {
	var params = d3.select("#parameters")
		.classed("open", false);
	show_id = undefined;
    }

    function show_config(config) {
	var params = d3.select("#parameters")
		.classed("open", true);
	var head = params.select("th").text('');
	head.append("span").text(show_id);
	head.append("span")
	    .attr("class", "cancel")
	    .attr("data-action", "closeConfig")
	    .call(uitools.add_click_action);
	var cellRows = params.select("tbody")
		.selectAll("tr")
		.data(flat(config));
	cellRows.exit().remove();
	var row = cellRows
		.enter()
		.append("tr")
		.merge(cellRows)
		.selectAll("td")
		.data(function (d) { return d; });
	row.exit().remove();
	row.enter()
	    .append("td")
	    .merge(row)
	    .text(function (d) { return d; });
    }

    function update() {
	GRAPH.hideAll();
	for (var s = 0; s < LIST.length; ++s) {
	    var src = LIST[s];
	    GRAPH.show(src.node);
	    if (src.node.info === INFO_APP) {
		// Assume SMA Application
		var list = src.node.config;
		for (var i = 0; i < list.length; ++i) {
		    var cell_id = list[i].cell_id;
		    var freq_min = list[i].options[0].freq_min;
		    var freq_max = list[i].options[0].freq_max;
		    var bandwidth = list[i].options[0].bandwidth;
		    var cell = GRAPH.node('0_eNB_' + i);
		    GRAPH.relation(src.node, cell, 'control', {'end': ['['+freq_min+'..'+freq_max+'] ' + bandwidth]},
				   undefined, GRAPH.MARKER.END);
		}
	    }
	    var data = src.data;
	    if (!data) continue;
	    
	    for (i = 0; i < data.eNB_config.length; ++i) {
		var config = data.eNB_config[i];
		var enb = GRAPH.node(src.index + '_eNB_' + i,
				     i,
				     INFO_ENB);
		GRAPH.relation(enb, src.node, 'connection', {});
		enb.config = {
		    cellConfig: config.eNB.cellConfig,
		    ueConfig: config.UE.ueConfig,
		    lcUeConfig: config.LC.lcUeConfig
		};
		if (config.LC.lcUeConfig) {
		    for (var j = 0; j < config.LC.lcUeConfig.length; ++j) {
			var ueConfig = config.LC.lcUeConfig[j];
			// THIS IS NOT "PRODUCTION LEVEL"
			// solution. The rnti is random value, and
			// this keeps adding new nodes into the
			// graph (even if they are not
			// visible). If 'rnti' based solution is
			// kept, old nodes must be deleted.
			var ue = GRAPH.node(src.index + '_UE_'+ ueConfig.rnti, ueConfig.rnti, INFO_UE);
			var l = [];
			for (var k = 0; k < data.mac_stats.length; ++k) {
			    for (var m = 0; m < data.mac_stats[k].ue_mac_stats.length; ++m) {
				var stats = data.mac_stats[i].ue_mac_stats[m];
				if (!stats || stats.rnti != ueConfig.rnti) continue;
				ue.config = stats;
				//l.push(stats.mac_stats.ulCqiReport.pucchDbm[0].p0PucchDbm);
				l.push('CQI='+stats.mac_stats.dlCqiReport.csiReport[0].p10csi.wbCqi);
				l.push('RSRP='+stats.mac_stats.rrcMeasurements.pcellRsrp);
				l.push('RSRQ='+stats.mac_stats.rrcMeasurements.pcellRsrq);
				if (ue.id == show_id)
				    show_config(ue.config);
			    }
			}
			GRAPH.relation(enb, ue, 'connection', {end: l, arrow: [''+stats.mac_stats.pdcpStats.pktTxBytesW]},undefined, GRAPH.MARKER.END);
			GRAPH.relation(ue, enb, 'connection', {arrow: [''+stats.mac_stats.pdcpStats.pktRxBytesW]},undefined, GRAPH.MARKER.END);
		    }
		}
		if (enb.id == show_id)
		    show_config(enb.config);
	    }
	}
	GRAPH.update();
    }
    
    function refresh(src) {
	console.log(src);
	d3.json(src.url, function (error, data) {
	    src.node.error = !!error;
	    if (!error) {
		src.data = data;
	    }
	    // Keep alive (if timeout set)
	    if (src.timer > 0)
		src.timeout = setTimeout(src.refresh, src.timer*1000);
	    else
		src.timeout = undefined;
	    update();
	});
    }

    function refresh_ws(src) {
	src.timeout = undefined;
	if (src.ws === undefined) {
	    src.ws = new WebSocket(src.url);
	    console.log("Trying SMA");
	    src.ws.onopen = function () {
		src.node.error = false;
		if (src.timer > 0) {
		    console.log("SMA WS Open");
		    src.ws.send(JSON.stringify('get-list'));
		} else {
		    console.log("SMA WS Cancel open");
		    src.ws.close();
		}
		update();
	    };
	    src.ws.onclose = function () {
		src.ws = undefined;
		src.node.error = true;
		console.log("SMA WS Closed");
		if (src.timer > 0)
		    src.timeout = setTimeout(src.refresh, src.timer*1000);
		else
		    src.timeout = undefined;
		update();
	    };
	    src.ws.onerror = function (evt) {
		src.node.error = true;
		console.log(evt);
		update();
	    };
	    src.ws.onmessage = function (evt) {
		src.node.error = false;
		console.log(evt.data);
		var msg = JSON.parse(evt.data);
		src.node.config = msg;
		update();
	    };
	}
	update();
    }
    
    function resize(elem, param) {
	expandBottom(elem,param);
	GRAPH.resize();
	GRAPH.update();
    }

    function setup(sources) {
	// Stop old timers
	for (var i = 0; i < LIST.length; ++i) {
	    if (LIST[i].timeout)
		clearTimeout(LIST[i].timeout);
	    LIST[i].timeout = undefined;
	    LIST[i].timer = -1;
	    if (LIST[i].ws) {
		LIST[i].ws.close();
	    }
	}

	// Setup a new source list
	LIST = sources.map(function (src, index) {
	    src.index = index;
	    if (src.url.startsWith("ws")) {
		src.node = GRAPH.node(src.index + '_APP', src.name + ' ' + src.index, INFO_APP);
		src.node.error = true; // Start in error state until ws connection is up
		src.refresh = function () { refresh_ws(src); };
	    } else {
		src.node = GRAPH.node(src.index + '_RTC', src.name + ' ' + src.index, INFO_RTC);
		src.refresh = function () { refresh(src);};
	    }
	    // Set the displayed data when node is clicked
	    src.node.config = { index: src.index, url: src.url} ;
	    src.timer = +src.timer; // Make it a number (if string)
	    // src.timer unit is [s]
	    if (src.timer > 0)
		src.timeout = setTimeout(src.refresh, src.timer*1000);
	    return src;
	});
    }

    function node_presentation(nodes) {
	nodes.append("text")
	    .attr("class", "stats")
	    .attr("dx", GRAPH.NODE.R)
	    .attr("dy", -GRAPH.NODE.R);
	nodes.filter(function (d) { return d.info === INFO_APP;})
	    .append("circle")
	    .attr("r", GRAPH.NODE.R * 0.6);
    }
    
    function node_status_indicator(nodes) {
	nodes.filter(function (d) { return !d.error;}).selectAll(".error_x").remove();
	var errors = nodes.filter(function (d) { return d.error;})
		.selectAll(".error_x")
		.data([0])
		.enter() // ..if error_x is already present, nothing new is inserted!
		.append("text")
		.attr("text-anchor", "middle")
		//.attr("alignment-baseline", "center")
		.attr("dy", "0.3em")
		.attr("class", "error_x")
		.text("\u2716");
	var stats = nodes.filter(function (d) { return d.info === INFO_ENB;})
		.select("text.stats")
		.selectAll("tspan")
		.data(['cellId', 'dlFreq', 'ulFreq', 'eutraBand', 'dlPdschPower', 'ulPuschPower', ]);
	stats.enter()
	    .append("tspan")
	    .attr("x", GRAPH.NODE.R)
	    .attr("dx", 0)
	    .attr("dy", "1em");
	stats.merge(stats)
	    .text(function (d) {
		var config = this.parentNode.__data__.config;
		return d + '=' + config.cellConfig[0][d];
	    });
    }

    var GRAPH = graph("#topology",
		      {},
		      {
			  nodeSelect: function (d) {
			      console.log("show ",d.id);
			      if (show_id != d.id) {
				  show_id = d.id;
				  show_config(d.config);
			      }
			  }
		      }
		     );
    GRAPH.NODE.update = node_status_indicator;
    GRAPH.NODE.create = node_presentation;

    resize(d3.select("#topology").node());

    setup(sources);
    
    return {
	getSources: function () { return LIST.map(function (x) { return {name: x.name, url: x.url, timer: x.timer };});},
	setSources: function (sources) { setup(sources); },
	closeConfig: closeConfig,
	GRAPH: GRAPH,
	update: update,
	resizeGraph: resize
    };
}
