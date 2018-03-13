"""
   Licensed to the Mosaic5G under one or more contributor license
   agreements. See the NOTICE file distributed with this
   work for additional information regarding copyright ownership.
   The Mosaic5G licenses this file to You under the
   Apache License, Version 2.0  (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
  
    	http://www.apache.org/licenses/LICENSE-2.0
  
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
 -------------------------------------------------------------------------------
   For more information about the Mosaic5G:
   	contact@mosaic-5g.io
"""

"""
    File name: app_sdk.py
    Author: Lukasz Kulacz and navid nikaein
    Description: This lib provides an open data model framework for network control apps to share knowledge
    version: 1.0
    Date created:  15 Dec. 2017
    Date last modified: 15 Dec 2017 
    Python Version: 2.7
    
"""
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

    def __init__(self, log, callback=None, notification=None):
	self.clients = []
	self.log = log
	self.callback = callback
	self.notification = notification
	
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

    def notify(self, method, message=None):
	for i in self.clients:
	    i.send_notification(method, message)

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
        self.log.info("app_handler: received message="+ str(message))
        self.log.info("app_handler: received on=" + str(self.uri))	

        # main decoding part
        message = tornado.escape.json_decode(message)
        method = message.get('method')
        id = message.get('id')

        if method is None:
            # The message is a reply (error/succes) to a command
            # issued by this application to the client. As this app
            # currently does not send commands to clients, this should
            # not happen. The id should not be "None"...
            error = message.get('error')
            result = message.get('result')
            if error is not None:
                # Error reply to some command
                pass
            elif result is not None:
                # Success of some command
                pass
            else:
                # Invalid format
                pass
        elif id is None:
            # This message is a notification from the client. Because
            # "app_sdk" does not have a callback for new client
            # connection, we use the "capabilities" notification from
            # client to trigger capability notification from this app
            # to the client. Obviously, this does not work if the
            # client is using the same strategy (both would wait the
            # other).
	    self.handler.notification(self, method, message)
        else:
            # The message contains a command from the client
            self.handler.callback(self, id, method, message)

    def on_close(self):
        self.handler.unregister(self, "you are unregistered")
        self.log.info("app_handler: unregistered")
         
    def send(self, msg):
        self.write_message(msg)

    def send_error(self, id, code, message):
	self.send({
                    'id': id,
                    'error': {
                        'code': code,
                        'message': message
                    }})

    def send_result(self, id, result):
	self.send({
                    'id': id,
                    'result': result
                    })

    def send_notification(self, method, params=None):
	self.send({
		    'method': method,
	            'params': params
		   })

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
	client.send({'current_time': str(datetime.datetime.now())})

    def run_app(self):    
	self.add_options("", app_handler(log=self.log, callback=self.send_apps_list))
	self.add_options("time", app_handler(log=self.log, callback=self.send_time))
	self.app = tornado.web.Application(self.handler_list, **self.settings)
	self.app.listen(self.port, self.address)
        
def run_all_apps(): 
    # make sure that function is runned once per PC  
    try:
        tornado.ioloop.IOLoop.current().start()
    except:
	pass
