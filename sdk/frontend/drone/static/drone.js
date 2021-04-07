var drone = (function () {
    
    var max_lines = 500;
    var local_url = (location.protocol == 'https' ? 'wss://' : 'ws://') + location.host + "/drone";

    function Drone(url) {
	this.tasks = {};
	this.url = url;
	this.ws = undefined;
	this.open = false;
    }

    Drone.prototype.connect = function() {
	if (this.ws) this.ws.close();
	this.ws = new WebSocket(this.url);
	this.open = false;
	var drone = this;
	
	this.ws.onopen = function(evt) {
	    console.log("Web Socket open");
	    drone.open = true;
	    for (var key in drone.tasks) {
		var task = drone.tasks[key];
		if (task.drone === drone && task.task.autostart)
		    drone.tasks[key].start();
	    }
	};
	
	this.ws.onclose = function () {
	    drone.ws = undefined;
	    drone.open = false;
	    console.log("Web Socket connection lost");
	    for (var key in drone.tasks) {
		drone.tasks[key].closed();
	    }
	};
	this.ws.onerror = function (evt) {
	    console.log(evt);
	};
	
	this.ws.onmessage = function (evt) {
	    var msg = JSON.parse(evt.data);
	    if (drone.tasks[msg.id]) {
		drone.tasks[msg.id].message(msg);
	    } else {
		console.log("Ignoring message for unregistered task: ", msg);
	    }
	};
    };
    
    Drone.prototype.register = function (id, task) {
	this.tasks[id] = task;
	if (this.open && task.drone === this && task.task.autostart) {
	    task.start();
	} else if (!this.ws) {
	    this.connect();
	}
    };

    Drone.prototype.send = function(msg, task) {
	if (this.ws && this.open) {
	    this.ws.send(JSON.stringify(msg));
	} else if (this.ws && this.ws.readyState == WebSocket.CONNECTING) {
	    task.message({error: "Websocket not ready -- still connecting", status: 'error'});
	    this.ws.close(undefined, "closed due stalled connect");
	} else {
	    if (this.ws) this.ws.close(); // just in case.
	    task.message({error: "Websocket not open - trying reconnect", status: 'error'});
	    this.connect();
	}
    };

    function Console(selector) {
	var area = d3.select(selector)
		.text('');
	this.console = area.node();
	this.bottom = true;
	area.append('p');
    }

    Console.prototype.output = function(bytes) {
	bytes = bytes.replace(/ /g, '\xa0');
	this.bottom = this.console.scrollHeight - this.console.clientHeight <= this.console.scrollTop + 5;
	var lines = bytes.split("\n");

	var overflow = this.console.childNodes.length + lines.length - max_lines;
	if (overflow > 0) {
	    var range = document.createRange();
	    range.setStart(this.console, 0);
	    if (lines.length >= max_lines) {
		range.setEnd(this.console, this.console.childNodes.length-1);
	    } else {
		range.setEnd(this.console, overflow-1);
	    }
	    range.deleteContents();
	}
	var log = this.console.lastElementChild;
	log.textContent += lines[0];
	for (var i = 1; i < lines.length; ++i) {
	    log = document.createElement("p");
	    log.appendChild(document.createTextNode(lines[i]));
	    this.console.appendChild(log);
	}
	if (this.bottom)
	    this.console.scrollTop = this.console.scrollHeight - this.console.clientHeight;
    };
    Console.prototype.clear = function () {
	this.bottom = true;
	d3.select(this.console).text('').append('p');
    };
    Console.prototype.open = function () {
	if (this.bottom)
	    this.console.scrollTop = this.console.scrollHeight - this.console.clientHeight;
    };

    
    var DRONES = {
    };

    function Task(task, parent) {
	this.task = task;
	this.children = [];
	this.parent = parent;
	if (parent)
	    parent.children.push(this);
    }

    Task.prototype.message = function (msg) {
	if (msg.log) {
	    this.console.output(msg.log);
	}
	this.callback(this, msg);
    };

    Task.prototype.start = function() {
	d3.select(this.element).select(".error").text("");
	this.drone.send({request: 'start',
			 id: this.task.id,
			 cwd: this.task.cwd,
			 user: this.task.user,
			 command: this.task.command
			}, this);
    };

    
    Task.prototype.closed = function() {
	this.callback(this, {error: "Lost Connection", status: 'error'});
    };

    Task.prototype.stop = function() {
	d3.select(this.element).select(".error").text("");
	this.drone.send({request: 'stop', id: this.task.id}, this);
    };
	
    Task.prototype.clear = function() {
	d3.select(this.element).select(".error").text("");
	this.console.clear();
    };

    Task.prototype.open = function() {
	// Called when the task information becomes visible or is reselected
	this.console.open();
    };
    
    Task.prototype.keypress = function() {
    	var event = d3.event;
    	console.log("keypress: which=" + event.which +
    		    " keyCode=" + event.keyCode +
    		    " key= " + event.key +
    		    " charCode=" + event.charCode +
    		    " char= " + event.char +
    		    " ctrlKey= " + event.ctrlKey +
    		    " shiftKey= " + event.shiftKey
    		   );
    	event.preventDefault();
    	var char = event.keyCode || event.which;
    	if (event.ctrlKey) char &= 0x1f;
    	this.drone.send({request: "input",
    			 id: this.task.id,
    			 input: String.fromCharCode(char)
    			}, this);
    };

    Task.prototype.init = function (element, callback) {
	this.element = element;
	this.callback = callback;
	this.console = new Console(d3.select(this.element).select('.log').node());

	var url;
	var p = this;
	do {
	    p = p.parent;
	    url = p ? p.task.drone : local_url;
	} while (!url);

	this.drone = DRONES[url];
	if (!this.drone) {
	    DRONES[url] = this.drone = new Drone(url);
	}
	this.drone.register(this.task.id, this);
    };

    function drone_Task(task, parent) {
	return new Task(task, parent);
    }
    
    return drone_Task;
})();
