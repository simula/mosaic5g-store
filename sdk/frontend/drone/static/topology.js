function topology(sources) {

    var LIST = [];

    var INFO_ENB = {
	// icon: "enb-black",
	icon: 'm5g-oai-ran',
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
	// icon: "RTC",
	icon: 'm5g-flexran',
	class: "rtc"
    };

    var INFO_APP = {
	// icon: "APP",
	icon: 'm5g-store',
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
	GRAPH.hidelinks('control', src.node);
    	var list = node.config;
	if (!list) return;
	for (var i = 0; i < list.length; ++i) {
	    // Pick to values from first option of the last
	    // message of the SMA_APP
	    var cell_id = list[i].cell_id;
	    var freq_min = list[i].options[0].freq_min;
	    var freq_max = list[i].options[0].freq_max;
	    var bandwidth = list[i].options[0].bandwidth;
	    var eNB_id = list[i].options[0].eNB_id;
	    if (!eNB_id) {
		// Just a testing fallback
		if (LIST[0].type == 'RTC' && LIST[0].node) {
		    eNB_id = LIST[0].node.config.eNB_config[i].eNB.eNBId;
		}
	    }
	    var cell = GRAPH.find('eNB_' + eNB_id);
	    if (cell) {
		// The 'end' parameter defines what is shown at
		// the end of the dashed line from SMA_APP to
		// eNB. The styling of the line is defined by
		// ".link.control" in style.css.
		cell.option = list[i].options[0];
		GRAPH.relation(node, cell, 'control', {'start': [list[i].options[0].MVNO_group + ' ['+freq_min+'..'+freq_max+'] ' + bandwidth]},
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

    function find_src(elem) {
	while (elem) {
	    if (elem.classList.contains('application'))
		return elem.__data__;
	    elem = elem.parentNode;
	}
	return undefined;
    }

    function numberValue(btn) {
	if (btn.value)
	    return parseInt(btn.value, 10);
	return undefined;
    }

    function buildChoice(choice) {
	// Expand substitutions within a choice list
	var list = [];
	for (var i = 0; i < choice.length; ++i) {
	    if (choice[i] == '#ENBID') {
		// Collect a list of known eNBs
		for (var j = 0; j < LIST.length; ++j) {
		    if (LIST[j].type != 'RTC') continue;
		    var node = LIST[j].node;
		    if (!node || !node.enb_list) continue;
		    for (var k = 0; k < node.enb_list.length; ++k) {
			var enb = node.enb_list[k];
			// Extract the eNBId part only
			list.push(enb.id.split('_')[1]);
		    }
		}
	    } else {
		list.push(choice[i]);
	    }		
	}
	return list;
    }
    
    function buildSchema(container, schema, prefix) {
	d3.select(container)
	    .selectAll("div.control")
	    .data(schema)
	    .enter()
	    .append("div")
	    .attr("class", "control")
	    .each(function (d) {
		var control = d3.select(this);
		if (typeof d == 'string') {
		    control
			.append("div")
			.attr("class", "name")
			.text(d);
		    control
			.append("div")
			.attr("class", "command")
			.append("input")
			.attr("type", "text")
			.attr("name", prefix + d)
			.attr("class", "button");
		} else {
		    var name = prefix + d.name;
		    control
			.append("div")
			.attr("class", "name")
			.text(d.name);
		    if (d.choice) {
			control
			    .selectAll("div.command")
			    .data(buildChoice(d.choice))
			    .enter()
			    .append("label")
			    .attr("class", "command")
			    .text(function (d) { return d === null ? 'None' : d;})
			    .append("input")
			    .attr("class", "button")
			    .attr("type", "radio")
			    .attr("name", name)
			    .attr("data-converter", d.type == 'number' ? 'numberValue' : undefined)
			    .attr("value", function (d) { return d || '';});
		    } else if (d.range) {
			control
			    .append("div")
			    .attr("class", "command")
			    .append("input")
			    .attr("class", "button")
			    .attr("type", "number")
			    .attr("name", name)
			    .attr("data-converter", 'numberValue')
			    .attr("min", d.range[0])
			    .attr("max", d.range[1])
			    .attr("step", d.range[2]);
		    } else if (d.schema) {
			buildSchema(control
				    .append("div")
				    .attr("class", "application")
				    .node(), d.schema, name + '.');
		    } else {
			control
			    .append("div")
			    .attr("class", "command")
			    .text(d)
			    .append("input")
			    .attr("type", "text")
			    .attr("name", name)
			    .attr("class", "button");
		    }
		}
	    });
    }

    function buildCommand(src, method, schema) {
	var popup = d3.select("#build_command");
	var app = popup.select(".popup-content > .application")
		.text("");
	uitools.replace_text(popup.select(".popup-header").node(), src.name + "/" + method);
	
	app.append("input")
	    .attr("type", "hidden")
	    .attr("name", "application")
	    .attr("value", src.name);
	app.append("input")
	    .attr("type", "hidden")
	    .attr("name", "method")
	    .attr("value", method);
	buildSchema(app.node(),schema, 'params.');
	popup.classed("open", true);
    }

    function prepareCommand(elem, params) {
	var src = find_src(params.target);
	if (src) {
	    buildCommand(src, params.datum, src.capabilities[params.datum].schema);
	}
    }

    
    function submitCommand(elem, msg) {
	console.log(elem, msg);
	// First, find the target application
	for (var i = 0; i < LIST.length; ++i) {
	    var src = LIST[i];
	    if (src.name == msg.application && src.type == 'RPC') {
		// Finalize message into proper request
		delete msg.application;
		msg.id = msg.method;
		send_ws_message(src, msg);
		return true;
	    }
	}
	show_error(msg.application + ' does not exist');
	return true;
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
	    src = find_src(params.target);
	    if (src && src.capabilities) {
		cap = src.capabilities[method];
		if (!cap) {
		    show_error("Method " + method + " not defined by " + src.name);
		    return;
		}
		cap._reply = undefined;
		d3.select("#methods")
		    .selectAll(".application")
		    .filter(function (d) { return d === src;})
		    .selectAll(".command")
		    .filter(function (d) { return d == method;})
		    .classed("fail ok", false);
		send_ws_message(src, { method: method, id: method});
	    }
	}
    }

    var last_command_label = "Command";
    function get_command_input() {
	var command = d3.select('#command_input input');
	if (command.empty()) return '';
	return command.property("value");
    }

    function add_command_input (current) {
	var cmd = d3.select("#methods-content")
		.append("div")
		.attr("id", "command_input")
		.attr("class", "application");
	cmd.append("div")
	    .attr("class", "name")
	    .text(last_command_label);
	cmd.append("form")
	    .attr("class", "control")
	    .attr("data-submit", "sendCommand")
	    .call(uitools.add_submit_action)
	    .append("input")
	    .attr("name", "command")
	    .attr("type", "text")
	    .property("value", current);
    }
    
    function update_capabilities() {
	// Temp solution. If input is active while executing this, try
	// to save and restore the current content. Not fully working:
	// if user is typing input while this happens, the focus is
	// lost and typing goes to wrong place.. [Correct solution: DO
	// NOT DELETE the command input div!]
	var current = get_command_input();

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
		.selectAll("div.application")
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
			.attr("data-popup", function (d) {
			    return src.capabilities[d].schema ? 'build_command' : undefined;
			})
			.call(uitools.add_click_action)
			.attr("class",  function (d) {
			    var cls = "command";
			    var reply = src.capabilities[d]._reply;
			    if (reply) {
				if (reply.error)
				    cls += " fail";
				else if (reply.result)
				    cls += " ok";
			    }
			    return cls;
			});
		cmd.append("div")
		    .attr("class", "button")
		    .each(function (d) {
			if (src.capabilities[d].label) {
			    d3.select(this).html(src.capabilities[d].label);
			} else {
			    d3.select(this).text(d);
			}
		    });
		cmd.append("div")
		    .attr("class", "tooltip bottom")
		    .call(uitools.add_tooltip_action)
		    .text(function (d) {
			return src.capabilities[d].help;
		    });
	    });
	add_command_input(current);
    }

    function select_control(src, cap) {
	// Return empty selection, if cap is undefined
	return d3.select("#methods")
	    .selectAll(".application")
	    .filter(function (d) { return d === src;})
	    .selectAll(".control")
	    .filter(function (d) { return cap && d == cap.group;});
    }

    function get_enb_node(enb_id) {
	// Create or find existing eNB node
	return GRAPH.node('eNB_' + enb_id, 'eNB ' + enb_id, INFO_ENB);
    }
    function get_ue_node(enb, ue_id, info) {
	return GRAPH.node(enb.id + '_UE_'+ ue_id, ue_id, info);
    }

    var SOURCE_UPDATE = {
	"RPC": function (src) {
	    var data = src.node.config;
	    if (!data) return;
	    console.log(data);
	    if (data.id === undefined) {
		// Assume notification
		if (data.method == 'capabilities') {
		    src.capabilities = data.params;
		    update_capabilities();
		} else if (data.method == 'get-list') {
		    // get-list notification
		    src.node.config = data.params;
		    sma_get_list(src);
		} else if (data.method) {
		    var ctl = select_control(src, src.capabilities[data.method]);
		    ctl.selectAll(".command")
			.classed("ok notified", function (d) { return d == data.method;});
		    ctl.selectAll(".command")
			.filter(function (d) { return d == data.method;})
			.classed("fail", false);
		}
	    } else if (data.method !== undefined) {
		// No methods implemented by the this GUI
		// Invalid request, send error
		src.ws.send({error: {code: -32601, message: "Method not found"}, id: data.id});
	    } else if (src.capabilities) {
		var cap = src.capabilities[data.id];
		if (cap) cap._reply = data; // Remember last reply
		ctl = select_control(src, cap);
		if (data.result !== undefined) {
		    // Succesful completion of a previous method request
		    src.node.error = false;
		    if (data.id == 'get-list') {
			src.node.config = data.result;
			sma_get_list(src);
		    }
		    // Set OK to current command, clear from others in group. Also, remove
		    // _reply from all other commands in same group.
		    ctl.selectAll(".command")
			.classed("ok", function (d) {
			    if (d != data.id) {
				var cap = src.capabilities[d];
				if (cap) {
				    if (cap._reply && cap._reply.result)
					// only remove OK replies (leave errors on)
					cap._reply = undefined;
				}
				return false;
			    }
			    return true;
			});
		    // Remove fail from current button (don't touch others)
		    ctl.selectAll(".command")
			.filter(function (d) { return d == data.id;})
			.classed("fail notified", false);
		} else if (data.error !== undefined) {
		    // Error completion of a previouse request.
		    ctl.selectAll(".command")
			.filter(function (d) { return d == data.id;})
			.classed("fail", true);
		    show_error(src.name + ': Error (' + data.error.code + ') in ' +
			       data.id + ': ' + data.error.message);
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

	    // Hide eNB's not present in the new eNB_config.
	    if (node.enb_list)
		for (var i = 0; i < node.enb_list.length; ++i) {
		    var enb = node.enb_list[i];
		    for (var rnti in enb.ue_list) {
		    	GRAPH.hide(enb.ue_list[rnti]);
		    }
		    GRAPH.hidelinks(undefined, enb);
		    GRAPH.hide(enb);
		}
	    GRAPH.hidelinks(undefined, node);
	    
	    node.enb_list = [];
	    for (i = 0; i < data.eNB_config.length; ++i) {
		var config = data.eNB_config[i];
		enb = get_enb_node(config.eNB.eNBId);
		node.enb_list.push(enb);

		GRAPH.relation(enb, node, 'rtc', {},undefined,GRAPH.MARKER.END|GRAPH.MARKER.START);
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
			    ue_list[ueConfig.rnti] = get_ue_node(enb, ueConfig.rnti, INFO_UE);
			}
		    }
		}
		if (config.LC.lcUeConfig) {
		    for (j = 0; j < config.LC.lcUeConfig.length; ++j) {
			ueConfig = config.LC.lcUeConfig[j];
			if (ueConfig.rnti !== undefined) {
			    ue_list[ueConfig.rnti] = get_ue_node(enb, ueConfig.rnti, INFO_LC_UE);
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
		if (enb.id == show_id)
		    show_config(enb.config);
	    }
	    for (i = 0; i < data.mac_stats.length; ++i) {
		enb = get_enb_node(data.mac_stats[i].eNBId);
		for (var m = 0; m < data.mac_stats[i].ue_mac_stats.length; ++m) {
		    var stats = data.mac_stats[i].ue_mac_stats[m];
		    if (!stats) continue;
		    var ue = enb.ue_list[stats.rnti];
		    if (!ue) {
			// mac_stats ghosts, UE's not shown by enb
			// config -- for now just ignore (caused bad
			// flickering because they are deleted in
			// above enb loop, and recreated here)
			
			// ue = GRAPH.node(enb.id + '_UE_'+ stats.rnti, stats.rnti, INFO_UE);
			// enb.ue_list[stats.rnti] = ue;
			continue;
		    }
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
		    GRAPH.relation(ue, enb, 'oai', lbls, style, GRAPH.MARKER.END);
		    lbls.end = l;
		    lbls.arrow = [''+pdcp.pktTxBytesW];
		    GRAPH.relation(enb, ue, 'oai', lbls, style, GRAPH.MARKER.END);
		    
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
	nodes.filter(function (d) { return d.info === INFO_ENB;})
	    .insert("circle", ":first-child")
	    .attr("class", "config")
	    .attr("r", GRAPH.NODE.R-8)
	    .attr("cx", "-2px");
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
		.each(function (d) {
		    var freq = d.config.cellConfig[0].dlFreq;
		    if (d.option && freq) {
			var waiting = (d.option.freq_min <= freq && d.option.freq_max <= freq);
			d3.select(this)
			    .select(".config")
			    .classed("waiting", waiting);
			if (!waiting) {
			    // "borrow" existing "vendor" field for GROUP
			    d3.select(this)
				.select(".vendor")
				.text(d.option.MVNO_group);
			}
		    }
		})
		.select("text.stats")
		.selectAll("tspan")
	// The following fields from cellConfig[0] will be show on
	// right of the eNB icon. Generated below...
		.data(['cellId', 'dlFreq', 'ulFreq', 'eutraBand', 'dlPdschPower', 'ulPuschPower', 'dlBandwidth', 'ulBandwidth']);
	stats.enter()
	    .append("tspan")
	    .attr("x", GRAPH.NODE.R+5)
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
	prepareCommand: prepareCommand,
	submitCommand: submitCommand,
	numberValue: numberValue,
	GRAPH: GRAPH,
	update: update_all,
	resizeGraph: function () { resize(d3.select("#topology").node());}
    };
}
