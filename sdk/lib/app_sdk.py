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



class app_handler(tornado.websocket.WebSocketHandler):
	
    def __init__(self, *args, **kwargs):
	self.log = kwargs['log']
	self.uri = args[1].uri
	self.log.info("app_handler init for uri: " + str(self.uri))
	self.callback = kwargs['callback']
        self.register = kwargs['register']
        self.unregister = kwargs['unregister']
	self.reply = kwargs['reply']

	del kwargs['reply']
	del kwargs['callback']
        del kwargs['register']
        del kwargs['unregister']
	del kwargs['log']        
        
        super(app_handler,self).__init__(*args, **kwargs)

    def check_origin(self, origin):
        return True

    def open(self):
	if self.register is not None:
       	    self.register(self, "you are registered")
	self.log.info("app_handler: registered")

    def on_message(self, message):
	# its possibly optional and due to specific app        
	# message = tornado.escape.json_decode(message)
        self.log.info("app_handler: received message="+ str(message))
	self.log.info("app_handler: received on=" + str(self.uri))
	if self.callback is not None:	
	    self.callback(self, message)
	if self.reply is not None:
	    self.send(self.reply(self, message))

    def on_close(self):
	if self.unregister is not None:
            self.unregister(self, "you are unregistered")
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

    def add_options(self, uri, callback=None, reply=None, register=None,unregister=None):
        """
        
        """
	self.handler_list.append(("/" + uri, app_handler, {'log':self.log, 'callback' : callback, 'reply' : reply,
							   'register' : register,'unregister' : unregister}))
	
    def send_apps_list(self, client, message):
	list_apps = []
	for i in self.handler_list:
	    list_apps.append(i[0][1:])
	return {'Available apps' : str(list_apps)}

    def run_app(self):    
	self.add_options("", reply=self.send_apps_list)
	app = tornado.web.Application(self.handler_list, **self.settings)
	app.listen(self.port, self.address)
        
