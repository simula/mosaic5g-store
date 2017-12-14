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



class AppHandler(tornado.websocket.WebSocketHandler):
	
    def __init__(self, *args, **kwargs):
        print ("ws init: " + " " + str(args[1].uri))
	self.uri = args[1].uri
	self.callback = kwargs['callback']
        self.register = kwargs['register']
        self.unregister = kwargs['unregister']
	print kwargs
	del kwargs['callback']
        del kwargs['register']
        del kwargs['unregister']
                
        super(AppHandler,self).__init__(*args, **kwargs)

    def check_origin(self, origin):
        return True

    def open(self):
        print("ws open: register to the client")
        self.register(self, "hello")

    def on_message(self, message):
        message = tornado.escape.json_decode(message)
        print("ws message="+ str(message))
	print(self.uri)
	#print(self.callback)
	self.send({'URI':self.uri, 'CALLBACK' : self.callback(self, message)})

    def on_close(self):
        #self._detach()
        self.unregister(self, "bye")
        print ("ws closed")
         
    def send(self, msg):
        self.write_message(msg)

   # def _detach(self):
#	pass
        # Remove client from all running tasks

#    def __del__(self):
#        self._de


class app_builder:
    
    def __init__(self, app="test",address="localhost", port=8080):

        self.handler_list = []
        self.app=app
        self.address = address.replace("http://","")
	self.port = port
        print port
        print self.address 
        if not os.path.exists(self.app):
            os.makedirs(self.app)
            
    	self.settings = {
            "static_path": os.path.join(os.path.dirname(__file__), self.app) # parametr  name
    	}

    def add_options(self, uri, callback, register,unregister):
        """
        
        """
	self.handler_list.append((r"/{0}".format(uri), AppHandler, {'callback' : callback, 'register' : register,'unregister' : unregister}))
	
        
    def run_app(self):
        list_apps = []
	for i in self.handler_list:
	    list_apps.append(i[0])
            
	self.add_options("", lambda x,y: {'Available Apps': list_apps},lambda x,y:None,lambda x,y:None)
	app = tornado.web.Application(self.handler_list, **self.settings)
	app.listen(self.port, self.address)
        
