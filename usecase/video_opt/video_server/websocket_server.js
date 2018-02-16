"use strict";
var http = require('http');
var WebSocketServer = require('websocket').server;
var url = require('url')
var path = require('path')

var fs = require('fs');

const PUBLISHER_RULE = 'pub'
const SUBSCRIBER_RULE = 'sub'
const BROWSER_RULE = 'browser'
const VERBOSE = false

/**
* When the streamer sets this field, it will be compliant with this format:
*	{
fps: 20,				//frame rate
encodeBps: 500000,		//encoder bitrate (default=500Kpbs)
width: 320,				//frame width
height: 240,			//frame height
configArray: '',		//SPS-PPS array for H.264 stream configuration
}
*/
var configuration = undefined;
var port = 9090;
var streamer = undefined;
var publisherDeviceName = undefined
var subscribers = [];
var browserClients = [];
var params = [];
var lowParams = undefined, mediumParams = undefined, highParams = undefined;
var currentQuality = undefined;
//var bitrates = [];
//var currentBitrate = undefined;

String.format = function() {
  // The string containing the format items (e.g. '{0}')
  // will and always has to be the first argument.
  var theString = arguments[0];
  // start with the second argument (i = 1)
  for (var i = 1; i < arguments.length; i++) {
    // 'gm' = RegEx options for Global search (more than one instance)
    // and for Multiline search
    var regEx = new RegExp('\\{' + (i - 1) + '\\}', 'gm');
    theString = theString.replace(regEx, arguments[i]);
  }
  return theString;
}

function parseHTTPbody(bodyString){
  var fields = bodyString.split('&');
  if (fields === undefined || fields.length == 0){
    return undefined;
  }
  var s = '{';
  fields.forEach(function(entry, index, array) {
    var ss = entry.split('=');
    if (ss === undefined || ss.length != 2){
      return;
    }
    var key = '\"'+ss[0]+'\"';
    var value = '\"'+ss[1]+'\"';
    var sep = (index == array.length-1) ? '' : ', ';
    s += ( key + ':' + value + sep );
  });
  s += '}';
  try{
    return JSON.parse(s);
  }
  catch(Exception){
    return undefined;
  }
}

var httpServerCallback = function(request, response) {
  if (request.method == 'GET'){
    if (request.url === '/favicon.ico') {
      response.writeHead(200, {'Content-Type': 'image/x-icon'} );
      response.end();
      console.log('favicon requested');
      return;
    }
    var uri = url.parse(request.url).pathname;
    var filename = path.join(process.cwd(), uri);
    fs.stat(filename, function(err, stat) {
      if(err) {
        console.log('err='+err.code+' retrieving '+filename)
        response.writeHead(404, {'Content-Type': 'text/plain'});
        response.write('404 Not Found\n');
        response.end();
        return;
      }
      if (stat.isDirectory()){
        filename += '/index2.html';
      }
      fs.readFile(filename, 'binary', function(err, file) {
        if(err) {
          response.writeHead(500, {'Content-Type': 'text/plain'});
          response.write(err + '\n');
          response.end();
          return;
        }
        response.writeHead(200, 'OK', {'Content-Type': 'text/html'});
        response.write(file, 'binary');
        response.end();
      });
    });
  }
  else if (request.method == 'POST'){
    var body = '';
    var timestamp_t1 = Date.now();
    request.on('data', function (data) {
        body += data;
    });

    request.on('end', function() {
      if(request.url == "/time"){
        let json_req = JSON.parse(body);
        let json = JSON.stringify({
          timestamp_t2 : Date.now(),
          timestamp_t1 : timestamp_t1,
          timestamp_t0 : json_req.timestamp_t0
        });
        response.end(json);
      }else{

        var bodyObj = parseHTTPbody(body);
        if (bodyObj === undefined){
          return;
        }
        if (bodyObj.hasOwnProperty('congestion') && bodyObj.hasOwnProperty('bitrate')){
          console.log('CONGESTION MESSAGE RECEIVED: ' + JSON.stringify(bodyObj));
          var congestionValue = parseInt(bodyObj.congestion);
          if (isNaN(congestionValue)){
            console.log('Can\'t parse congestion value ' + bodyObj.congestion);
            return;
          }
          var bitrateValue = bodyObj.bitrate;
          var targetParams = undefined;
          switch (bitrateValue){
            case 'low':
            case 'LOW':
            targetParams = lowParams;
            break;
            case 'medium':
            case 'MEDIUM':
            targetParams = mediumParams;
            break;
            case 'high':
            case 'HIGH':
            targetParams = highParams;
            break;
            default:
            console.log('Unknown bitrate value: ' + bitrateValue);
            break;
          }
          if (targetParams !== undefined){
            console.log('Triggered change to params: ' + JSON.stringify(targetParams));
            var resetMessage = buildParamsObj(targetParams.width, targetParams.height, targetParams.bitrate);
            resetMessage['type'] = 'reset';
            resetMessage['quality'] = bitrateValue;
            console.log('RESET message: '+resetMessage);
            forwardToSubscribers(JSON.stringify(resetMessage));
            forwardToStreamer(JSON.stringify(resetMessage));
          }
        }

        response.writeHead(200, 'OK', {'Content-Type': 'text/html'});
        response.write('<html>');
        response.write('<head><title>OK!</title></head>');
        response.write('<body><h1>200 OK</h1><p>That\'s ok. Enjoy!</p></body>');
        response.write('</html>');
        response.end();
      }
    });
  }

}

var server = http.createServer(httpServerCallback);
server.listen(port, function() {
  console.log((new Date()) + ' Server running at http://127.0.0.1:'+port);
});



var onTextMessageReceived = function(message, webSocket) {
	var json;
	if ((json = parseJSON(message.utf8Data)) == null){
		console.log('Can\'t parse JSON. Discarding text message');
		return;
	}
	if (!json.hasOwnProperty('rule')){
		console.log('No rule for this JSON message. Will discard...');
		return;
	}


	//I'm the sender
	if (json.rule === PUBLISHER_RULE){
		switch (json.type) {
			case 'hello':
			/*if (streamer !== undefined){
			if (VERBOSE) console.log('Publisher already defined. Discarding HELLO request');
			webSocket.close();
			break;
			}*/
				streamer = webSocket
				publisherDeviceName = json.device
				params = []
				//each param is in string format 'wxh b'
				json.qualities.forEach(function(element, index, array){
				  var q = element.split(' ');
				  var size = q[0];
				  var bitrate = q[1];
				  q = size.split('x');
				  if (q.length != 2){
					return;
				  }
				  var param = {
					w: parseInt(q[0]),
					h: parseInt(q[1]),
					b: parseInt(bitrate)
				  }
				  var newParam = buildParamsObj(param.w, param.h, param.b);
				  if (newParam.bitrate < 1024){
					lowParams = newParam;
				  }
				  else if (newParam.bitrate < 2048){
					mediumParams = newParam;
				  }
				  else if (newParam.bitrate < 4096){
					highParams = newParam;
				  }
				  params.push(newParam);
				})
				currentQuality = params[json.current];
				//bitrates = json.bitrates;
				//currentBitrate = json.currentBitrate;
				if (VERBOSE) {
				  console.log('Hello from publisher '+json.device+'\n My resolutions: '+json.qualities);
				  logAll()
				}
				var notice = getQualitiesNoticePacket();
				forwardToBrowsers(JSON.stringify(notice));
				//forwardToSubscribers(JSON.stringify(qualitiesNotice));
				break;

			case 'config':
				var configArray = json.data;
				var width = json.width;
				var height = json.height;
				var encodeBps = json.encodeBps;
				var frameRate = json.frameRate;
				currentQuality = buildParamsObj(width, height, encodeBps);
				//currentQuality = width + 'x' + height;
				//currentBitrate = encodeBps;
				if (VERBOSE) console.log('\nNew quality: '+JSON.stringify(currentQuality));

				var notice = getQualitiesNoticePacket();
				forwardToBrowsers(JSON.stringify(notice));

				setConfigParams(configArray, width, height, encodeBps, frameRate);
				var response = getConfigPacket();
				//if (VERBOSE) console.log('sending config: '+JSON.stringify(response)+' to subscribers ');
				forwardToSubscribers(JSON.stringify(response));
				break;

			case 'stream':
				//var response = message.utf8Data;
				//console.log('seq num -> '+json.num);
				//if (VERBOSE) process.stdout.write('.');
				//forwardToSubscribers(response);
				break;

			case 'reset':
				break;
		}
	}

	//I'm the receiver
	else if (json.rule === SUBSCRIBER_RULE){
	  var isNew = (subscribers.indexOf(webSocket) < 0);
	  switch (json.type) {
		case 'hello':
		if (isNew){
		  subscribers.push(webSocket);
		  if (VERBOSE){
			console.log('Hello from subscriber: '+webSocket.remoteAddress)
			logAll()
		  }
		}
		break;

		case 'config':
		if (isNew){
		  if (VERBOSE) console.log('Unknown subscriber');
		  break;
		}
		if (VERBOSE) console.log('config requested by sub '+webSocket.remoteAddress)
		var conf = getConfigPacket()
		if (conf === undefined){
		  //no configuration was set, i.e. no stream sender started streaming
		  if (VERBOSE) console.log('no config available yet')
		  break;
		}
		//send configuration back to the client who made request
		if (VERBOSE) console.log('sending config params to sub '+webSocket.remoteAddress)
		webSocket.sendUTF(JSON.stringify(conf))
		break;
	  }
	}

	//I'm the browser client
	else if (json.rule === BROWSER_RULE){
	  var isNew = (browserClients.indexOf(webSocket) < 0);
	  switch (json.type) {
		case 'hello':
		if (isNew){
		  browserClients.push(webSocket);
		  if (VERBOSE) {
			console.log('Hello from browser client: '+webSocket.remoteAddress)
			logAll()
		  }
		}
		//must contain qualities, if they exist
		var qualitiesNotice = getQualitiesNoticePacket();
		webSocket.sendUTF(JSON.stringify(qualitiesNotice));
		break;

		case 'reset':
		if (isNew){
		  if (VERBOSE) console.log('Unknown web client');
		  break;
		}
		if (VERBOSE) console.log('Received RESET from client '+webSocket.remoteAddress)
		logAll()
		var response = message.utf8Data;
		forwardToStreamer(response);
		forwardToSubscribers(response);
		//webSocket.sendUTF(response)
		break;
	  }
	}
}

function onBinaryMessageReceived(message, webSocket){
  if (VERBOSE) process.stdout.write('.');
  for (var i=0; i < subscribers.length; i++) {
    subscribers[i].sendBytes(message.binaryData);
  }
}


var wsServer = new WebSocketServer({
  httpServer: server,
  autoAcceptConnections: false
});
wsServer.config.maxReceivedMessageSize = 16*1024*1024
wsServer.config.maxReceivedFrameSize = 512*1024

Object.prototype.getName = function() {
  var funcNameRegex = /function (.{1,})\(/;
    var results = (funcNameRegex).exec((this).constructor.toString());
    return (results && results.length > 1) ? results[1] : "";
};


wsServer.on('request', function(request) {

  if (!originIsAllowed(request)){
    if (VERBOSE) console.log('Connection refused');
    return;
  }

  var connection = request.accept(null,request.origin);
  console.log((new Date()) + ' Connection accepted.')
  connection.on('message', function(message){
    if (message.type === 'utf8') {
      onTextMessageReceived(message, connection);
    }
    else if (message.type === 'binary') {
      onBinaryMessageReceived(message, connection);
    }
  });
  connection.on('close', function(reasonCode, description) {
    if (connection === streamer){
      streamer = undefined;
      publisherDeviceName = undefined;
      params = []; lowParams = undefined; mediumParams = undefined; highParams = undefined;
      currentQuality = undefined;
      //bitrates = [];
      //currentBitrate = undefined;
      configuration = undefined;
      if (VERBOSE) {
        console.log('\nStreamer reset! Bye');
        logAll();
      }
    }
    if (subscribers.indexOf(connection) >= 0){
      if (VERBOSE) console.log('Subscriber '+connection.remoteAddress+' left');
      subscribers.splice(subscribers.indexOf(connection), 1);
    }
    if (browserClients.indexOf(connection) >= 0){
      if (VERBOSE) console.log('Browser client '+connection.remoteAddress+' left');
      browserClients.splice(browserClients.indexOf(connection), 1);
    }
    console.log((new Date()) + ' client ' + connection.remoteAddress + ' disconnected.');
  });
});

function forwardToStreamer(obj){
  if (streamer !== undefined){
    streamer.sendUTF(obj);
  }
}

function forwardToSubscribers(obj){
  for (var i=0; i < subscribers.length && streamer; i++) {
    subscribers[i].sendUTF(obj);
  }
}

function forwardToBrowsers(obj){
  for (var i=0; i < browserClients.length; i++) {
    browserClients[i].sendUTF(obj);
  }
}

function setConfigParams(configArray, width, height, encodeBps, frameRate){
  configuration = {
    fps: frameRate,
    encodeBps: encodeBps,
    width: width,
    height: height,
    configArray: configArray
  };
}

function buildParamsObj(width, height, bitrate){
  var obj = {
    width: width,
    height: height,
    bitrate, bitrate
  }
  return obj;
}

function getConfigPacket(){
  if (configuration === undefined){
    return undefined;
  }
  var obj = {
    type: 'config',
    fps: configuration.fps,
    configArray: configuration.configArray,
    encodeBps: configuration.encodeBps,
    width: configuration.width,
    height: configuration.height
  }
  return obj;
}

function getQualitiesNoticePacket(){
  var obj = {
    type: 'qualitiesNotice',
    sizes: params,
    currentSize: currentQuality,
    //bitrates: bitrates,
    //currentBitrate: currentBitrate
  }
  return obj;
}

//utility functions
function parseJSON(str){
  var obj;
  try{
    obj = JSON.parse(str);
  }
  catch(e){
    console.log('syntax error: '+str);
    return null;
  }
  return obj;
}


function originIsAllowed(request) {
  // put logic here to detect whether the specified origin is allowed.
  if (streamer === undefined || streamer.remoteAddress === undefined){
    return true;
  }

  var hds = request.httpRequest.headers;
  var isPub = (hds.hasOwnProperty('rule') && (hds.rule === PUBLISHER_RULE));

  if (isPub && (streamer.remoteAddress !== request.remoteAddress)){
    if (VERBOSE) console.log('Publisher already defined');
    return false;
  }
  return true;
}

function logAll(){
  console.log('publisher: ' + ((streamer === undefined) ? streamer : streamer.remoteAddress))
  var s = '[ '
  for (var i=0; i < subscribers.length; i++) {
    s += subscribers[i].remoteAddress + ' '
  }
  s += ']'
  console.log('subscribers: '+s)
  s = '[ '
  for (var i=0; i < browserClients.length; i++) {
    s += browserClients[i].remoteAddress + ' '
  }
  s += ']'
  console.log('browser clients: '+s)
  //console.log('configuration= '+JSON.stringify(configuration))
}

function isStreamerAllowed(webSocket, messageObj){
  if (webSocket === undefined) return false;
  var rule = messageObj.rule;
  if (streamer === undefined){
    return rule === PUBLISHER_RULE;
  }
  return (rule === PUBLISHER_RULE) && (webSocket === streamer);
}

function isSubscriberAllowed(webSocket, messageObj){
  if (webSocket === undefined) return false;
  return messageObj.rule === SUBSCRIBER_RULE;
}

function isBrowserAllowed(webSocket, messageObj){
  if (webSocket === undefined) return false;
  return messageObj.rule === BROWSER_RULE;
}

// var sendUtcTime = function(){
//   let json = JSON.stringify({
//     type: "sync",
//     timestamp : Date.now()
//   });
//   forwardToStreamer(json);
//   json = JSON.stringify({
//     type: "sync",
//     timestamp : Date.now()
//   });
//   forwardToSubscribers(json);
//   setTimeout(sendUtcTime, 2 * 1000);
// }
//
// setTimeout(sendUtcTime, 2 * 1000);
