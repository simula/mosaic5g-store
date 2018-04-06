// Insert dynamic D3 force graph at indicated position in the document and return the graph API

function graph(graph_selector, NAME_MAP, CALLBACKS) {

    var D3_IS_V3 = d3.version.startsWith("3.");

    if (NAME_MAP === undefined) NAME_MAP = {};
    if (CALLBACKS === undefined) CALLBACKS = {};

    // This is incremented before each udpate process (the process
    // that generates display from internal structure).
    var update_sequence = 0;

    // When a node is referenced directly or indirectly as an end
    // point of link, the current update_sequence is stored into
    // node. When generating the display, only nodes with sequence
    // value greater than display_sequence are included.
    var display_sequence = update_sequence - 1;
    
    var update_request = 0;
    var update_active = false;
    var resize_pending = false;
    
    var nodes = [];
    var links = [];
    var clusters = [];
    var nodemap = {};
    var linkmap = {};

    // The values are used as "mask" bits (marker at both ends is
    // indicated by 3).
    var MARKER = {
	NONE: 0,
	START: 1,
	END: 2
    };

    // Parameters for the node representation
    var NODE = {
 	// ... icon size (width/height of square)
	S: 50,
	// ... precompute radius of the circle around the node icon
	R: 50 * Math.sqrt(2) / 2,
	// ... translate reference point to node center.
	translate: function (x, y) { return "translate(" + (x - this.S/2) + "," + (y - this.S/2) + ")";}
    };

    var PORT = {
	// .. radius of the port circle
	S: 8,
	R: 8 * Math.sqrt(2) / 2,
	translate: function (x, y) { return "translate(" + (x - this.S/2) + "," + (y - this.S/2) + ")";}
    };

    var LINK = {
    };

    // This defines the initial settings
    var VIEW = {
	name: '',
	freeze_node_on_drag: true,
	freeze_port_on_drag: false
    };

    var view = { }; // Actual view

    function nodes_only(force) {
	var init = force.initialize;
	force.initialize = function () {
	    init(nodes.filter(function (d) {
		return !d.node;
	    }));
	};
	return force;
    }
    function ports_only(force) {
	var init = force.initialize;
	force.initialize = function () {
	    init(nodes.filter(function (d) {
		return d.node;
	    }));
	};
	return force;
    }
    // function cluster_only(force) {
    // 	var init = force.initialize;
    // 	force.initialize = function () {
    // 	    var n = clusters;
    // 	    console.log("cluster size=", n.length);
    // 	    init(n);
    // 	};
    // 	return force;
    // }

    function forceCluster(alpha) {
	var k = alpha * 0.1;
    	for (var i = 0, n = nodes.length; i < n; ++i) {
    	    var node = nodes[i];
	    if (node.node) continue;
    	    var cluster = clusters[node.cluster || 0];
	    if (!cluster) return; // can happen, if node.cluster is changed to yet unseen cluster in application
    	    node.vx -= (node.x - cluster.x) * k;
    	    node.vy -= (node.y - cluster.y) * k;
    	}
    }

    var force;
    var zoom;
    var drag;
    if (D3_IS_V3) {
	force = d3.layout.force()
	    .gravity(0.4)
	    .linkDistance(100)
	    .linkStrength(0.9)
	    .on("tick", tick)
	    .stop();
	zoom = d3.behavior.zoom()
	    .scaleExtent([0.2,6])
	    .on("zoom", zoomed);
	drag = force.drag()
	    .origin(function (d) { return d;})
	    .on("dragstart", dragstarted)
	    .on("drag", dragged)
	    .on("dragend", dragended);
    } else {
	force = d3.forceSimulation()
	    .force("link", d3.forceLink().id(function (d) { return d.id;}).distance(150))
	    .force("collide", d3.forceCollide())
	    .force("cluster", forceCluster)
	    .force("charge", nodes_only(d3.forceManyBody()
	    				.strength(-2000)
	    				.distanceMax(500)
	    			       ))
	    // .force("center", d3.forceCenter())
	    .on("tick", tick);
	zoom = d3.zoom()
	    .scaleExtent([0.2,6])
	    .on("zoom", zoomed);
	drag = d3.drag()
	    .clickDistance(3)
	    .on("start", dragstarted)
	    .on("drag", dragged)
	    .on("end", dragended);
    }
    // The graph always fills the containter identified by the
    // "grap_selector". The caller is responsible for fixing the size
    // of the container.
    var svg = d3.select(graph_selector)
		.insert("svg", ":first-child")
		.style("position", "absolute")
		.style("top", 0)
		.style("left", 0)
		.on("contextmenu", graph_context)
		.call(zoom)
	    .append("g");

    var defs = d3.select('#graph-defs');
    if (defs.empty()) {
	// defs markers use element id's which are global to
	// document. Create graph defs only once and share it with
	// other instances of graph.
	defs = svg.append("defs").attr("id", "graph-defs");
	defs.append("g")
	    .attr("id", "marker-triangle")
	    .append("path")
	    .attr("d", "M 0 0 L 10 5 L 0 10 z");
    }
    var svg_background = svg.append("g").attr("class", "background");
    // Group links into 'g' that appears before nodes
    var svg_links = svg.append("g").attr("class", "links");
    // Group nodes after links, so that nodes are on top of links
    var svg_nodes = svg.append("g").attr("class", "nodes");

    var node = svg_nodes.selectAll(".node");
    var link = svg_nodes.selectAll(".link");
    
    var intervalId;
    var frozen = false;
    
    // The width and height of the SVG are maintained dynamically
    // from the resize function.
    var width;
    var height;
    var view_x = 0;
    var view_y = 0;
    var view_w = width;
    var view_h = height;
    var view_s = 1;

    function graph_context() {
	var pos = d3.mouse(this);
	var xy = [
		pos[0]/view_s + view_x,
		pos[1]/view_s + view_y
	];
	if (CALLBACKS.graphContext) {
	    d3.event.preventDefault();
    	    d3.event.stopPropagation();
	    (CALLBACKS.graphContext)(xy);
	}
    }

    function reset_frame() {
	view_w = width / view_s;
	view_h = height / view_s;
    }

    function reset_size() {
	var graph = d3.select(graph_selector).node();
	width = graph.clientWidth;
	height = graph.clientHeight;
	d3.select(graph_selector).select("svg")
	    .attr("width", width)
	    .attr("height", height);
	reset_frame();
	resize_pending = false;
	if (D3_IS_V3) {
	} else {
	    // force.force("center", d3.forceCenter(view_w/2,view_h/2));
	    force.force("x", nodes_only(d3.forceX(view_w/2)));
	    force.force("y", nodes_only(d3.forceY(view_h/2)));
	    // force.force("x", nodes_only(d3.forceX(0.001)));
	    // force.force("y", nodes_only(d3.forceY(0.001)));
	}
    }
    
    function zoomed() {
	if (D3_IS_V3) {
	    view_s = d3.event.scale;
	    view_x = -d3.event.translate[0] / view_s;
	    view_y = -d3.event.translate[1] / view_s;
	    svg.attr("transform", "translate(" + d3.event.translate
		     + ")scale(" + d3.event.scale + ")");
	} else {
	    view_s = d3.event.transform.k;
	    view_x = -d3.event.transform.x / view_s;
	    view_y = -d3.event.transform.y / view_s;
	    svg.attr("transform", d3.event.transform);
	}
	reset_frame();
    }

    function dragstarted(d) {
	if (D3_IS_V3) {
	    d3.event.sourceEvent.stopPropagation();
	} else {
	    if (!d3.event.active) force.alphaTarget(0.3).restart();
	    d.fx = d.x;
	    d.fy = d.y;
	}
	if (d3.event.sourceEvent.button == 0)
	    d.dragged = true;
    }

    function dragged(d) {
	if (D3_IS_V3) {
	} else {
            d.fx = d3.event.x;
            d.fy = d3.event.y;
	}
    }

    function dragended(d) {
	d.dragged = false;
	if (D3_IS_V3) {
	} else {
            if (!d3.event.active) force.alphaTarget(0);
	}
	if (!d.fixed)
	    d.fixed = d.node ? view.freeze_port_on_drag : view.freeze_node_on_drag;
	if (D3_IS_V3) {
	} else {
	    if (!d.fixed) {
		d.fx = null;
		d.fy = null;
	    }
	}
    }

    function setRefresh(interval) {
	if (intervalId) clearInterval(intervalId);
	intervalId = undefined;
	var delay = interval.value * 1000;
	if (delay > 0)
	    intervalId = setInterval(refresh, delay);
    }

    function add_unique_labels(list, labels) {
	if (!labels || labels.length == 0)
	    return list;

	if (!list) list = [];

	// ... and add label if different from existing ones.
	nextlabel:
	for (var k = 0; k < labels.length; ++k) {
	    if (!labels[k]) continue; // ..for now, ignore empy labels
	    for (var i = 0; i < list.length; ++i) {
		if (list[i] == labels[k]) continue nextlabel;
	    }
	    list.push(labels[k]);
	}
	return list;
    }

    /**
     * Add or modify a link object in graph
     *
     */
    function add_link(source, target, type, label, style, marker) {

	// ... also make target and source visible if hidden.
	source.sequence = update_sequence;
	if (label.source) {
	    source = port_node(source, label.source);
	    source.sequence = update_sequence;
	}
	target.sequence = update_sequence;
	if (label.target) {
	    target = port_node(target, label.target);
	    target.sequence = update_sequence;
	}

	if (source.id == target.id)
	    return null; // No link generated

	var arc = [source, target]; // Remember original unswapped state

	if (source.id < target.id) {
	    // Use the same link for all added links between
	    // nodes. Always use same direction such that source id
	    // is always the larger one, and when not, swap the
	    // parameters.
	    label = {start: label.end,
		     middle: label.middle,
		     arrow: label.arrow,
		     end: label.start};

	    var tmp = source;
	    source = target;
	    target = tmp;

	    if (marker == MARKER.START)
		marker = MARKER.END;
	    else if (marker == MARKER.END)
		marker = MARKER.START;
	}

	if (label.arrow) {
	    if (marker & MARKER.END) {
		var above_arrow = label.arrow;
	    } else if (marker & MARKER.START) {
		var below_arrow = label.arrow;
	    }
	}


	var id = source.id + '-' + target.id + '-' + type;
	var lnk = linkmap[id];
	if (!lnk) {
	    // A new link not seen before
	    lnk = {
		source: source,
		target: target,
		style: style,
		marker: marker,
		labels: {},
		id: id,
		type: type,
		sequence: update_sequence
	    };
	    linkmap[id] = lnk;
	} else if (lnk.sequence != update_sequence) {
	    // After each update, the labels and markers are reset and
	    // must be refreshed.
	    lnk.sequence = update_sequence;
	    lnk.labels = {};
	    lnk.marker = MARKER.NONE;
	}

	lnk.style = style;
	lnk.marker |= marker;
	
	lnk.labels.start = add_unique_labels(lnk.labels.start, label.start);
	lnk.labels.middle = add_unique_labels(lnk.labels.middle, label.middle);
	lnk.labels.above = add_unique_labels(lnk.labels.above, above_arrow);
	lnk.labels.below = add_unique_labels(lnk.labels.below, below_arrow);
	lnk.labels.end = add_unique_labels(lnk.labels.end, label.end);
	arc.push(lnk);
	return arc;
    }
    
    function add_relation(source, target, type, label, style, marker) {
	// For now, relation is just a link
	return add_link(source, target, type, label, style, marker);
    }
    
    function node_click(d) {
	d3.event.preventDefault();
    	d3.event.stopPropagation();
	if (CALLBACKS.nodeSelect)
	    (CALLBACKS.nodeSelect)(d, this);
    }
    
    function node_context(d) {
    	d3.event.preventDefault();
    	d3.event.stopPropagation();
    	if (d.node) {
	    if (CALLBACKS.portContext)
    		(CALLBACKS.portContext)(d, this);
	} else {
	    if (CALLBACKS.nodeContext)
    		(CALLBACKS.nodeContext)(d, this);
	}
    }

    function label_attr(label, type) {
	label
	    .attr("x", 0)
	    .attr("dy", "1em")
	    .text(function(t) {return t;});
    }

    function label_create(parent, type) {
	parent.each(function (d) {
	    var label = d3.select(this).selectAll("." + type);
	    if (!d.labels[type] || d.labels[type].length == 0) {
		label.remove();
		return;
	    }
	    if (label.empty()) {
		label = d3.select(this)
		    .append("text")
		    .attr("class", type);
	    }
	    label = label.selectAll("tspan")
		.data(function (d) {return d.labels[type];})
		.call(label_attr);
	    label.enter()
		.append("tspan")
		.call(label_attr);
	    label.exit().remove();
	});
    }

    function arrow_create(parent, type) {
	var param;
	if (type == "above")
	    param = ["left", "right"];
	else
	    param = ["right", "left"];
	parent.each(function (d) {
	    var arrow = d3.select(this).selectAll('.' + type);
	    if (!d.labels[type] || d.labels[type].length == 0) {
		arrow.remove();
		return;
	    }
	    if (arrow.empty()) {
		arrow = d3.select(this)
		    .append("text")
		    .attr("class", type);
		arrow.append("tspan")
		    .attr("class", param[0])
		    .text("\u2190");
		arrow.append("tspan")
		    .attr("class", "labels");
		arrow.append("tspan")
		    .attr("class", param[1])
		    .text("\u2192");
	    }
	    var label = arrow.selectAll(".labels")
		    .selectAll("tspan")
		    .data(function(d) { return d.labels[type];});
	    label.text(function (d) { return d;});
	    label.enter()
		.append("tspan")
		.text(function (d) { return d;});
	    label.exit().remove();
	});
    }

    function get_marker_url(d, line) {
	var id = 'triangle-' + d.type;
	var classes = d.type;
	if (d.style) {
	    id += "-" + d.style;
	    classes += " " + d.style;
	}
	
	var style = window.getComputedStyle(line, null);

	// Intentionally ignore the possible "px" ending...
	d.stroke_width = parseInt(style.getPropertyValue("stroke-width"), 10);
	
	if (defs.select('#'+id).empty()) {
	    // Create a new arrow marker
	    defs.append("marker")
		.attr("id", id)
		.attr("class", classes)
		.attr("viewBox", "0 0 10 10")
		.attr("refX", 7) // REVISIT: "ad hock value"
		.attr("refY", 5)
		.attr("orient", "auto-start-reverse")
	    // Currenlty, markers don't inherit style from line, make
	    // a half-hearted effort and set stroke and fill from the
	    // line
		.style("stroke", style.getPropertyValue("stroke"))
		.style("fill", style.getPropertyValue("stroke"))
		.append("use")
		.attr("xlink:href", "#marker-triangle");
	}
	return "url(#" + id + ")";
    }

    function link_update(link) {
	link.attr("class", function (d) { return "link " + d.type + (d.style ? " " + d.style: "");});
	link.select("line")
	    .attr("marker-end", function(d) {
		if (d.marker & MARKER.END)
		    return get_marker_url(d, this);
		return undefined;
	    })
	    .attr("marker-start", function(d) {
		if (d.marker & MARKER.START)
		    return get_marker_url(d, this);
		return undefined;
	    });
	link.call(label_create, "middle");
	link.selectAll(".translated")
	    .call(label_create, "start")
	    .call(label_create, "end")
	    .call(arrow_create, "above")
	    .call(arrow_create, "below");
    }

    function link_create(link) {
	link.append("g")
	    .attr("class", "translated")
	    .each(function (d) {
		if (d.source.node === d.target || d.source === d.target.node) {
		    // This link is between the node and it's port
		    //d3.select(this).append("path");
		    d3.select(this).append("line");
		} else {
		    // Normal link
		    d3.select(this).append("line");
		}
	    });
	if (LINK.create)
	    (LINK.create)(link);
    }
    
    function node_icon(d) {
	if (d.info && d.info.icon) {
	    return 'images/' + d.info.icon +  '.svg';
	}
	return undefined;
    }
    
    function node_label(d) {
	return d.name === undefined ? d.id : d.name;
    }

    function node_vendor(d) {
	return (d.info && d.info.vendor) ? d.info.vendor : "";
    }

    function node_update(node) {
	var nodes = node.filter(function (d) {return !d.node;});
	var internal = nodes.selectAll(".graph");
	internal.selectAll(".vendor")
	    .text(node_vendor);
	internal.selectAll(".label")
	    .text(node_label);
	internal.selectAll(".icon")
	    .attr("xlink:href", node_icon);
	if (NODE.update)
	    (NODE.update)(nodes);
    }

    function node_create(node) {
	// Create nodes group
	var nodes = node.filter(function (d) {return !d.node;});
	var internal = nodes.append('g')
		.attr("class", "graph");
	internal.each(function (d) {
	    var icon = node_icon(d);
	    if (icon) {
		d3.select(this).append("image")
		    .attr("class", "icon")
		    .attr("transform", NODE.translate(0,0))
		    .attr("width", NODE.S)
		    .attr("height", NODE.S)
		    .attr("xlink:href", icon);
	    }
	});
	internal.append("text")
	    .attr("class", "vendor")
	    .attr("dy", -NODE.S/2)
	    .text(node_vendor);
	// for nodes, put label below image
	internal.append("text")
	    .attr("class", "label")
	    .attr("dy", NODE.S/2+10) // REVISIT: "+10" s.b. 1em?
	    .text(node_label);
	if (NODE.create)
	    (NODE.create)(nodes);

	var ports = node.filter(function (d) {return !!d.node;});
	internal = ports
	    .append('g')
	    .attr("class", "graph");
	internal.each(function (d) {
	    var icon = node_icon(d);
	    if (icon) {
		d3.select(this).append("image")
		    .attr("class", "icon")
		    .attr("transform", PORT.translate(0,0))
		    .attr("width", PORT.S)
		    .attr("height", PORT.S)
		    .attr("xlink:href", node_icon);
	    }
	});
	// for ports, put label in center
	internal.append("circle")
	    .attr("r", PORT.R);
	internal.append("text")
	    .attr("class", "label")
	    .attr("dy", "0.5em") // REVISIT: "+10" s.b. 1em?
	    .text(node_label);
	if (PORT.create)
	    (PORT.create)(ports);
    }

    function hex_string(s, start, length) {
	var h = '';
	var end = start + length;
	for (var j = start; j < end; ++j) {
	    h += ("00" + s.charCodeAt(j).toString(16)).slice(-2);
	}
	return h;
    }

    function update() {
	if (update_active) {
	    update_request++;
	    return;
	}
	if (update_request == 0) {
	    update_request++;
	    setTimeout(do_update, 10);
	    return;
	}
    }

    function do_update() {
	// Rebuild nodes
	update_sequence += 1;
	update_active = true;
	update_request = 0;

	force.stop();

	links.splice(0, links.length);
	nodes.splice(0, nodes.length);
	// clusters.splice(0, clusters.length);

	var id;

	// Collect active nodes
	for (id in nodemap) {
	    var fn = nodemap[id];
	    if (fn.show || fn.sequence > display_sequence) {
		if (fn.node) {
		    // A port node
		    fn.neighbors = [];
		} else {
		    var cluster = fn.cluster || 0;
		    if (fn.fixed || !clusters[cluster])
			clusters[cluster] = fn;
		}
		nodes.push(fn);
	    }
	}

	// Collect active links
	for (id in linkmap) {
	    var lnk = linkmap[id];
	    if (lnk.show || lnk.sequence > display_sequence) {
		// Add link only if both source and target is visible
		if (lnk.target.sequence > display_sequence && lnk.source.sequence > display_sequence) {
		    // The "tick()" needs a quick access to neighbors of
		    // the port nodes -- maintain neighbor lists for
		    // ports (at this point normal nodes do not need this
		    // tracking).
		    if (lnk.target.node) lnk.target.neighbors.push(lnk.source);
		    if (lnk.source.node) lnk.source.neighbors.push(lnk.target);
		    links.push(lnk);
		}
	    }
	}
	    
	node = svg_nodes.selectAll(".node").data(nodes, function (d) { return d.id; });
	node.call(node_update);
	node.exit().remove();
	
	var nodeenter = node.enter()
		.append("g")
	//.attr("title", function(d) { return d.id;})
		.attr("class", function (d) {
		    return (d.info && d.info.class) ? "node " + d.info.class : "node";
		})
		.on("click", node_click)
		.on("contextmenu", node_context)
		.call(node_create)
	// .call(node_update)
		.call(drag);

	link = svg_links.selectAll(".link")
	    .data(links, function (d) { return d.id; })
	    .call(link_update);
	var linkenter = link.enter().append("g");
	linkenter.call(link_create);
	// linkenter
	//     .append("g")
	//     .attr("class", "translated")
	//     .append("line");
	linkenter.call(link_update);
	link.exit().remove();

	update_active = false;

	if (D3_IS_V3) {
	    force
		.nodes(nodes)
		.links(links)
		.size([width, height])
	    // REVISIT: setting charge 0 for ports seems to stabilize
	    // initial graph, need to add some intelligent collision
	    // detection for ports.
	    //.gravity(function (d) { return d.node ? 0.4 : 0.4;})
		.charge(function (d) { return d.node ? 0 : -2000;})
		.start();
	} else {
	    node = nodeenter.merge(node);
	    link = linkenter.merge(link);
	    force.nodes(nodes)
		.force("link").links(links);
	    force.restart().alpha(1);
	}
    }

    function offsetHeight(e) {
	// ..firefox doesn't seem to have offsetHeight property
	// defined at this point -- this avoids NaN error.
	return e.offsetHeight ? e.offsetHeight : 0;
    }
    
    function tick() {
	if (update_active) {
	    console.log("tick called while in do_update");
	    return;
	}

	// var k = e.alpha;

	nodes.forEach(function (d) {
	    if (!d.node) {
		return;
	    }

	    if (d.dragged) {
		d.cx = d.x - d.node.x;
		d.cy = d.y - d.node.y;
	    } else if (!d.fixed) {
		var dx, dy;
		// This should be the same as d.weight!!!
		var weight = d.neighbors.length;
		if (weight > 0) {
		    // When port is connected to other nodes, aim the
		    // port to average position of all connected
		    // nodes.
		    dx = dy = 0;
		    for (var i = 0; i < weight; ++i) {
			dx += d.neighbors[i].x || 0;
			dy += d.neighbors[i].y || 0;
		    }
		    dx /= weight;
		    dy /= weight;
		} else {
		    dx = d.x;
		    dy = d.y;
		}
		var radius = d.radius;
		if (!d.node.ports) console.log("No ports!", d.node, d);
		if (d.node.ports.length > 8) {
		    var limit = PORT.R / Math.sin(Math.PI / d.node.ports.length);
		    // console.log("adjust " + radius + " -> " + limit);
		    if (radius < limit) {
			radius = limit;
		    }
		}
		dx -= d.node.x;
		dy -= d.node.y;
		var r = Math.sqrt(dx*dx + dy*dy);
		var cx = dx * radius / r;
		var cy = dy * radius / r;

		d.cx += (cx - d.cx);
		d.cy += (cy - d.cy);
	    }
	    d.x = /*d.px =*/ d.node.x + d.cx;
	    d.y = /*d.py =*/ d.node.y + d.cy;
	    console.assert(!(isNaN(d.x) || isNaN(d.y)),
			   "NaN Values from port :", d, width + "x" + height);
	});
	// Compute translation for link line group
	var translated = link.select(".translated").attr("transform", function(d) {
	    var x1 = d.source.x;
	    var y1 = d.source.y;
	    var x2 = d.target.x;
	    var y2 = d.target.y;


	    var a = x2 - x1;
	    var b = y2 - y1;
	    var c = Math.sqrt(a*a + b*b);
	    if (c == 0) return undefined;
	    var sin = b / c;
	    var cos = a / c;
	    // for "fixing" arrow head rendition (draw a shorter line)
	    // -- if the line has markers, d.stroke_width is defined
	    var end = d.stroke_width;
	    if (a > 0) {
		d.x2 = c - (+d.target.gap);
		d.x1 = +d.source.gap;
	    } else {
		cos = -cos;
		sin = -sin;
		d.x2 = -c + (+d.target.gap);
		d.x1 = -d.source.gap;
		end = -end;
	    }
	    if (d.marker & MARKER.START) d.x1 += end;
	    if (d.marker & MARKER.END) d.x2 -= end;

	    var t = "matrix("
		+ cos + ","
		+ sin + ","
		+ (-sin) + ","
		+ cos + ","
		+ x1 + ","
		+ y1 + ")";
	    console.assert(!(isNaN(+cos) || isNaN(+sin) || isNaN(+x1) || isNaN(+y1)),
			   "NaN Values from:", d, width + "x" + height);
	    return t;
	});

	link.select(".middle")
	    .attr("transform", function(d) {
		return "translate(" +
		    ((d.source.x + d.target.x) / 2) + "," + 
		    ((d.source.y + d.target.y) / 2) + ")";
	    });
	translated.select("line")
	    .attr("x1", function(d) { return d.x1; })
	    .attr("x2", function(d) { return d.x2; });
	    
	translated.selectAll(".start")
	    .attr("transform", function(d) { return "translate(" + d.x1 + "," + (-offsetHeight(this)/2)+ ")";})
	    .style("text-anchor", function(d) { return d.x2 < 0 ? "end" : "start";});
	translated.selectAll(".end")
	    .attr("transform", function(d) { return "translate(" + d.x2 + "," + (-offsetHeight(this)/2) + ")";})
	    .style("text-anchor", function(d) { return d.x2 < 0 ? "start" : "end";});
	translated.selectAll(".below")
	    .attr("transform", function(d) {
		return "translate(" + ((d.x1 + d.x2) / 2) + ",-3)";
	    });
	translated.selectAll(".above")
	    .attr("transform", function(d) {
		return "translate(" + ((d.x1 + d.x2) / 2) + ",+9)";
	    });
	translated.selectAll(".right")
	    .attr("visibility", function (d) { return d.x2 < 0 ? "hidden" : "visible";});
	translated.selectAll(".left")
	    .attr("visibility", function (d) { return d.x2 < 0 ? "visible" : "hidden";});

	node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")";});
    }

    function add_node(id, name, info) {
	var fn = nodemap[id];
	if (!fn) {
	    fn = {id: id };
	    fn.x = width / 2;
	    fn.y = height / 2;
	    nodemap[id] = fn;
	}
	if (name !== undefined) fn.name = name;
	fn.gap = NODE.R;
	fn.sequence = update_sequence;
	if (info !== undefined) {
	    fn.info = info;
	    fn.show = info.show;
	}
	return fn;
    }

    function port_node(node, port, radius, info) {
	var port_id = node.id + "_" + port;
	port = add_node(port_id, port, info);
	if (!port.node) {
	    // Introducing a new port. Because port id is generated
	    // from unique node id, port can only be attached to one
	    // node (it never moves from a node to another). Thus if
	    // port is already attached to node, then the port also
	    // must be already registered in the ports list.
	    port.node = node;
	    port.cx = 0;
	    port.cy = 0;
	    // Record the port on ports list.
	    if (node.ports)
		node.ports.push(port);
	    else
		node.ports = [port];
	}
	port.radius = radius || PORT.distance || NODE.R + PORT.R;
	port.gap = PORT.R;
	// Always add a link between port and node
	//var arc = add_link(port.node, port, 'port', {}, undefined, MARKER.NONE);
	//arc[2].show = true;
	return port;
    }

    function host_node(id, name, info) {
	if (id in NAME_MAP) id = NAME_MAP[id];
	return add_node(id, name, info);
    }

    // Internal function to remove node and attached ports (no links cleanup)
    function delete_node(id) {
	var node = nodemap[id];
	if (!node) return;
	node.id = undefined;
	delete nodemap[id];
	if (node.ports) {
	    for (var i = 0; i < node.ports.length; ++i) {
		var port = node.ports[i];
		if (port.node !== node) alert("Bad node/port", node, port);
		port.node = undefined;
		delete_node(port.id);
		port.id = undefined; // just in case it wasn't in nodemap!
	    }
	    node.ports = undefined;
	}
    }
    function remove_node(id) {
	// First, delete node and all attached ports.

	// If node is a port, remove the reference to port from the
	// ports of the attached node.
	var port = nodemap[id];
	if (port && port.node) {
	    var i = port.node.ports.indexOf(port);
	    if (i > -1) {
		port.node.ports.splice(i,1);
	    }
	}

	delete_node (id);
	
	// Clean up all links pointing to deleted nodes and ports
	for (id in linkmap) {
	    var lnk = linkmap[id];
	    if (lnk.source.id == undefined || lnk.target.id == undefined) {
		delete linkmap[id];
	    }
	}
    }
    
    function freezeAllNodes(elem, params) {
	var freeze = (params.value == 'Freeze');
	for (var name in nodemap) {
	    var node = nodemap[name];
	    if (node.node) continue; // Ignore ports...
	    node.fixed = freeze;
	    if (freeze) {
		node.fx = node.x;
		node.fy = node.y;
	    } else {
		node.fx = undefined;
		node.fy = undefined;
	    }
	}
	update();
    }

    function link_visibility(type, node, sequence) {
	var count = 0;
	for (var id in linkmap) {
	    var lnk = linkmap[id];
	    if (type && lnk.type != type)
		continue;
	    if (node && 
		lnk.source !== node &&
		lnk.target !== node &&
		lnk.source.node !== node &&
		lnk.target.node !== node)
		// The node does not match source or target node or port.
		continue;
	    if (sequence != -1) {
		// If link source or target is hidden, do not
		// enable the link either.
		if (lnk.source.sequence == -1 || lnk.target.sequence == -1)
		    continue;
	    }
	    // Hide/Show this link
	    lnk.sequence = sequence;
	    count += 1;
	}
	return count;
    }

    // Simple shallow "merge" for an object to fill in missing
    // attributes from another object...
    function fill_defaults(obj, defaults) {
	for (var attr in defaults) {
	    if (!(attr in obj)) obj[attr] = defaults[attr];
	}
    }

    fill_defaults(view, VIEW);
    reset_size();

    // Get the intial default view
    return {
	// Return the SVG roog "g" element as d3 selection
	svg: function () {
	    return svg;
	},
	// Call when changes to nodes and links need to be displayed
	update: update,

	/**
	 * Return existing node or create a new node
	 *
	 * @param {string} id The unique node identifier
	 * @param {string} name The visible name of the node (optional, defaults to id)
	 * @param {Object.<string, string>} info Additional node styling info
	 *
	 * The following keywords, if present in info, are used:
	 * 
	 *  - icon: selects the graphical icon with name
	 *    "images/<icon>.svg"
	 *
	 *  - vendor: Shown as text above node (icon)
	 *
	 *  - class: Add this as a class to node SVG group
	 *
	 * The info is attached as is to the node. This means that if
	 * content of the info is changed, it is reflected in the
	 * display. The same info block can be used for multiple
	 * similar nodes.
	 *
	 * If info or name is undefined, the existing name or info is
	 * not modified.
	 *
	 * @example
	 * html:
	 *
	 * <g glass="node <info.class>">
	 *   <image class="icon" xref="<info.icon>">
	 *   <text class="vendor"><info.vendor></text>
	 *   <text class="label"><name parameter></text> 
	 * </g>
	 */
	node: function (id, name, info) {
	    return host_node(id, name, info);
	},

	port: function (node, id, radius, info) {
	    return port_node(node, id, radius, info);
	},

	/**
	 * Freeze node to specified location
	 *
	 * @param {Object} node The node to freeze
	 * @param {{x: number, y: number}} location The position to freeze
	 */
	freeze: function(node, location) {
	    node.fixed = true;
	    if (node.node) {
		// Port node (x,y) is relative to the node center
		node.cx = location.x;
		node.cy = location.y;
	    } else {
		if (D3_IS_V3) {
		    node.px = node.x = location.x;
		    node.py = node.y = location.y;
		} else {
		    node.fx = node.x = location.x;
		    node.fy = node.y = location.y;
		}
	    }
	},
	// Hide the node -- it becomes visible again, if it is
	// referenced by any existing links.
	hide: function(node) {
	    node.sequence = -1;
	},
	// Hide/Show links of specific type (optinally limit to specic node)
	hidelinks: function (type, node) { return link_visibility(type, node, -1);},
	showlinks: function (type, node) { return link_visibility(type, node, update_sequence);},

	/**
	 * Make node visible
	 *
	 * @param {boolean} permanet Make node permanently visible, if
	 * true. Otherwise, visibility is controlled by sequence.
	 */
	show: function (node, permanent) {
	    if (permanent) {
		node.show = true;
	    } else {
		node.show = false;
		node.sequence = update_sequence;
	    }
	},
	/**
	 * Remove node permanently
	 *
	 * @param {string} id The unique id of the node to remove
	 *
	 * Does nothing if there no node with that id. This also
	 * removes all associated port nodes if any.
	 */
	remove: remove_node,

	/**
	 * Find node (or port) by id
	 *
	 * @param {string} id The unique id of the node to find
	 * @param {string} port The port id relative to node (optional)
	 *
	 * Returns undefined, if node does not exist
	 */
	find: function (id, port) {
	    if (port) id = id + "_" + port;
	    return nodemap[id];
	},

	/**
	 * Add a relation (link) between source and target
	 * @param {Object} source The source node of the relation (link)
	 * @param {Object} target The target node of the relation (link)
	 * @param {string} type The type of the relation
	 * @param {Object.<string, string>} label The labels to add on the link
	 * @param {string} style The style of the relation (optional)
	 * @param {number} marker The marker to use, a bitmask of MARKER.START, MARKER.END or MARKER.NONE
	 *
	 * Each relation creates a SVG group (g) element with classes
	 * 'link', type and style (if given). Inside this group the
	 * 'line' element draws the actual line. If the relation uses
	 * marker, then an additional marker element is created with
	 * with class type and style.
	 *
	 * The application style sheet controls the final style of
	 * generated line.
	 *
	 * The keywords in label have the following interpreation:
	 *
	 * - source, target: The link originates and/or terminates in
	 *   a special "port" node identified by the string value of
	 *   the keyword.
	 *
	 * - arrow: Is a special label placed in middle of the line.
	 *   The label includes an arrow symbol and provided
	 *   text. These generate text elements with class "above" and
	 *   "below".
	 *
	 * - middle: The label text is placed in middle of the line
	 *
	 * - end: The label text is placed at end of line (target)
	 *
	 * - start: The label text is placed at start of the line
         *   (source)
	 *
	 * @example
	 * css:
	 *
	 * .link.<type>.<style> {
	 *      stroke: green;
	 *      fill: green;
	 * }
	 *
	 * html:
	 *
	 * <marker class="<type> <style>" ...> ... </marker>
	 *
	 * <g class="link <type> <style>">
	 *    <g>
	 *       <line ... > </line>
	 *       <text class="below" ...> ... </text>
	 *       <text class="above" ...> ... </text>
	 *    </g>
	 * </g>
	 */
	relation: function(source, target, type, label, style, marker) {
	    return add_relation(source, target, type, label, style, marker);
	},

	// Make changes visible
	udpate: update,
	
	// Stop force
	stop: function () { force.stop(); },

	// Add background image
	background: function(path, width, height) {
	    svg_background.text('');
	    if (path) {
		svg_background.append('image')
		    .attr("xlink:href", path)
		    .attr("height", height)
		    .attr("width", width);
	    }
	},

	// Call when the size of the drawing area has potentially changed
	resize: function () {
	    if (!resize_pending) {
		resize_pending = true;
		setTimeout(reset_size, 100);
	    }
	},

	// Set global NODE paramareters
	nodeSize: function (N, S, R) {
	    if (R === undefined)
		// Default radius is circle around the square (S x S)
		R = S* Math.sqrt(2) / 2;
	    N.S = S;
	    N.R = R;
	},
	
	// Hide all nodes and links. If graph.update() is called after
	// this, no nodes or links are drawn. Links and nodes will be
	// visible if graph.node() or graph.relation() has been used
	// to reactivate them.
	hideAll: function () {
	    display_sequence = update_sequence;
	    update_sequence += 1;
	},
	// Remove all link information
	removeLinks: function () {
	    linkmap = {};
	},
	/**
	 * Return a saveset
	 *
	 * Return JSON serializable information about nodes that have
	 * manual overrides, which should be preserved when state is
	 * saved. (currently only positions of fixed nodes in graph).
	 */
	saveset: function () {
	    var set = [];
	    for (var i = 0; i < nodes.length; ++i) {
		var node = nodes[i];
		if (!node.fixed) continue;
		var info = {id: node.id, x: node.x, y: node.y};
		if (node.node) {
		    info.port = [node.cx, node.cy];
		}
		set.push(info);
	    }
	    return set;
	},

	/**
	 * Restore node parameters from the saveset
	 *
	 * @param {Object} saveset The saveset
	 * 
	 * Fix positions of graph nodes from a saveset generated by
	 * the saveset() function.
	 */
	restore: function(saveset) {
	    if (!saveset) return;

	    for (var i = 0; i < saveset.length; ++i) {
		var info = saveset[i];
		var node = nodemap[info.id];
		if (!node)
		    node = {id: info.id};
		nodemap[info.id] = node;
		node.fixed = true;
		if (D3_IS_V3) {
		    node.px = node.x = info.x;
		    node.py = node.y = info.y;
		} else {
		    node.fx = node.x = info.x;
		    node.fy = node.y = info.y;
		}
		if (info.port) {
		    node.cx = info.port[0];
		    node.cy = info.port[1];
		}
	    }
	},

	/**
	 * Freeze or unfreeze all nodes
	 *
	 * @param {Object} elem DOM element
	 * @param {{value: 'Freeze'} params
	 *
	 * The parameters are such that this can bound to GUI click or
	 * other event.
	 *
	 * If params.value == 'Freeze', then freeze all nodes at their
	 * current position.
	 *
	 * If params.value != 'Freeze', then unfreeze all nodes.
	 */
	freezeAllNodes: freezeAllNodes,

	MARKER: MARKER,
	NODE: NODE,
	PORT: PORT,
	LINK: LINK
    };
}
