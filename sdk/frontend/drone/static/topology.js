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
    
    var INFO_LC_UE = {
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
	var rect = elem.getBoundingClientRect();
	var h = window.innerHeight;
	// Ad hoc: -30 for potential borders and margins -- not a
	// stable solution
	var vh = Math.max(200, (h - rect.top) - 30);
	d3.select(elem).style("height", vh + "px");
    }

    var show_id;
    
    function flat(obj) {
	var result = [];
	
	function flatten(prefix, obj) {
	    if (obj === null || typeof obj != 'object') {
		result.push([prefix, obj]);
	    } else if (Array.isArray(obj)) {
		if (obj.length > 0) {
		    for (var i in obj) {
			flatten(prefix + '[' + i + ']', obj[i]);
		    }
		} else {
		    flatten(prefix + '[]', '');
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

    function get(obj, path, value) {
	// Safely get deep property from obj.
	//  - path: array of property names, path to target
	//  - value: returned, if path does not exist
	for (var i = 0; i < path.length; ++i) {
	    if (!(path[i] in obj)) return value;
	    obj = obj[path[i]];
	}
	return obj;
    }
    
    function closeConfig() {
	var params = d3.select("#parameters")
		.classed("open", false);
	show_id = undefined;
	// More room for the graph
	GRAPH.resize();
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
	// Less room for the graph
	GRAPH.resize();
    }

    var SOURCE_UPDATE = {
	"APP": function (node) {
	    var data = node.config;
	    if (data && data.msg && data.app) {
		var app = GRAPH.port(node, data.app);
		app.config = data.msg;
		if (SOURCE_UPDATE[data.app])
		    SOURCE_UPDATE[data.app](app);
	    }
	},
	"SMA": function (node) {
	    var list = node.config;
	    for (var i = 0; i < list.length; ++i) {
		// Pick to values from first option of the last
		// message of the SMA_APP
		var cell_id = list[i].cell_id;
		var freq_min = list[i].options[0].freq_min;
		var freq_max = list[i].options[0].freq_max;
		var bandwidth = list[i].options[0].bandwidth;
		// This needs to change: now we just assume the
		// index of SMA_APP is the same as the enb index
		// from flexran. Must be replaced by proper id of
		// the enb being controlled.
		var cell = GRAPH.node('RTC_0_eNB_' + i);
		// The 'end' parameter defines what is shown at
		// the end of the dashed line from SMA_APP to
		// eNB. The styling of the line is defined by
		// ".link.control" in style.css.
		GRAPH.relation(node, cell, 'control', {'end': ['['+freq_min+'..'+freq_max+'] ' + bandwidth]},
			       undefined, GRAPH.MARKER.END);
	    }
	},
	"RTC": function (node) {
	    var data = node.config;
	    if (!data) return;

	    // Need to hide/remove eNB's and associated UE's that are
	    // not present in the new eNB_config. BUT, as there is no
	    // way to identify eNB yet, this cannot be implemented
	    // properly, unless all of them have gone away...
	    if (!data.eNB_config.length) {
		if (node.enb_list)
		    for (var i = 0; i < node.enb_list.length; ++i) {
			var enb = node.enb_list[i];
			for (var rnti in enb.ue_list)
			    GRAPH.remove(enb.ue_list[rnti].id);
			GRAPH.remove(enb.id);
		    }
	    }
	    node.enb_list = [];
	    for (i = 0; i < data.eNB_config.length; ++i) {
		var config = data.eNB_config[i];
		enb = GRAPH.node(node.id + '_eNB_' + i, i, INFO_ENB);
		node.enb_list.push(enb);

		GRAPH.relation(enb, node, 'connection', {},undefined,GRAPH.MARKER.END);
		enb.config = {
		    cellConfig: config.eNB.cellConfig,
		    ueConfig: config.UE.ueConfig,
		    lcUeConfig: config.LC.lcUeConfig
		};
		var ue_list = [];
		if (config.UE.ueConfig) {
		    for (var j = 0; j < config.UE.ueConfig.length; ++j) {
			var ueConfig = config.UE.ueConfig[j];
			if (ueConfig.rnti) {
			    ue_list[ueConfig.rnti] = GRAPH.node(enb.id + '_UE_'+ ueConfig.rnti, ueConfig.rnti, INFO_UE);
			}
		    }
		}
		if (config.LC.lcUeConfig) {
		    for (j = 0; j < config.LC.lcUeConfig.length; ++j) {
			ueConfig = config.LC.lcUeConfig[j];
			if (ueConfig.rnti) {
			    ue_list[ueConfig.rnti] = GRAPH.node(enb.id + '_UE_'+ ueConfig.rnti, ueConfig.rnti, INFO_LC_UE);
			}
		    }
		}
		if (enb.ue_list) {
		    // Remove old non-existent UE nodes
		    for (rnti in enb.ue_list) {
			if (!ue_list[rnti]) {
			    console.log("removing " + enb.ue_list[rnti].id);
			    GRAPH.remove(enb.ue_list[rnti].id);
			}
		    }
		}
		enb.ue_list = ue_list;
		// Assuming data.mac_stats[i] holds stats for the current eNB
		if (data.mac_stats[i]) {
		    for (var m = 0; m < data.mac_stats[i].ue_mac_stats.length; ++m) {
			var stats = data.mac_stats[i].ue_mac_stats[m];
			if (!stats) continue;
			var ue = ue_list[stats.rnti];
			if (!ue) continue;
			ue.config = stats;
			// The array 'l' below defines the information
			// set drawn at the end of the link from eNB
			// to UE. Each pushed string will show up on
			// their own line.
			var l = [];
			l.push('CQI='+ get(stats, ['mac_stats','dlCqiReport','csiReport', 0, 'p10csi', 'wbCqi']));
			var rrc = get(stats, ['mac_stats','rrcMeasurements']);
			if (rrc) {
			    l.push('RSRP='+rrc.pcellRsrp);
			    l.push('RSRQ='+rrc.pcellRsrq);
			}
			if (ue.id == show_id)
			    show_config(ue.config);

			var style = undefined;
			if (ue.info === INFO_UE) {
			    style = 'ghost';
			    ue.error = true;
			} else {
			    ue.error = false;
			}
			// The "arrow" labels depend on the link
			// direction, thus we need to call relation
			// for each direction. Only one two-headed
			// link is drawn, with arrow labels above and
			// below the link center. The labels at UE end
			// (array l) are only specified for the
			// enb->ue link.
			var lbls = {};
			var pdcp = get(stats, ['mac_stats', 'pdcpStats'], {});
			lbls.arrow = [''+pdcp.pktRxBytesW];
			GRAPH.relation(ue, enb, 'connection', lbls, style, GRAPH.MARKER.END);
			lbls.end = l;
			lbls.arrow = [''+pdcp.pktTxBytesW];
			GRAPH.relation(enb, ue, 'connection', lbls, style);
		    }
		}
		if (enb.id == show_id)
		    show_config(enb.config);
	    }
	}
    };

    function update_src(src) {
	if (!src.node) return;

	GRAPH.show(src.node);
	if (src.node.id == show_id) {
	    show_config(src.node.config);
	}
	if (src.node.error)
	    return; // Don't refresh links from a node in error state
	if (SOURCE_UPDATE[src.type])
	    SOURCE_UPDATE[src.type](src.node);
    }

    function update_all() {
    	GRAPH.hideAll();
    	for (var s = 0; s < LIST.length; ++s)
    	    update_src(LIST[s]);
    	GRAPH.update();
    }
    
    function refresh(src) {
	d3.json(src.url, function (error, data) {
	    src.node.error = !!error;
	    if (error) {
		console.log("Refresh fail: " + src.url);
	    } else {
		src.node.config = data;
	    }
	    // Keep alive (if timeout set)
	    if (src.timer > 0)
		src.timeout = setTimeout(src.refresh, src.timer*1000);
	    else
		src.timeout = undefined;
	    update_src(src);
	    GRAPH.update();
	});
    }

    function refresh_ws(src) {
	src.timeout = undefined;
	if (src.ws === undefined) {
	    src.ws = new WebSocket(src.url);
	    console.log("Trying WS");
	    src.ws.onopen = function () {
		src.node.error = false;
		if (src.timer > 0) {
		    console.log("WS Open");
		    src.ws.send(JSON.stringify('get-list'));
		} else {
		    console.log("WS Cancel open");
		    src.ws.close();
		}
		update_src(src);
		GRAPH.update();
	    };
	    src.ws.onclose = function () {
		src.ws = undefined;
		src.node.error = true;
		console.log("WS Closed");
		if (src.timer > 0)
		    src.timeout = setTimeout(src.refresh, src.timer*1000);
		else
		    src.timeout = undefined;
		update_src(src);
		GRAPH.update();
	    };
	    src.ws.onerror = function (evt) {
		src.node.error = true;
		console.log(evt);
		update_src(src);
		GRAPH.update();
	    };
	    src.ws.onmessage = function (evt) {
		src.node.error = false;
		console.log(evt.data);
		var msg = JSON.parse(evt.data);
		src.node.config = msg;
		update_src(src);
		GRAPH.update();
	    };
	}
	update_src(src);
	GRAPH.update();
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
	    if (LIST[i].node) {
		GRAPH.remove(LIST[i].node.id);
		LIST[i].node = null;
	    if (LIST[i].ws)
		LIST[i].ws.close();
	    }
	}

	// Setup a new source list
	LIST = sources.map(function (src, index) {
	    src.index = index;
	    if (src.url.startsWith("ws")) {
		src.node = GRAPH.node(src.type + '_' + src.index, src.name + ' ' + src.index, INFO_APP);
		src.node.error = true; // Start in error state until ws connection is up
		src.refresh = function () { refresh_ws(src); };
	    } else {
		src.node = GRAPH.node(src.type + '_'+ src.index, src.name + ' ' + src.index, INFO_RTC);
		src.refresh = function () { refresh(src);};
	    }
	    // Set the displayed data when node is clicked
	    //src.node.config = { index: src.index, url: src.url} ;
	    src.timer = +src.timer; // Make it a number (if string)
	    // src.timer unit is [s]
	    if (src.timer > 0)
		src.timeout = setTimeout(src.refresh, src.timer*1000);
	    return src;
	});
	GRAPH.update();
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
	// If node created with INFO_UE (and not INFO_LC_UE), then it
	// represents a ghost UE (not present in LC.lcUeConfig)
	nodes.classed("ghost", function (d) { return d.info === INFO_UE;});

	var stats = nodes.filter(function (d) { return d.info === INFO_ENB;})
		.select("text.stats")
		.selectAll("tspan")
	// The following fields from cellConfig[0] will be show on
	// right of the eNB icon. Generated below...
		.data(['cellId', 'dlFreq', 'ulFreq', 'eutraBand', 'dlPdschPower', 'ulPuschPower', 'dlBandwidth', 'ulBandwidth']);
	stats.enter()
	    .append("tspan")
	    .attr("x", GRAPH.NODE.R)
	    .attr("dx", 0)
	    .attr("dy", "1em");
	stats.merge(stats)
	    .text(function (d) {
		var config = this.parentNode.__data__.config;
		// ...add/update the above defined cellConfig[0].xxx
		// fields in graph.
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

    setup(sources);

    // initial size is slightly wrong, but following does not fix it...
    //setTimeout(function () {resize(d3.select("#topology").node());}, 100);
    
    return {
	getSources: function () { return LIST.map(function (x) {
	    return {
		type: x.type,
		name: x.name,
		url: x.url,
		timer: x.timer
	    };
	});},
	setSources: function (sources) { setup(sources); },
	closeConfig: closeConfig,
	GRAPH: GRAPH,
	update: update_all,
	resizeGraph: function () { resize(d3.select("#topology").node());}
    };
}
