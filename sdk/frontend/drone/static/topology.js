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
	icon: "APP",
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

    function closeError() {
	d3.select("#error_note")
	    .classed("open", false);
    }
    function show_error(message) {
	d3.select("#error_note")
	    .classed("open", true)
	    .select(".message")
	    .text(message);
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

    function sma_get_list(src) {
	var node = src.node;
    	var list = node.config;
	if (!list) return;
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
	    var cell = GRAPH.find('flexran-rtc_eNB_' + i);
	    if (cell) {
		// The 'end' parameter defines what is shown at
		// the end of the dashed line from SMA_APP to
		// eNB. The styling of the line is defined by
		// ".link.control" in style.css.
		GRAPH.relation(node, cell, 'control', {'end': ['['+freq_min+'..'+freq_max+'] ' + bandwidth]},
			       undefined, GRAPH.MARKER.END);
	    }
	}
    }

    function send_ws_message(src, msg) {
	if (msg) {
	    if (src.ws) {
		console.log("sending:", msg);
		src.ws.send(JSON.stringify(msg));
	    } else {
		show_error('Application ' + src.node.id + ' does not have websocket connection');
	    }
	}
    }

    function sendCommand(elem, params) {
	var src, method, cap, args;

	if (params.command) {
	    // Command input 'appid/method/params/...'. If input
	    // starts with '/', there is no application and message is
	    // sent for all RPC applications.
	    var app_id = params.command.split('/')[0];
	    var command = params.command.slice(app_id.length+1);
	    // Find the source...
	    var send_count = 0;
	    next_source: for (var i = 0; i < LIST.length; ++i) {
		src = LIST[i];
		if (src.type != 'RPC') continue;
		if (!app_id || app_id == src.node.id) {
		    if (src.capabilities) {
			var caps = Object.keys(src.capabilities);
			for (var j = 0; j < caps.length; ++j) {
			    method = caps[j];
			    if (command.startsWith(method+'/')) {
				// A valid method of the src
				args = command.slice(method.length + 1).split('/');
				cap = src.capabilities[method];
				var msg = { method: method, id: method};
				if (cap.schema) {
				    msg.params = {};
				    for (var k = 0; k < cap.schema.length && k < args.length; ++k) {
					msg.params[cap.schema[k]] = args[k];
				    }
				} else {
				    // No schema, just pass 'args' array
				    msg.params = args;
				}
				send_ws_message(src, msg);
				send_count += 1;
				continue next_source;
			    }
			}
		    }
		    args = command.split('/');
		    method = args.shift();
		    send_ws_message(src, { method: method, id: method, params: args});
		    send_count += 1;
		}
	    }
	    if (!send_count)
		show_error(app_id + ' is not present');
	    return;
	} else {
	    method = params.datum;
	    var app = params.target;
	    while (app) {
		if (app === elem) break; // App div not found
		if (app.classList.contains('application')) {
		    src = app.__data__;
		    if (!src || !src.capabilities) break;
		    cap = src.capabilities[method];
		    if (!cap) break;
		    cap._reply = undefined;
		    d3.select("#methods")
			.selectAll(".application")
			.filter(function (d) { return d === src;})
			.selectAll(".button")
			.filter(function (d) { return d == method;})
			.classed("fail ok", false);
		    if (cap.schema) {
			d3.select("#command_input .name")
			    .text(src.node.id + "/" + method + "/" + cap.schema.join("/"));
			d3.select("#command_input input")
			    .property("value", src.node.id + "/" + method + "/")
			    .node().focus();
			return;// ...not sending anything yet, wait for input
		    }
		    send_ws_message(src, { method: method, id: method});
		    break;
		}
		app = app.parentNode;
	    }
	}
    }

    function add_command_input () {
	var cmd = d3.select("#methods-content")
		.append("div")
		.attr("id", "command_input")
		.attr("class", "application");
	cmd.append("div")
	    .attr("class", "name")
	    .text("Command");
	cmd.append("form")
	    .attr("class", "control")
	    .attr("data-submit", "sendCommand")
	    .call(uitools.add_submit_action)
	    .append("input")
	    .attr("name", "command")
	    .attr("type", "text");
    }
    
    function update_capabilities() {
	var apps = LIST.filter(function (src) {
		    if (src.capabilities == undefined) return false;
		    var keys = Object.keys(src.capabilities);
		    return keys.length > 0;
	});
	if (apps.length == 0) {
	    // No applications with capabilities
	    d3.select("#methods-content")
		.text("")
		.append("div")
		.attr("class", "application")
		.append("div")
		.attr("class", "name")
		.text("No Applications");
	    return;
	}
	var targets = d3.select("#methods-content")
		.text("")
		.selectAll("div")
		.data(apps);
	targets.enter()
	    .append("div")
	    .attr("class", "application")
	    .each(function (src) {
		var set = d3.select(this);
		set.append("div")
		    .attr("class", "name")
		    .text(function (src) { return src.name;});
		var keys = Object.keys(src.capabilities).sort();
		// Sort capabilities into groups
		var groups = {};
		for (var i = 0; i < keys.length; ++i) {
		    var cap = keys[i];
		    var group = src.capabilities[cap].group;
		    if (group === undefined) {
			group = '_default';
			src.capabilities[cap].group = group;
		    }
		    if (groups[group] === undefined)
			groups[group] = [cap];
		    else
			groups[group].push(cap);
		}
		var cmd = set.selectAll("div.control")
			.data(Object.keys(groups).sort())
			.enter()
			.append("div")
			.attr("class", "control")
			.selectAll("div.command")
			.data(function (d) { return groups[d];})
			.enter()
			.append("div")
			.attr("class", "command");
		cmd.append("div")
		    .attr("class", function (d) {
			var cls = "button";
			console.log(d);
			var reply = src.capabilities[d]._reply;
			if (reply) {
			    if (reply.error)
				cls += " fail";
			    else if (reply.result)
				cls += " ok";
			}
			return cls;
		    })
		    .call(uitools.add_click_action)
		    .text(function (d) { return d;});
		cmd.append("div")
		    .attr("class", "tooltip bottom")
		    .call(uitools.add_tooltip_action)
		    .text(function (d) {
			return src.capabilities[d].help;
		    });
	    });
	add_command_input();
    }

    function select_control(src, cap) {
	return d3.select("#methods")
	    .selectAll(".application")
	    .filter(function (d) { return d === src;})
	    .selectAll(".control")
	    .filter(function (d) { return d == src.capabilities[cap].group;});
    }
    
    var SOURCE_UPDATE = {
	"RPC": function (src) {
	    var data = src.node.config;
	    if (!data) return;
	    if (data.id === undefined) {
		// Assume notification
		if (data.method == 'capabilities') {
		    src.capabilities = data.params;
		    update_capabilities();
		} else if (data.method == 'get-list') {
		    // get-list notification
		    src.node.config = data.params;
		    sma_get_list(src);
		} else {
		    var ctl = select_control(src, data.method);
		    ctl.selectAll(".button")
			.classed("ok notified", function (d) { return d == data.method;});
		    ctl.selectAll(".button")
			.filter(function (d) { return d == data.method;})
			.classed("fail", false);
		}
	    } else if (data.method !== undefined) {
		// No methods implemented by the this GUI
		// Invalid request, send error
		src.ws.send({error: {code: -32601, message: "Method not found"}, id: data.id});
	    } else if (src.capabilities) {
		var cap = src.capabilities[data.id];
		if (!cap) return; // unknown method in reply
		cap._reply = data; // Remember last reply
		ctl = select_control(src, data.id);
		if (data.result !== undefined) {
		    // Succesful completion of a previous method request
		    src.node.error = false;
		    if (data.id == 'get-list') {
			src.node.config = data.result;
			sma_get_list(src);
		    }
		    // Set OK to current button, clear from others in group
		    ctl.selectAll(".button")
			.classed("ok", function (d) { return  d == data.id;});
		    // Remove fail from current button (don't touch others)
		    ctl.selectAll(".button")
			.filter(function (d) { return d == data.id;})
			.classed("fail notified", false);
		} else if (data.error !== undefined) {
		    // Error completion of a previouse request.
		    ctl.selectAll(".button")
			.filter(function (d) { return d == data.id;})
			.classed("fail", true);
		}
	    }
	    // silently ignore all non-conformant messages (no
	    // 'method', 'error' or 'result' present).
	},

	"APP": function (src) {
	    var node = src.node;
	    var data = node.config;
	    if (data && data.msg && data.app) {
		var app = GRAPH.port(node, data.app);
		app.config = data.msg;
		if (SOURCE_UPDATE[data.app])
		    SOURCE_UPDATE[data.app](app);
	    }
	},
	"SMA": sma_get_list,

	"RTC": function (src) {
	    var node = src.node;
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
			if (ueConfig.rnti !== undefined) {
			    ue_list[ueConfig.rnti] = GRAPH.node(enb.id + '_UE_'+ ueConfig.rnti, ueConfig.rnti, INFO_UE);
			}
		    }
		}
		if (config.LC.lcUeConfig) {
		    for (j = 0; j < config.LC.lcUeConfig.length; ++j) {
			ueConfig = config.LC.lcUeConfig[j];
			if (ueConfig.rnti !== undefined) {
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
			GRAPH.relation(enb, ue, 'connection', lbls, style, GRAPH.MARKER.END);

			if (ue.timechart && !ue.error) {
			    var bytes = [ pdcp.pktTxBytes, pdcp.pktRxBytes ];
			    var stamp = Date.now() / 1000;
			    if (ue.timechart.bytes !== undefined) {
				ue.timechart.chart.append(
				    stamp, /* seconds! */
				    ue.timechart.bytes.map(function (d, i) {
					if (d === undefined || bytes[i] === undefined)
					    return undefined;
					else
					    // Value is bits/second estimate
					    return ((bytes[i] - d) * 8) / (stamp - ue.timechart.stamp);
				    }));
			    }
			    ue.timechart.bytes = bytes;
			    ue.timechart.stamp = stamp;
			}
		    }
		}
		if (enb.id == show_id)
		    show_config(enb.config);
	    }
	}
    };

    // These are called once when the source is opened. Mainly for
    // WebSocket APIs that require some initial (once only) messages
    // after opening the socket.
    var SOURCE_OPEN = {
	RPC: function (src) {
	    src.ws.send(JSON.stringify({method: 'capabilities'}));
	},
	SMA: function (src) {
	    src.ws.send(JSON.stringify('get-list'));
	}
    };
    // These are called once when the source is closed
    var SOURCE_CLOSED = {
	RPC: function (src) {
	    src.capabilities = undefined;
	    update_capabilities();
	}
    };
    
    function open_src(src) {
	if (src.ws && SOURCE_OPEN[src.type])
	    SOURCE_OPEN[src.type](src);
    }
    function close_src(src) {
	if (SOURCE_CLOSED[src.type])
	    SOURCE_CLOSED[src.type](src);
    }

    function update_src(src) {
	if (!src.node) return;

	GRAPH.show(src.node);
	if (src.node.id == show_id) {
	    show_config(src.node.config);
	}
	if (src.node.error)
	    return; // Don't refresh links from a node in error state

	// Graphic update...
	if (SOURCE_UPDATE[src.type])
	    SOURCE_UPDATE[src.type](src);
    }

    function update_all() {
    	GRAPH.hideAll();
    	for (var s = 0; s < LIST.length; ++s)
    	    update_src(LIST[s]);
    	GRAPH.update();
    }

    // var URL_PARSER = document.createElement('a');
    function url(href) {
	// Support only hostname substitution...
	return href.replace('*', window.location.hostname);
	// FIX LATER...
	// URL_PARSER.href = href;
	// href =
	//     (URL_PARSER.protocol == '_' ? window.location.protocol : URL_PARSER.protocol) +
	//     '//' + (URL_PARSER.host == '_' ? window.location.host : URL_PARSER.host) +
	//     URL_PARSER.pathname +
	//     URL_PARSER.search +
	//     URL_PARSER.hash;
	// console.log(href);
	//return href;
    }
    
    function refresh(src) {
	d3.json(url(src.url), function (error, data) {
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
	    src.ws = new WebSocket(url(src.url));
	    console.log("Trying WS");
	    src.ws.onopen = function () {
		if (src.node)
		    src.node.error = false;
		if (src.timer > 0) {
		    console.log("WS Open");
		    open_src(src);
		} else {
		    console.log("WS Cancel open");
		    src.ws.close();
		    close_src(src);
		}
		update_src(src);
		GRAPH.update();
	    };
	    src.ws.onclose = function () {
		src.ws = undefined;
		if (src.node)
		    src.node.error = true;
		console.log("WS Closed");
		if (src.timer > 0)
		    src.timeout = setTimeout(src.refresh, src.timer*1000);
		else
		    src.timeout = undefined;
		close_src(src);
		update_src(src);
		GRAPH.update();
	    };
	    src.ws.onerror = function (evt) {
		if (src.node)
		    src.node.error = true;
		console.log(evt);
		update_src(src);
		GRAPH.update();
	    };
	    src.ws.onmessage = function (evt) {
		if (src.node) {
		    src.node.error = false;
		    var msg = JSON.parse(evt.data);
		    console.log("received:", msg);
		    src.node.config = msg;
		}
		update_src(src);
		GRAPH.update();
	    };
	}
	update_src(src);
	GRAPH.update();
    }
    
    function resize(elem, param) {
	// expandBottom(elem,param);
	GRAPH.resize();
	GRAPH.update();
    }

    function setSources(sources) {
	// Check validity of the new list
	// - source[i].name must be unique within the list
	var names = {};
	for (var i = 0; i < sources.length; ++i) {
	    var src = sources[i];
	    if (names[src.name]) {
		show_error('The source name ' + src.name + ' used multiple times');
		return false;
	    }
	    names[src.name] = true;
	}

	// Stop old timers
	for (i = 0; i < LIST.length; ++i) {
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
		src.node = GRAPH.node(src.name,undefined, INFO_APP);
		src.node.error = true; // Start in error state until ws connection is up
		src.refresh = function () { refresh_ws(src); };
	    } else {
		src.node = GRAPH.node(src.name, undefined, INFO_RTC);
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
	update_capabilities();
	GRAPH.update();
	return true;
    }

    function node_presentation(nodes) {
	nodes.append("text")
	    .attr("class", "stats")
	    .attr("dx", GRAPH.NODE.R)
	    .attr("dy", -GRAPH.NODE.R);
	// nodes.filter(function (d) { return d.info === INFO_APP;})
	//     .append("circle")
	//     .attr("r", GRAPH.NODE.R * 0.6);
	nodes.filter(function (d) { return d.info === INFO_LC_UE;})
	    .append("g")
	    .attr("transform", "translate("+(GRAPH.NODE.R/2)+','+(-GRAPH.NODE.R)+')')
	    .attr("class", "timechart")
	    .each(function (d) {
		var g = d3.select(this);
		g.append("rect")
		    .attr("width", 100)
		    .attr("height", GRAPH.NODE.R*2);
		d.timechart = {
		    chart: timechart(g, 100, GRAPH.NODE.R*2, 100)
		};
	    });
    }

    function node_status_indicator(nodes) {
	nodes.filter(function (d) { return !d.error;}).selectAll(".error_x").remove();
	var errors = nodes.filter(function (d) { return d.error;})
		.selectAll(".error_x")
		.data([0])
		.enter() // ..if error_x is already present, nothing new is inserted!
		.append("path")
		.attr("class", "error_x")
		.attr("transform", "rotate(45)")
		.attr("d", d3.symbol().size(GRAPH.NODE.S*10).type(d3.symbolCross));
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
			      if (show_id == d.id) {
				  closeConfig();
			      } else if (show_id != d.id) {
				  show_id = d.id;
				  show_config(d.config);
			      }
			  }
		      }
		     );
    GRAPH.NODE.update = node_status_indicator;
    GRAPH.NODE.create = node_presentation;

    setSources(sources);

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
	setSources: setSources,
	closeConfig: closeConfig,
	closeError: closeError,
	sendCommand: sendCommand,
	GRAPH: GRAPH,
	update: update_all,
	resizeGraph: function () { resize(d3.select("#topology").node());}
    };
}
