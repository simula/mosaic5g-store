uitools.callbacks(
    (function () {

	var CONFIG = [
	    // {
	    // 	id: 'neo4j',
	    // 	cwd: '/home/msa/COHERENT/neo4j-community-3.2.3',
	    // 	command: ['./bin/neo4j', 'console']
	    // },
	    // {
	    // 	id: 'ls',
	    // 	command: ['ls']
	    // },
	    // {
	    // 	id: 'ps',
	    // 	command: ['ps', 'aux'],
	    // 	autostart: true,
	    // 	user: 'msa'
	    // },
	    // {
	    // 	id: 'sma-app',
	    // 	command: ['python','sma_app.py'],
	    // 	cwd: '/home/msa/COHERENT/store/sdk',
	    // 	user: 'msa'
	    // },
	    // {
	    //  	id: 'top',
	    // 	command: ['top']
	    // },
	    // {
	    // 	id: 'flexran-rtc',
	    // 	command: ['./run_flexran_rtc.sh'],
	    // 	cwd: '/home/msa/COHERENT/flexran-rtc',
	    // 	autostart: true
	    // },
	    // {
	    // 	id: 'epc-forward',
	    // 	command: ['ssh','-L','8081:localhost:8080', 'epc-msa.local' ,'sleep','30'],
	    // 	drone: 'ws://localhost:8081/drone',
	    // 	user: 'msa',
	    // 	autostart: true,
	    // 	config: [
	    // 	    {
	    // 		id: 'hss',
	    // 		cwd: '/home/msa/openair-cn/scripts',
	    // 		command: ['./run_hss'],
	    // 		autostart: true,
	    // 		config: [
	    // 		    {
	    // 			id: 'mme',
	    // 			cwd: '/home/msa/openair-cn/scripts',
	    // 			command: ['./run_mme'],
	    // 			autostart: true
	    // 		    },
	    // 		    {
	    // 			id: 'spgw',
	    // 			cwd: '/home/msa/openair-cn/scripts',
	    // 			command: ['./run_spgw'],
	    // 			autostart: true
	    // 		    }
	    // 		]
	    // 	    }
	    // 	    // {
	    // 	    // 	id: 'epc-msa',
	    // 	    // 	cwd: '.',
	    // 	    // 	command: ['ps','aux']
	    // 	    // }
	    // 	]
	    // },
	    // {
	    // 	id: 'enb-forward',
	    // 	command: ['ssh','-L','8082:localhost:8080', 'ttesma@ettus02.local','sleep','30'],
	    // 	drone: 'ws://localhost:8082/drone',
	    // 	user: 'msa',
	    // 	autostart: true,
	    // 	config: [
	    // 	    {
	    // 		id: 'eNB',
	    // 		cwd: '/home/ttesma/openairinterface5g/cmake_targets/lte_build_oai/build',
	    // 		command: ['sudo','-E',
	    // 			  './lte-softmodem',
	    // 			  '-O', '/home/ttesma/openairinterface5g/targets/PROJECTS/GENERIC-LTE-EPC/CONF/enb.band7.tm1.usrpb210.vtt2.conf',
	    // 			  '-d']
	    // 	    },
	    // 	    {
	    // 		id: 'ettus02',
	    // 		cwd: '.',
	    // 		command: ['ps','aux']
	    // 	    },
	    // 	]
	    // },
	    // {
	    // 	id: 'enb2-forward',
	    // 	command: ['ssh','-L','8083:localhost:8080', 'coherent@192.168.12.83','sleep','30'],
	    // 	drone: 'ws://localhost:8083/drone',
	    // 	autostart: true,
	    // 	user: 'msa',
	    // 	config: [
	    // 	    {
	    // 		id: 'eNB2',
	    // 		cwd: '/home/coherent/openairinterface5g/cmake_targets/lte_build_oai/build',
	    // 		command: ['sudo','-E',
	    // 			  './lte-softmodem',
	    // 			  '-O','/home/coherent/enb2.conf',
	    // 			  '-d']
	    // 	    // },
	    // 	    // {
	    // 	    // 	id: 'coherent-enb',
	    // 	    // 	cwd: '.',
	    // 	    // 	command: ['ps','aux']
	    // 	    }]
	    // }
	];
	
	function prepareTask(elem, params) {
	    elem.reset(); // assumes elem is form
	    if (!params.datum) return;
	    var task = d3.select(params.datum).datum();
	    if (!task) return;
	    if (task.task) {
		var keys = Object.keys(task.task);
		for (var i = 0; i < keys.length; ++i) {
		    var key = keys[i];
		    var val = task.task[key];
		    if (Array.isArray(val))
			val = val.join("\n");
		    // .... argh! using 'id' as 'name' messes up
		    // normal element id within form (elem.id returns
		    // the input element with "name=id")
		    if (key == 'id') key = '_id';
		    if (key != 'autostart') {
			d3.select(elem)
			    .datum(task.task)
			    .selectAll("[name='"+key+"']")
			    .property("value", val);
		    } else {
			d3.select(elem)
			    .selectAll("[name='autostart']")
			    .property("checked", val);
		    }
		}
	    }
	    uitools.reset(elem.id);
	}

	function modifyTask(elem, params) {
	    console.log(elem, params);
	    var task = d3.select(elem).datum();
	    var keys = Object.keys(params);
	    delete task.autostart;
	    for (var i = 0; i < keys.length; ++i) {
	     	var key = keys[i];
		var val = params[key];
		// Reverse the "id hack" (see prepareTask)
		if (key == '_id') key = 'id';
		if (val == '') {
		    delete task[key];
		} else {
		    if (key == 'command') {
			// Convert command args into array (each line is arg)
			val = val.split("\n");
		    } else if (key == 'autostart') {
			val = (val === 'on');
		    }
		    task[key] = val;
		}
	    }
	    return true;
	}

	function run_stop_task() {
	    // this.__data__ -> <tab element>
	    // <tab element>.__data__ -> task object
	    d3.event.stopPropagation();
	    var task = this.__data__.__data__;
	    if (task.state == "running" || task.state == "stopping")
		task.stop();
	    else
		task.start();
	}
	
	function _add_source_row(row) {
	    row.append("td")
		.attr("class", "popup-menu-open")
		.attr("data-popup-menu", "source_types")
		.attr("data-action", "setSourceType")
		.text(function (d) { return d.type ? d.type : 'Unknown';})
		.call(uitools.add_menu_action)
		.append("input")
		.attr("name", "list[].type")
		.property("value", function (d) { return d.type;})
		.style("display", "none");
	    row.append("td")
		.append("input")
		.attr("type", "text")
		.attr("name", "list[].name")
		.attr("value", function (d) { return d.name;});
	    row.append("td")
		.append("input")
		.attr("type", "text")
		.attr("name", "list[].url")
		.attr("value", function (d) { return d.url;});
	    row.append("td")
		.append("input")
		.attr("type", "number")
		.attr("name", "list[].timer")
		.attr("value", function (d) { return d.timer;});
	}

	function setSourceType(elem, params) {
	    uitools.replace_text(elem, params.value ? params.value : 'Undefined');
	    d3.select(elem).select("input").property("value", params.value);
	}

	function prepareSources(elem, params) {
	    var sources = d3.select(elem)
		    .select("table tbody")
		    .selectAll("tr")
		    .data(TOPOLOGY.getSources());
	    sources.exit().remove();
	    sources
		.enter()
		.append("tr")
		.merge(sources)
		.text("")
		.call(_add_source_row);
	}

	function addSources(elem, params) {
	    d3.select("#edit-sources")
		.select("table tbody")
		.append("tr")
		.datum({ url: '', timer: 1})
		.call(_add_source_row);
	    // resize popup
	    uitools.reset("edit-sources");
	}

	function modifySources(elem, params) {
	    console.log(params);
	    TOPOLOGY.setSources(params.list);
	    return true;
	}
	
	function expandBottom(elem, params) {
	    // Expand element height to the bottom of page (experimental)
	    var rect = elem.getBoundingClientRect();
	    var h = window.innerHeight;
	    // Ad hoc: -30 for potential borders and margins -- not a
	    // stable solution
	    var vh = Math.max(200, (h - rect.top) - 30);
	    d3.select(elem).style("height", vh + "px");
	}
	function openTaskTab(elem, params) {
	    // Called when a task tab has been opened
	    var d = params.datum;
	    expandBottom(d3.select(elem).select('.log').node(), params);
	    if (d) d.open();
	}


	function list_tasks() {
	    // Return flat list of tasks
	    var result = [];

	    function flatten(cfg) {
		for (var i = 0; i < cfg.length; ++i) {
		    result.push(cfg[i]);
		    if (cfg[i].config)
			flatten(cfg[i].config);
		}
	    }
	    flatten(CONFIG);
	    return result;
	}

	function create_tasks() {
	    // Build tree of Task objects, return flat list of created
	    // Task objects
	    var result = [];

	    function flatten(cfg, parent) {
		for (var i = 0; i < cfg.length; ++i) {
		    var task = drone(cfg[i], parent);
		    result.push(task);
		    if (cfg[i].config)
			flatten(cfg[i].config, task);
		}
	    }
	    flatten(CONFIG);
	    return result;
	}

	function task_message(d, msg) {
	    if (msg.status) {
		var bar = uitools.tab_bar(d.element);
		if (bar) {
		    if (d.state)
			bar.classList.replace(d.state,msg.status);
		    else
			bar.classList.add(msg.status);
		    d.state = msg.status;
		}
		d3.select(d.element).select(".state").text(msg.status);
		if (msg.status == 'starting' || msg.status == 'running') {
		    // Start next level of tasks
		    for (var i = 0; i < d.children.length; ++i) {
			d.children[i].start();
		    }
		}
	    }
	    if (msg.error) {
		d3.select(d.element).select(".error").text(msg.error);
	    }
	}

	function update_menu_list(id, menu_list, empty) {
	    menu_list = menu_list.sort();
	    // Add empty choice, if desired
	    if (empty) menu_list.unshift("");

	    var items;
	    items = d3.select("#" + id)
		.selectAll("li")
		.data(menu_list);
	    items.exit().remove();
	    items.enter()
		.append("li")
		.merge(items)
		.attr("data-value", function (d) {
		    return d;
		})
		.call(uitools.add_click_action)
		.text(function (d) {
		    return d ? d : empty;
		});
	}
	
	function handle_reply(error, reply) {
	    if (error)
		console.log(error);
	    if (!reply) {
		console.log("NULL reply for: " + error);
		return;
	    }

	    if (reply.error) {
		console.log(reply.error);
		return;
	    } else if (!reply.result) {
		console.log("No result in reply");
	    } else if (reply.id == 'tasks') {
		update_menu_list(reply.id, reply.result, "no task");
	    } else {
		console.log(error,reply);
	    }
	}

	function updateDashBoard() {
	    var drones = d3.select("#drones");
	    drones.selectAll("div.tab.task").remove();
	    drones.selectAll("ul.tabsbar").remove();
	    var tasks = drones
		    .attr("class", "tabs vertical")
		    .selectAll("div.tab.task")
		    .data(create_tasks())
		    .enter()
		    .append("div")
		    .attr("class", "tab task")
		    .attr("data-label", function (d) { return d.task.id;})
		    .attr("data-resize", "openTaskTab")
		    .attr("data-open", "openTaskTab");
	    
	    tasks.append("p")
		.attr("class", "command")
		.text(function (d) { return d.task.command.join(' ');});
	    var state = tasks
		    .append("div")
		    .attr("class", "horizontal");
	    state.append("input")
		.attr("type", "button")
		.attr("value", "\u25B6 start")
		.on("click", function (d) { d.start();});
	    state.append("input")
		.attr("type", "button")
		.attr("value", "\u25FC stop")
		.on("click", function (d) { d.stop();});
	    state.append("input")
		.attr("type", "button")
		.attr("value", "clear")
		.on("click", function (d) { d.clear();});
	    state.append("div")
		.attr("class", "state");
	    state.append("div").text(":\u00a0");
	    state.append("div")
		.attr("class", "error");
	    
	    var drone_console = tasks
		    .append("div")
		    .attr("tabindex", "0")
		    .attr("class", "log")
		    .on("keypress", function (d) { d.keypress();});
	    
	    tasks.each(function (d) { d.init(this, task_message);});
	    
	    d3.select("#drones").each(function () { uitools.prepare_tabs(this);});

	    // Add task "bullet" balls into tab labels
	    d3.selectAll("#drones .tab.task").each(function (d) {
		var bar = uitools.tab_bar(this);
		if (bar) {
		    var depth = 0;
		    while (d.parent) {
			depth += 1;
			d = d.parent;
		    }
		    d3.select(bar)
			.insert("span", ":first-child")
			.attr("class", "bullet")
			.style("margin-left", depth + "em");
		}
	    });
	    // Add control edit buttons
	    d3.selectAll("#drones .tab").each(function (d) {
		var bar = uitools.tab_bar(this);
		if (bar) {
		    // If actual tab defines "data-popup", then copy
		    // the value into the tab bar element (the default
		    // edit-task has been overridden). [ copy all?]
		    if (this.dataset.popup)
			bar.dataset.popup = this.dataset.popup;
		    var ctrl = d3.select(bar)
			    .append("span")
			    .attr("class", "control");
		    // For tasks, add run/stop button
		    if (this.classList.contains("task")) {
			// This is internal in coherent.js -- map
			// click directly to action (no need to route
			// via uitools).
			ctrl.append("button")
			    .attr("class", "runstop")
			    .on("click", run_stop_task);
		    }

		    // Edit task/sources button (this uses uitools
		    // popup panel functionality -- route via uitools)
		    ctrl.append("button")
			.text("\u270E")
			.call(uitools.add_click_action);
		}
	    });
	    TOPOLOGY.update();
	}

	function build_saveset() {
	    return {
		config: CONFIG,
		sources: TOPOLOGY.getSources(),
		graph: TOPOLOGY.GRAPH.saveset()
	    };
	}
	function restore_saveset(saveset) {
	    if (saveset.config) CONFIG = saveset.config;

	    // -- Code to be removed eventually --
	    // ...support old format of sources not containing the
	    // type field. 
	    for (var i = 0; i < saveset.sources.length; ++i) {
		var src = saveset.sources[i];
		if (src.type === undefined) {
		    if (src.url.startsWith("ws")) {
			src.type = "SMA";
		    } else {
			src.type = "RTC";
		    }
		}
	    }
	    // -- End fallback --

	    if (saveset.sources) TOPOLOGY.setSources(saveset.sources);
	    if (saveset.graph) TOPOLOGY.GRAPH.restore(saveset.graph);
	}

	function file_reply(error, reply, elem) {
	    console.log(error, reply, elem);
	    if (error) {
	    } else if (reply) {
		if (reply.id) {
		    d3.json("config/"+reply.id, handle_reply);
		}
	    }
	}

	function deleteTasks(elem, params) {
	    var name = params.fileName;
	    if (!name) {
		uitools.notify("The application name not given", elem);
	    } else {
		d3.json("config/tasks/" + name)
		    .send("DELETE",undefined, function (error, reply) {
			file_reply(error, reply, elem);
		    });
	    }
	    return true;
	}
	
	function saveTasks(elem, params) {
	    var name = params.fileName;
	    // fileName is not part of the saved data
	    delete params.fileName;

	    if (name === undefined) {
		// Called from menubar, save using current name (if any)
		name = d3.select("#configName").node().value;
	    }
	    if (!name) {
		uitools.notify("No configuration selected/loaded", elem);
		return true;
	    }

	    d3.json("config/tasks/" + name)
		.header("Content-Type", "application/json")
		.post(JSON.stringify(build_saveset()), function (error, reply) {
		    file_reply(error, reply, elem);
		});
	    return true;
	}

	function loadTasks(elem, params) {
	    d3.select("#configName").node().value = params.value;
	    if (!params.value) {
		CONFIG = [];
		updateDashBoard();
	    } else {
		d3.json("config/tasks/" + params.value,
			function (error, reply) {
			    if (!reply) {
				console.log("NULL reply: " + error);
			    } else {
				restore_saveset(reply);
				updateDashBoard();
			    }
			});
	    }
	    return false;
	}
	var TOPOLOGY = topology([
	    {
		type: 'RTC',
		name: 'flexran-rtc',
		url: "http://localhost:9999/stats_manager/json/all",
		timer: 1
	    },
	    {
		type: 'SMA',
		name: 'sma-app',
		url: "ws://localhost:8080/list",
		timer: 1
	    }
	]);
	
	updateDashBoard();
	d3.json("/config/tasks", handle_reply);

	return {
	    loadTasks: loadTasks,
	    saveTasks: saveTasks,
	    deleteTasks: deleteTasks,
	    modifyTask: modifyTask,
	    prepareTask: prepareTask,
	    prepareSources: prepareSources,
	    modifySources: modifySources,
	    setSourceType: setSourceType,
	    addSources: addSources,
	    openTaskTab: openTaskTab,
	    resizeGraph: TOPOLOGY.resizeGraph,
	    closeConfig: TOPOLOGY.closeConfig
	};
    })());
