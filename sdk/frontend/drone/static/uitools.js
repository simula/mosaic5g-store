/**
 * Provide UI components for D3 (v3/v4) web applications
 *
 *
 * Click Action - activate action
 *
 *    If a "click action" is associated with an element, then on click
 *    search the element and parents until either 'data-action',
 *    'data-popup' or 'data-submit' within FORM is found.
 *
 *    The value of the 'data-action' or 'data-submit' must be defined
 *    in the 'callbacks' dictionary with function value. This function
 *    is executed on click. If both are while looking up, then the
 *    first found will be used. Defining both on same element is an
 *    error.
 *
 *    The 'data-action' callback triggers when the value is found. The
 *    'data-submit' continues the search to find the FORM parent
 *    element, and when found adds the form values into
 *    params.form_data, then calls the data-submit action.
 *
 *    The value of the 'data-popup' must be an id of an (.popup)
 *    element in the document. This element is assumed to describe a
 *    popup panel, which is displayed.
 *
 *    The click action is implicit on popup menu items. For explicit
 *    definion for other elements, add the class "click-action" to the
 *    element class list.
 *
 *    ... <span class="click-action">Click me</span> ...
 *
 * Popup menu - popup up a menu list, when mouse is over the element.
 *
 *    .popup-menu-open -- identify the popup menu element
 *
 *    *.popup-menu-open > ul.popup-menu -- identify the list of menu
 *    items to popup. This element is hidden until parent is hovered
 *    over.
 *
 *    <div class="popup-menu-open">
 *       .. visible content to hover over ..
 *       <ul class="popup-menu">
 *          <li> item 1 </li>
 *          <li> item 2 </li>
 *       </ul>
 *   </div>
 *
 *   Each list item in static popup-menu is automatically attached to
 *   on click event. However, for a dynamically generated menu list,
 *   the click action must be activated by the javascript code (in
 *   D3JS selection, you can use ".call(uitools.add_click_action)".
 *
 *   The same popup menu list can be shared with multiple elements, if
 *   the ".popup-menu-open" has attribute 'data-popup-menu="menuid"',
 *   where the "menuid" is the id of a shared "ul.popup-menu"
 *   instance. When .popup-menu-open element is hovered, the shared
 *   menu list is moved under the hovered element.
 *
 *   There can be only one popup-menu as a immeadiate child of
 *   ".popup-menu-open". If there are multiple, they are rendered over
 *   each other.
 *
 *   However, the menu item (li) or some element inside it can be
 *   another popup menu construct, which opens up, when mouse hovers
 *   over that menu item.
 *
 * Tooltips
 *
 *   Tooltip text popups up when the parent element is hovered over.
 *
 *   Currently, only supported placement is to the left side of the
 *   parent element. Because tooltip is placed outside the parent, you
 *   cannot have any pointer activated content in tooltip -- it will
 *   disappear before pointer gets over the tooltip.
 *
 *   The parent element must have relative positioning for the
 *   tooltips to work [REVISIT THIS]
 *
 *      ....parent content...
 *      <div class="tooltip">
 *         ...tooltip content...
 *      </div>
 *      ... parent content...
 *
 *   The "div" as tooltip in above is just an example, any element
 *   type will do.
 *
 * Popup windows (panels)
 *
 *   A popup window is opened by an click action that finds
 *   "data-popup" attribute. The value of the attribute must be an id
 *   of a ".popup" class element (usually form or div). Such elements
 *   are not displayed until activated.
 *
 *      <form class="popup" id="popup-name" title="The Popup Title" data-submit="submit-action">
 *          ... popup content ...
 *      </form>
 *
 *   The startup code rewrites each ".popup" class element into
 *
 *      <form class="popup" id="popup-name" data-submit="submit-action">
 *        ... resize handles for sides and corners
 *        <div class="handle .."></div>
 *        ...
 *        <div class="popup-wrapper">
 *           <div class="drag popup-header">
 *              Title Popup Title
 *              <span class="cancel"></span>
 *           </div>
 *           <div class="popup-content">
 *               ...popup content....
 *           </div>
 *        </div>
 *      </form>
 *
 * *NOTE*
 *      d3.select(elem).attr("data-XXXX") === elem.dataset["XXXX"]
 */

var uitools = (function () {

    var D3_IS_V3 = d3.version.startsWith("3.");
    var DRAG = D3_IS_V3 ? d3.behavior.drag : d3.drag;
    var DRAG_START = D3_IS_V3 ? "dragstart" : "start";

    var call_backs = {};

    // The popup_stack records stack of open popups, for each a pair
    // [<id-of-popup>,<origin-element>].
    var popup_stack = [];

    function call(callback, elem, params) {
	var close = false;
	if (d3.event && d3.event.stopPropagation)
	    d3.event.stopPropagation();
	if (!callback) {
	    alert("No action defined");
	    return close;
	}
	var calls = callback.split(" ");
	for (var i = 0; i < calls.length; ++i) {
	    if (calls[i] in call_backs) {
		close |= call_backs[calls[i]](elem, params);
		// if (call_backs[calls[i]](elem, params))
		//     close_popup();
	    } else {
		alert("Unknown callback: " + calls[i]);
	    }
	}
	return close;
    }

    // Look if specific attribute exists on some ancestor node (root
    // defined by parent_class or parent_tag).
    //
    // Returns {node: <node>, value: <value>}, if attibute exists,
    // where both node and value are defined; and undefined otherwise.
    //
    function find_attribute(node, attr, parent_class, parent_tag) {
	var value;
	while (node) {
	    value = d3.select(node).attr(attr);
	    if (value) {
		return { value: value,  node: node};
	    }
	    if (parent_tag && node.tagName == parent_tag) break;
	    if (parent_class && node.classList.contains(parent_class)) break;
	    node = node.parentNode;
	}
	return undefined;
    }

    // Check if specific popup (id) is open, return index into
    // popup_stack or -1, if not found.
    function popup_check(id) {
	for (var i = popup_stack.length; --i > 0; )
	    if (id == popup_stack[i][0]) break;
	return i;
    }
    
    // Close non-pinned popups (up to specific id, if given), if any open
    function close_popup(id) {
	while (popup_stack.length > 0) {
	    var pop = popup_stack.pop();
	    var popup = d3.select("#" + pop[0]);
	    popup.classed("open", false);
	    var closed = popup.attr("data-closed");
	    if (closed) call(closed, popup.node(), {});
	    if (pop[0] == id) break;
	}
	// last_popup = '';
    }

    // Close specific popup from which the event originates
    function cancel_popup() {
	var popup = this;
	while (popup) {
	    if (popup.classList.contains("popup")) {
		if (popup_check(popup.id) != -1) {
		    // If the cancelled popup is present in stacked
		    // popups, then close all above and including it.
		    close_popup(popup.id);
		} else {
		    // Some kind of detached popup (pinned, not
		    // recorded in stack), just close this one.
		    d3.select(popup).classed("open", false);
		    var closed = popup.dataset.closed;
		    if (closed) call(closed, popup, {});
		}
		return;
	    }
	    popup = popup.parentNode;
	}
    }

    function form_values(node, params) {
	// This assumes the node is <form>. If some other element type
	// needs to be allowed, then this "data collection" loop must
	// be rewritten (perhaps: look for input elements with class
	// "data" or something).
	var elems = node.elements;
	for (var i = 0; i < elems.length; i++) {
	    var e = elems[i];
	    if (!e.name)
		continue;
	    if (e.type == 'checkbox' && !e.checked)
		continue;
	    if (e.type == 'radio' && !e.checked)
		continue;

	    // If name includes periods, generate corresponding
	    // javascript structure into params
	    var fds = e.name.split('.');
	    var tmp = params;
	    for (;;) {
		var f = fds.shift();
		// Allow index within [], but ignore it (needed if
		// array elements contain radio button groups -- each
		// array element must then have different name).
		var farray = false;
		f = f.replace(/\[\d*\]$/, function (x) { farray = true; return '';});

		if (Array.isArray(tmp)) {
		    var last = tmp[tmp.length-1];
		    if (last[f] != null) {
			last = {};
			tmp.push(last);
		    }
		    tmp = last;
		}

		if (fds.length == 0) break;
		
		if (tmp[f] == null) {
		    tmp[f] = farray ? [{}] : {};
		}
		tmp = tmp[f];
	    }

	    var value = e.value;
	    if (e.dataset.converter) {
		// If the element has a data-converter function, then
		// the return value of that defines the value of the
		// input (called without 'params').
		value = call_backs[e.dataset.converter](e);
		// Returning undefined, the converter can indicate
		// that the value should be ignored.
		if (value === undefined) continue;
	    }
	    if (e.type == 'select-multiple') {
		// Force value always into array
		if (tmp[f] === undefined)
		    tmp[f] = [];
		else
		    tmp[f] = [tmp[f]];

		for (var o = 0; o < e.options.length; ++o) {
		    if (e.options[o].selected)
			tmp[f].push(e.options[o].value);
		}
	    } else if (tmp[f] === undefined) {
		tmp[f] = farray ? [value] : value;
	    } else if (Array.isArray(tmp[f])) {
		// Already multiple values, just add to the list
		tmp[f].push(value);
	    } else {
		// Multiple values with same name, silenlty make value
		// an array (without requiring trailing [] on field
		// name)
		tmp[f] = [tmp[f], value];
	    }
	}
    }
    
    function submit_popup() {
	d3.event.preventDefault();
	var action = null;
	var node = this;
	var elem = this;
	var params = {};
	var id;

	// Find the "popup" level
	while (node) {
	    // While going up, remember the first submit action
	    if (!action) {
		action = node.dataset.submit;
	    }
	    if (node.tagName == 'FORM') {
		form_values(node, params);
		elem = node;
	    }
	    if (node.classList.contains("popup")) {
		id = node.id;
		elem = node;
		break;
	    }
	    node = node.parentElement;
	}
	var index = popup_check(id);
	if (index != -1) {
	    // Submitting a stacked popup
	    if (!action) {
		// Action has not been defined, perform implicit
		// return value to origin.
		var origin = popup_stack[index][1];
		if (origin.dataset.converter) {
		    // If origin element defines 'data-converter',
		    // assume this function will do the necessary
		    // setting of element value. It should return
		    // 'false', if conversion fails and user can
		    // correct the input. True return closes the
		    // popup.
		    if (call_backs[origin.dataset.converter](origin, params))
			close_popup(id);
		} else {
		    // Otherwise just set the "value" of the origin
		    // element from the params.value
		    origin.value = params.value;
		    close_popup(id);
		}
	    } else if (call(action, elem, params)) {
		close_popup(id);
	    }
	} else {
	    // Submit outside stacked popups, just call the action
	    call(action, elem, params);
	}
	return false;
    }

    function keep_within_graph(rect) {
	var area = document.documentElement;
	var x = rect.x;
	var y = rect.y;
	var max_w = Math.round(area.clientWidth);
	var max_h = Math.round(area.clientHeight);
	var w = Math.max(50, Math.min(rect.w, max_w));
	var h = Math.max(50, Math.min(rect.h, max_h));

	if (x + w > area.clientLeft + area.clientWidth)
	    x = area.clientLeft + area.clientWidth - w;
	if (y + h > area.clientTop + area.clientHeight)
	    y = area.clientTop + area.clientHeight - h;
	if (x < 0) x = 0;
	if (y < 0) y = 0;
	return {x: x,
		y: y,
		h: h,
		w: w
	       };
    }

    function call_resize(node) {
	var resize = node.dataset.resize;
	if (resize) {
	    call(resize, node, {});
	}
    }

    function window_resize() {
	d3.selectAll(":not(.popup)[data-resize]").each(function () {call_resize(this);});
    }

    // function open_window(url, data) {
    // 	netscape.security.PrivilegeManager.enablePrivilege('UniversalBrowserWrite');
    // 	window.open(url,"foo","chrome,menubar=no,toolbar=no,width=auto,height=auto,location=no");
    // }

    function reset_popup(popup) {
	var rect = getPosition(popup.node());
	if (!rect.w || !rect.h) {
	    // Set position from event, if popup was not visible yet.
	    if (d3.event) {
		rect.x = d3.event.clientX;
		rect.y = d3.event.clientY;
	    }
	}
	popup.classed("open", true);
	if (popup.classed("popup-menu")) {
	    popup
		.style("left", rect.x + "px")
		.style("top", rect.y + "px");
	    return;
	}
	if (!popup.classed("fixed")) {
	    // First create the popup with maximum height and width to
	    // find out the "natural" size of the content.
	    popup
		.style("left", 0)
		.style("top", 0)
		.style("width", document.documentElement.clientWidth + "px")
		.style("height", document.documentElement.clientHeight + "px");
	}
	var wrapper = popup.select(".popup-wrapper").node();
	var content = popup.select(".popup-content").node();
	// Compute new size for the popup based on the "natural" size
	rect.w = content.offsetLeft + content.offsetWidth + wrapper.offsetLeft * 2 + 1;
	rect.h = content.offsetTop + content.offsetHeight + wrapper.offsetTop * 2;
	//rect.x = Math.max(0,(rect.x - rect.w/2));
	//rect.y = Math.max(0,(rect.y - h/2));
	rect = keep_within_graph(rect);
	popup
	    .classed("fixed", true)
	    .style("left", rect.x + "px")
	    .style("top", rect.y + "px")
	    .style("height", rect.h + "px")
	    .style("width", rect.w + "px");
    }
    
    function open_popup(action, params) {
	var origin = params.target;
	var id = undefined;
	// If event originates from a popup that is present in popup
	// stack, then close popups upto that point. Otherwise, close
	// all.
	var zindex = 0;
	for (;;) {
	    if (!origin) {
		close_popup();
		break;
	    }
	    if (origin.classList.contains('popup')) {
		var index = popup_check(origin.id);
		if (index != -1) {
		    zindex = origin.style.zIndex;
		    index += 1;
		    if (index == popup_stack.length)
			break; // -- stack not touched!
		    close_popup(popup_stack[index][0]);
		    break;
		}
		close_popup();
		break;
	    }
	    origin = origin.parentElement;
	}
	
	if (action) {
	    var popup = d3.select("#" + action);
	    if (popup.empty()) {
		alert("Target popup '" + action + "' not found");
		return;
	    }
	    // If stacking popup over another, make sure the new one
	    // has higher z-index...
	    if (zindex)
		popup.style("z-index", zindex+1);
	    // If the target popup element has 'data-prepare', execute
	    // it before the popup as preparation stage.
	    params.popup = action;
	    params.value = popup.attr("data-value");
	    var prepare = popup.attr("data-prepare");
	    if (prepare) {
		call(prepare,
		     popup.node(),
		     params);
	    }
	    reset_popup(popup);
	    if (!popup.classed("pinned")) {
		popup_stack.push([action, params.target]);
	    }

	    // Set focus to first input element (if any)
	    popup.select("input:not([type=hidden])").each(function () { this.focus();});

	    // Call resize hook if specified
	    call_resize(popup.node());
	}
    }

    function reset(id, params) {
	var target = d3.select("#" + id).node();
	if (target.classList.contains('popup')) {
	    target.classList.remove("fixed");
	    reset_popup(d3.select(target));
	    return;
	}
	call_resize(target);
    }

    function click_action() {
	var elem = d3.event.target || this;
	var params = {
	    mouse: {x: d3.event.clientX, y: d3.event.clientY},
	    target: elem,
	    datum: undefined,
	    value: undefined
	};
	d3.selectAll('.notify').text('');
	while (elem && elem.nodeType == Node.ELEMENT_NODE) {
	    if (params.datum === undefined)
		params.datum = elem.__data__;
	    if (params.value === undefined) {
		// ... must accept "" empty strings and number zero.
		params.value = elem.dataset.value;
		if (params.value == undefined) {
		    params.value = d3.select(elem).attr("value");
		    if (params.value == undefined) {
			if (elem.type != 'checkbox' || elem.checked)
			    params.value = elem.value;
		    }
		}
	    }
	    if (!action) {
		var action = elem.dataset.submit;
		if (!action) {
		    action = elem.dataset.action;
		    if (action) break;
		    var popup = elem.dataset.popup;
		    if (popup) {
			open_popup(popup, params);
			return;
		    }
		}
	    }
	    if (elem.tagName == 'FORM') {
		// FORM, fill in values
		params.form_data = {};
		form_values(elem, params.form_data);
		if (action) break;
	    }
	    // var url = d3.select(elem).attr("data-window");
	    // if (url) {
	    // 	open_window(url);
	    // }
	    elem = elem.parentNode;
	}
	call(action, elem, params);
    }

    function notify(msg, elem) {
	// If a popup is open and it has an element with class
	// "notify", then put the notification there. Otherwise, just
	// find the global notification element.
	//
	// Return false, if notify was in popup
	var note;
	for (var i = 0; i < popup_stack.length; ++i) {
	    note = d3.select('#' + popup_stack[i][0] + " .notify");
	    if (!note.empty()) {
		note.text(msg);
		return false;
	    }
	}
	if (elem) {
	    note = d3.select(elem).select(".notify");
	    if (!note.empty()) {
		note.text(msg);
		return true;
	    }
	}
	d3.select("#notify").text(msg);
	return true;
    }

    function getPosition(element) {
	var rect = element.getBoundingClientRect();
	return {x: rect.left,
		y: rect.top,
		w: rect.right - rect.left,
		h: rect.bottom - rect.top};
    }

    function context_clear() {
	close_popup();
    }

    function context_popup(action, params) {
	// This function is basically same as open_popup, except if a
	// popup is currently open, it is closed and no context popup
	// happens.
    	d3.event.preventDefault();
    	if (popup_stack.length > 0) {
    	    close_popup();
    	} else {
    	    open_popup(action, params);
    	}
    }

    function context_menu() {
    	d3.event.preventDefault();
	d3.event.stopPropagation();
	d3.selectAll('.notify').text('');
	// If there is open popup, then interpret action as close only
	if (popup_stack.length > 0) {
	    close_popup();
	    return;
	}
	var params = {
	    mouse: {x: d3.event.clientX, y: d3.event.clientY}
	};

	var target = d3.event.target;
	var elem = target;
	var action;
	while (elem) {
	    action = elem.dataset.popup;
	    if (action) break;
	    if (elem === this) return;
	    elem = elem.parentNode;
	}
	open_popup(action, params);
    }

    function context_clean() {
	close_popup();
    }

    // Should find a way not needing these "globals"
    var drag_dx;
    var drag_dy;
    var drag_dh;
    var drag_dw;
    var drag_action;
    var dragging;
    var drag_actions = {
	'top-left': function (orig, x, y) {
	    x -= drag_dx;
	    y -= drag_dy;
	    return {
		x: x,
		y: y,
		w: orig.right - x,
		h: orig.bottom - y
	    };
	},
	'top-right': function (orig, x, y) {
	    y -= drag_dy;
	    return {
		x: orig.left,
		y: y,
		w: x - orig.left + drag_dw,
		h: orig.bottom - y
	    };
	},
	'bottom-left': function (orig, x, y)  {
	    x -= drag_dx;
	    return {
		x: x,
		y: orig.top,
		w: orig.right - x,
		h: y - orig.top + drag_dh
	    };
	},
	'bottom-right': function (orig, x, y) {
	    return {
		x: orig.left,
		y: orig.top,
		w: x - orig.left + drag_dw,
		h: y - orig.top + drag_dh
	    };
	},
	'left': function (orig, x, y) {
	    x -= drag_dx;
	    return {
		x: x,
		y: orig.top,
		w: orig.right - x,
		h: orig.bottom - orig.top
	    };
	},
	'top': function (orig, x, y) {
	    y -= drag_dy;
	    return {
		x: orig.left,
		y: y,
		w: orig.right - orig.left,
		h: orig.bottom - y
	    };
	},
	'right': function (orig, x, y)  {
	    return {
		x: orig.left,
		y: orig.top,
		w: x - orig.left + drag_dw,
		h: orig.bottom - orig.top
	    };
	},
	'bottom': function (orig, x, y)  {
	    return {
		x: orig.left,
		y: orig.top,
		w: orig.right - orig.left,
		h: y - orig.top + drag_dh
	    };
	},
	'popup-header': function (orig, x, y) {
	    x -= drag_dx;
	    y -= drag_dy;
	    return {
		x: x,
		y: y,
		w: orig.right - orig.left,
		h: orig.bottom - orig.top
	    };
	}
    };
    var drag_popup = DRAG()
     	    .on(DRAG_START, function () {
		drag_action = null;
		for (var i = 0; i < d3.event.sourceEvent.target.classList.length; ++i) {
		    var act = d3.event.sourceEvent.target.classList[i];
		    if (act in drag_actions) {
			drag_action = drag_actions[act];
			break;
		    }
		}
		if (!drag_action) return;
    		d3.event.sourceEvent.stopPropagation();
		dragging = this;
		while (!dragging.classList.contains("popup")) {
		    dragging = dragging.parentNode;
		}
		var pos = getPosition(dragging);
		drag_dx = d3.event.sourceEvent.clientX - pos.x;
		drag_dy = d3.event.sourceEvent.clientY - pos.y;
		drag_dw = pos.x + pos.w - d3.event.sourceEvent.clientX;
		drag_dh = pos.y + pos.h - d3.event.sourceEvent.clientY;
    	    })
    	    .on("drag", function () {
		if (!drag_action) return;
		var x = d3.event.sourceEvent.clientX;
		var y = d3.event.sourceEvent.clientY; 
		var orig = dragging.getBoundingClientRect();
		var rect = keep_within_graph(drag_action(orig, x, y));
		d3.select(dragging)
		    .classed("fixed", true)
		    .style("left", rect.x + "px")
		    .style("top", rect.y + "px")
		    .style("width", rect.w + "px")
		    .style("height", rect.h + "px");
		// Call resize hook if specified
		call_resize(dragging);
    	    });

    // Transform popup dialogs, add event handlers and close button
    // (emulating jquery a bit)
    //
    // <.popup title=title>
    //   ..content...
    // </.popup>
    // =>
    // <.popup>
    //   <.popup-header> title </.popup-header>
    //   <.popup-content> content </.popup-content>
    //   <.popup-footer> footer </.popup-footer>
    // </.popup>

    // Move all of the html initial content under new parent
    // <div class="popup-content"> ...

    var popups = d3.selectAll(".popup[title]");
    popups.call(drag_popup);
    var wrappers = popups.insert("div", ":first-child")
	.attr("class", "popup-wrapper");
    
    var content = wrappers
	    .insert("div", ":first-child")
    	    .attr("class", "popup-content")
    	    .each(function () {
    		var parent = this.parentNode.parentNode;
    		var index = 0;
    		while (parent.childNodes.length > 1) {
    		    var child = parent.childNodes[index];
    		    if (child === this.parentNode) {
    			index = 1;
    			continue;
    		    }
    		    this.appendChild(parent.childNodes[index]);
    		}
    	    });
    // Add <div class="popup-header"..> element
    wrappers.insert("div", ":first-child")
    	.attr("class", "drag popup-header")
	.call(drag_popup)
    	.text(function () {
    	    // Move title attribute from popup into header area
    	    var pop = d3.select(this.parentNode.parentNode);
    	    var title = pop.attr("title");
    	    pop.attr("title", undefined);
    	    return title;
    	})
    	.append("span")
    	.attr("class", "cancel")
    	.on("click", cancel_popup);
    content.append("input")
	.attr("type", "button")
	.attr("value", "Cancel")
	.on("click", cancel_popup);
    content.append("input")
	.attr("type", "button")
	.attr("class", "submit-action")
	.attr("value", "OK");

    // Add resize handles before (under) the wrapper so that only the
    // wrapper margins decide the shape of active area for resize
    // handles. Also, the corner handles must be after (on top of) the
    // side handles.
    popups
	.insert("div", ":first-child")
	.attr("class", "handle top-left")
	.call(drag_popup);
    popups
	.insert("div", ":first-child")
	.attr("class", "handle top-right")
	.call(drag_popup);
    popups
	.insert("div", ":first-child")
	.attr("class", "handle bottom-left")
	.call(drag_popup);
    popups
	.insert("div", ":first-child")
	.attr("class", "handle bottom-right")
	.call(drag_popup);

    popups
	.insert("div", ":first-child")
	.attr("class", "handle left")
	.call(drag_popup);
    popups
	.insert("div", ":first-child")
	.attr("class", "handle top")
	.call(drag_popup);
    popups
	.insert("div", ":first-child")
	.attr("class", "handle bottom")
	.call(drag_popup);
    popups
	.insert("div", ":first-child")
	.attr("class", "handle right")
	.call(drag_popup);

    popups
    	.on("submit", submit_popup)
	.on("contextmenu", function () {
	    d3.event.preventDefault();
	    close_popup();
	});

    // disable context menu on popup menu
    d3.selectAll(".popup-menu")
	.on("contextmenu", function () {
	    d3.event.preventDefault();
	    close_popup();
	});

    // Transform tab groups, add controls and event handlers
    //
    // Each element of class "tabs" is turned into a tab group, where
    // each child element represents a tab content.
    //
    // If the tab elemenet contains a tooltip element, it is moved
    // into tabsbar.
    //
    // <.tabs>
    //   <tab-1 data-label="tab-1-name"> ... [<tooltip> .. </tooltip>] </tab-1>
    //   <tab-2 data-label="tab-2-name"> ... [<tooltip> .. </tooltip>] </tab-2>
    // </.tabs>
    // =>
    // <.tabs>
    //   <ul .tabsbar>
    //     <li> tab-1-name [<tooltip> .. </tooltip>]</li>
    //     <li> tab-2-name [<tooltip> .. </tooltip>]</li>
    //   </ul .tabsbar>
    //   <tab-1> .. </tab-1>
    //   <tab-2> .. </tab-1>
    //
    // The .tab can define
    //
    //  'data-prepare'  - executed once every time tab is opened after being closed
    //
    //  'data-open'     - executed every time the tab selection is clicked (also on first time)
    //
    //  'data-closed    - executed when tab is closed
    //

    // Add tab selector menubar into 'tabs'
    function prepare_tabs(element) {
	var tabs = d3.select(element);

	// REVISIT: Need to allow nested tabs -- below content select
	// fails now by returning all .tab elements to any depth!!!
	// ...filter helps, but reopening outer tab should repopen previous inner tabs!
	// ...style is messed too
	var content = D3_IS_V3 ? tabs.selectAll(".tabs > .tab")[0] : 
		tabs.selectAll(".tabs > .tab").filter(function () { return this.parentNode === element;}).nodes();
	var tabsbar = tabs.insert("ul", ":first-child")
		.attr("class", "tabsbar")
		.selectAll("li")
		.data(content)
		.enter()
		.append("li")
		.on("click", tab_select)
		.each(function(d, i) {
		    // Move the tooltip into tabsbar, if defined
		    var tip = d3.select(d).select('.tab > .tooltip').node();
		    if (tip) {
			this.appendChild(tip);
		    }
		})
		.append("span")
		.text(function (d) { return d.dataset.label;});

	if (content.length > 0) {
	    // Must delay the tab_select call to happen after the ui
	    // callbacks have been set up.
	    setTimeout(function() {
		tab_select(content[0]);
	    }, 10);
	}
    };
    /**
     * Find tab bar element for the content
     */
    function tab_bar(content) {
	var tabs = content;
	while (tabs) {
	    if (tabs.classList.contains('tabs')) break;
	    tabs = tabs.parentNode;
	}
	if (!tabs) return null;
	
	// Find the corresponding tabsbar li element
	var bar = d3.select(tabs)
		.selectAll(".tabsbar > li")
		.filter(function (d) { return d == content;})
		.node();
	return bar;
    }

    /**
     * Open tab
     *
     *     * @param {object} content The ".tabs .tab" element to be opened.
     */
    function tab_select(content) {
	// Find '.tabs' parent element
	var tabs = content;
	while (tabs) {
	    if (tabs.classList.contains('tabs')) break;
	    tabs = tabs.parentNode;
	}
	if (!tabs) return; // ALERT?
	// Find the corresponding tabsbar li element
	var bar = d3.select(tabs)
		.selectAll(".tabsbar > li")
		.filter(function (d) { return d == content;})
		.node();
	if (!bar) return; // ALERT?
	if (!bar.classList.contains("selected")) {
	    // Close other tab, if open
	    // - remove "selected" state from tabsbar
	    d3.select(bar.parentNode)
		.selectAll(".selected")
		.classed("selected", false);
	    // - close the tab content
	    d3.select(tabs)
		.selectAll(".tab.open")
		.classed("open", false)
		.each(function () {
		    var action = find_attribute(this, 'data-closed', 'tabs');
		    if (action) call(action.value, this, {});
		});

	    // Execute data prepare once before new tab is selected
	    var prepare = find_attribute(content, 'data-prepare', 'tabs');
	    if (action) call(action.value, content, {});

	    // Open the new tab
	    // - open tab content
	    d3.select(content)
		.classed("open", true);
	    // - set "selected" state into tabsbar
	    d3.select(bar).classed("selected", true);
	}
	// Execute open every time tab is clicked
	var action = find_attribute(content, 'data-open', 'tabs');
	if (action) call(action.value, content, { datum: content.__data__});
    }

    d3.selectAll(".tabs").each(function () { prepare_tabs(this);});

    // Transforem pane sets, add resize controls between panes
    //
    // <.panes>
    //   <pane-1>... </pane-1>
    //   <pane-2>...</pane-2>
    //   ...
    //   <pane-N>...</pane-N>
    // </.panes>
    // =>
    // <.panes>
    //   <pane-1>...</pane-1>
    //    <.pane-resizer></.pane-resizer>
    //    <pane-2>...</pane-2>
    //    <.pane-resizer><./pane-resizer>
    //    ...
    //    <pane-N>..<pane-N>
    // </.panes>
    var drag_pane = DRAG()
	    .on(DRAG_START, function () {
	    })
	    .on("drag", function (d) {
		var panes = this.parentNode;
		var max;
		var dv, vl, vr;
		if (!panes.classList.contains('panes')) {
		    alert(panes);
		    return;
		}
		if (panes.classList.contains('horizontal')) {
		    max = panes.clientWidth;
		    vl = d[0].offsetWidth;
		    vr = d[1].offsetWidth;
		    dv = d3.event.dx;
		} else {
		    max = panes.clientHeight;
		    dv = d3.event.dy;
		    vl = d[0].offsetHeight;
		    vr = d[1].offsetHeight;
		}
		if (dv) {
		    console.log(vl, vr, dv);
		    vl += dv;
		    vr -= dv;
		    if (panes.classList.contains('auto')) {
			// If pane size is flexible (auto), use absolute pixel values and
			// control only left pane.
			d3.select(d[0])
			    .style('flex-basis', vl + "px");
			call_resize(d[0]);
			d3.select(d[0])
			    .selectAll("[data-resize]")
			    .each(function() {call_resize(this);});
		    } else {
			d3.select(d[0])
			    .style('flex-basis', (vl / max * 100) + "%");
			call_resize(d[0]);
			d3.select(d[0])
			    .selectAll("[data-resize]")
			    .each(function() {call_resize(this);});
			d3.select(d[1])
			    .style('flex-basis', (vr / max * 100) + "%");
			call_resize(d[1]);
			d3.select(d[1])
			    .selectAll("[data-resize]")
			    .each(function () { call_resize(this);});
		    }
		}
	    });
		   
    function prepare_panes(element) {
	var prev;
	for (var i = 0; i < element.children.length; ++i) {
	    var pane = element.children[i];
	    if (pane.classList.contains('pane')) {
		// console.log(i,pane);
		if (prev) {
		    // Add resizer BETWEEN panes
		    var resizer = document.createElement('div');
		    element.insertBefore(resizer, pane);
		    d3.select(resizer)
			.datum([prev, pane])
			.attr('class', 'pane-resizer')
			.call(drag_pane);
		    ++i; // ... avoid getting the same pane again!!!
		}
		prev = pane;
	    }
	}
    }

    d3.selectAll(".panes").each(function () { prepare_panes(this);});

    // Transform collapsible element
    //
    // <.collaps left|right|top|bottom>
    //    < ...content... >
    // </.collaps>
    // =>
    // <.collaps>
    //    <.collaps-wrapper>
    //      <..collaps content..>
    //    <.collaps-wrapper>
    //
    function prepare_collaps(element) {
	var collaps = d3.select(element);
	collaps
	    .insert("div", ":first-child")
	    .attr("class", "collaps-wrapper")
	    .each(function () {
		var parent = this.parentNode;
		var index = 0;
		while (parent.childNodes.length > 1) {
		    var child = parent.childNodes[index];
		    if (child === this) {
			index = 1;
			continue;
		    }
		    this.appendChild(child);
		}
	    });
	collaps
	    .insert("div", ":first-child")
	    .attr("class", "collaps-handle")
	    .on("click", function () {
		this.parentNode.classList.toggle("open");
	});
    }
    
    d3.selectAll(".collaps").each(function () { prepare_collaps(this);});
    
    // Enable context menu
    d3.selectAll(".context-menu")
	.on("contextmenu", context_menu)
	.on("click", context_clean);

    function shared_hold(selection) {
	var holding = document.getElementById("holding");
	if (!holding) return;
	selection.selectAll(".shared")
	    .each(function() {holding.appendChild(this);});
    }

    function shared_menu(selection) {
	selection
	    .on("mouseover", function() {
		if (d3.event.target !== this) return;
		var target = this;
		//var pos = getPosition(target);
		var shared = this.dataset.popupMenu; // == data-popup-menu
		var menu;
		if (shared) {
		    menu = d3.select('#' + shared).each(function() {
			if (this.parentNode !== target) {
			    target.appendChild(this);
			}
		    });
		} else {
		    menu = d3.select(target).select(".popup-menu");
		}
		var prepare = menu.attr("data-prepare");
		if (prepare)
		    call(prepare, menu.node());
	    })
	    .on("mouseleave", function () {
		shared_hold(d3.select(this));
	    });
    }

    function add_click_action(selection) {
	selection.on("click", click_action);
    }
    function add_change_action(selection) {
	selection.on("change", click_action);
    }
    function add_submit_action(selection) {
	selection.on("submit", submit_popup);
    }

    function _tooltip_position() {
	var tip = d3.select(this).select(".tooltip").node();
	var box = getPosition(this);
	var top = 0;
	var left = this.offsetWidth; // 'right' placement is the default
	if (tip.classList.contains('left')) {
	    left = -tip.offsetWidth;
	} else if (tip.classList.contains('top')) {
	    left = (left - tip.offsetWidth) / 2;
	    top = -tip.offsetHeight;
	} else if (tip.classList.contains('bottom')) {
	    left = (left - tip.offsetWidth) / 2;
	    top = this.offsetHeight;
	}
	d3.select(tip)
	    .style('position', 'fixed')
	    .style('left', (box.x + left)+"px")
	    .style('top', (box.y + top)+"px");
    }
    
    function add_tooltip_action(selection) {
	// The main responsibility of the tooltip outlook in CSS. This
	// function is only for positioning the tooltip (left, top).
	//
	// "tooltip_action" is optional, the but fixed positioning is
	// necessary when the tooltip would extend outside positioned
	// parent and thus clipped off.
	selection.each(function () {
	    var tip = this;
	    d3.select(tip.parentNode)
		.on("mouseover", _tooltip_position);
	});
    }

    function replace_text(elem, newtext) {
	var node;
	for (var i = 0; i < elem.childNodes.length; ++i) {
	    node = elem.childNodes[i];
	    if (node.nodeType == Node.TEXT_NODE) {
		// Replace content of the first text node
		node.nodeValue = newtext;
		return;
	    }
	}
	// No previous text node, create one
	node = document.createTextNode(newtext);
	elem.appendChild(node);
    }

    // Override default submit for any form with "data-submit" 
    d3.selectAll("form[data-submit]").on("submit", submit_popup);

    d3.selectAll(".click-action").on("click", click_action);
    d3.selectAll(".change-action").on("change", click_action);
    d3.selectAll(".popup-menu > li").on("click", click_action);
    d3.selectAll(".submit-action").on("click", submit_popup);
    d3.selectAll(".popup-menu-open").call(shared_menu);
    d3.selectAll(".menubar > li").call(shared_menu);
    d3.selectAll(".tooltip").call(add_tooltip_action);

    d3.selectAll("input[type=range]")
	.on("input", click_action)
	.on("change", click_action);
    
    d3.select("body")
	.on("contextmenu", context_clear);

    // Catch browser window resize events
    d3.select(window).on('resize', window_resize);
    console.log(d3.version);
    return {
	callbacks: function (actions) {
	    var keys = Object.keys(actions);
	    for (var i = 0; i < keys.length; ++i) {
		var key = keys[i];
		if (key in call_backs) {
		    alert("Duplicate callback '" + key + "' ignored");
		} else {
		    call_backs[key] = actions[key];
		}
	    }
	},
	open_popup: open_popup,
	close_popup: close_popup,
	context_popup: context_popup,
	context_menu: context_menu,
	shared_menu: shared_menu,
	shared_hold: shared_hold,
	replace_text: replace_text,
	add_click_action: add_click_action,
	add_change_action: add_change_action,
	add_submit_action: add_submit_action,
	add_tooltip_action: add_tooltip_action,
	add_menu_action: shared_menu,
	prepare_collaps: prepare_collaps,
	prepare_tabs: prepare_tabs,
	tab_select: tab_select,
	tab_bar: tab_bar,
	notify: notify,
	reset: reset
    };
})();
