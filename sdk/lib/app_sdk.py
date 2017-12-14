import os
import sys
import signal
import pwd
import glob
import ssl
import base64
import subprocess
import tornado.ioloop
import tornado.iostream
import tornado.process
import tornado.web
import tornado.websocket
import tornado.options
import datetime

class app_handler:

    def __init__(self, log, callback=None):
	self.clients = []
	self.log = log
	self.callback = callback
	
    def register(self, client, message):
	if not client in self.clients:
            self.clients.append(client)
	self.log.info(message + ' APP registered')
    
    def unregister(self, client, message):
	if client in self.clients:
            self.clients.remove(client)
	self.log.info(message + ' APP unregistered')

    def on_received(self, client, message):
	if self.callback is not None:
	    self.callback(client, message)

    def send(self, message):
	for i in self.clients:
	    i.send(message)

class client_handler(tornado.websocket.WebSocketHandler):
	
    def __init__(self, *args, **kwargs):
	self.log = kwargs['handler'].log
	self.uri = args[1].uri
	self.log.info("app_handler init for uri: " + str(self.uri))
	self.handler = kwargs['handler']

	del kwargs['handler']        
        
        super(client_handler,self).__init__(*args, **kwargs)

    def check_origin(self, origin):
        return True

    def open(self):
       	self.handler.register(self, "you are registered")
	self.log.info("app_handler: registered")

    def on_message(self, message):
	# its possibly optional and due to specific app        
	# message = tornado.escape.json_decode(message)
        self.log.info("app_handler: received message="+ str(message))
	self.log.info("app_handler: received on=" + str(self.uri))	
	self.handler.callback(self, message)

    def on_close(self):
        self.handler.unregister(self, "you are unregistered")
        self.log.info("app_handler: unregistered")
         
    def send(self, msg):
        self.write_message(msg)

class app_builder:
    
    def __init__(self, log, app="test",address="localhost", port=8080):
	self.log = log
        self.handler_list = []
        self.app=app
        self.address = address.replace("http://","")
	self.port = port
	self.log.info("Creating app with address '{0}' on port '{1}'".format(self.address, self.port))       
        if not os.path.exists(self.app):
            os.makedirs(self.app)
            
    	self.settings = {
            "static_path": os.path.join(os.path.dirname(__file__), self.app)
    	}

    def add_options(self, uri, handler):
        """
        
        """
	self.handler_list.append(("/" + uri, client_handler, {'handler': handler}))

    def add_runtime_options(self, uri, handler):
	handler = ("/" + uri, client_handler, {'handler': handler})
	self.handler_list.append(handler)
	self.app.add_handlers(self.address,[handler,])
	
    def send_apps_list(self, client, message):
	list_apps = []
	for i in self.handler_list:
	    list_apps.append(i[0][0:])
	client.send({'Available apps' : str(list_apps)})

    def send_time(self, client, message):
	client.send(datetime.datetime.now())

    def run_app(self):    
	self.add_options("", app_handler(log=self.log, callback=self.send_apps_list))
	self.add_options("time", app_handler(log=self.log, callback=self.send_time))
	self.app = tornado.web.Application(self.handler_list, **self.settings)
	self.app.listen(self.port, self.address)
        
