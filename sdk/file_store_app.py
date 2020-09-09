from __future__ import division
# force division to return a float as in Python 3

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
    File name: file_store_app.py
    Author: Robert Schmidt
    Description: Push, list, retrieve any files
    version: 1.0
    Python Version: 2.7
"""

import argparse
import json
import os

# webserver
import tornado
# periodic loop
import tornado.ioloop

from lib import flexran_sdk
from lib import app_sdk
from lib import logger

class file_store_app(object):

    name = "file_store_app"
    odata_capabilities = 'capabilities'
    odata_refresh = 'Refresh'
    odata_remove = 'Remove'
    odata_push = 'Push'
    open_data = {
        odata_refresh: { 'help': 'Refresh the current list' },
        odata_remove: {
            'help': 'Remove objects from the NetStore',
            'schema': [
                {
                    'name': 'objects',
                    'type': 'string',
                    'checkbox': [],
                    'help': 'Select the object to remove'
                }
            ]
        },
        odata_push: {
            'help': 'Push objects into the NetStore (NetStore has to run on the same machine)',
            'schema': [
                {
                    'name': 'objectname',
                    'type': 'string',
                    'text': '',
                    'help': 'Name of the object'
                },
                {
                    'name': 'filename',
                    'type': 'string',
                    'text': '',
                    'help': 'Full path to file on the machine of the NetStore'
                }
            ]
        },
    }

    def __init__(self, log, directory):
        super(file_store_app, self).__init__()
        self.log = log
        self.dir = directory
        self.file_list = self.dir + 'file_list'
        self.check_and_create()
        self.clients = [] # list of clients, used to push notifications of new UEs
        self.update_odata()

    def update_odata(self):
        o = self.list_array()
        file_store_app.open_data[file_store_app.odata_remove]['schema'][0]['checkbox'] = o
        listing = self.list_array()
        for client in self.clients:
            client.send_notification(file_store_app.odata_capabilities,
                                     file_store_app.open_data)
            client.send_notification('app_info', listing)

    def check_and_create(self):
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        f = open(self.file_list, 'a')
        f.close()

    def do_push(self, name, body):
        f = open(self.dir + name, 'wb')
        f.write(body)
        f.close()
        self.check_and_create()
        f = open(self.file_list, 'r+')
        for line in f.readlines():
            if line == name + "\n":
                f.close()
                return name + ": updated\n"
        # did not find, add it
        f.write(name)
        f.write("\n")
        f.close()
        return name + ": ok\n"

    def push(self, client, *args):
        l = []
        name = args[0]
        body = client.request.body
        client.set_header("Content-Type", "text/plain")
        if body is "":
            client.write("no body\n")
            return
        msg = self.do_push(name, body)
        client.write(msg)
        self.update_odata()

    def retrieve(self, client, *args):
        name = args[0]
        client.set_header("Content-Type", "application/octet-stream")
        try:
            f = open(self.dir + name, 'rb')
        except:
            raise tornado.web.HTTPError(404)
            return
        client.write(f.read())
        f.close()

    def list_array(self, reduce_output=True):
        self.check_and_create()
        f = open(self.file_list, "r")
        text = []
        num = 0
        for l in f.readlines():
            text += [l.strip('\n')]
            num += 1
            if reduce_output and num == 5:
                text[-1] = '...'
                break
        f.close()
        return text

    def list(self, client, *args):
        client.set_header("Content-Type", "text/plain")
        for l in self.list_array(reduce_output = False):
            client.write(l + '\n')

    def do_remove(self, name):
        f = open(self.file_list, 'r+')
        lines = f.readlines()
        f.seek(0)
        is_del = False
        ret_text = ''
        for l in lines:
            if l != name + "\n":
                f.write(l)
            else:
                os.remove(self.dir + name)
                ret_text = name + ": deleted"
                is_del = True
        f.truncate()
        f.close()
        if not is_del:
            ret_text = name + ": no such object\n"
        return ret_text

    def remove(self, client, *args):
        client.set_header("Content-Type", "text/plain")
        name = args[0]
        msg = self.do_remove(name)
        client.write(msg + '\n')
        self.update_odata()

    def handle_remove(self, client, id, method, params, message):
        objects = params['objects']
        for o in objects:
            self.do_remove(o)
        self.update_odata()

    def handle_push(self, client, id, method, params, message):
        objectname = params['objectname']
        if objectname == '':
            return
        filename = params['filename']
        contents = ""
        try:
            f = open(filename, 'r')
            contents = f.read()
            f.close()
        except:
            self.log.error("file '" + filename + "' not found!")
            return
        self.do_push(objectname, contents)
        self.update_odata()

    def handle_message(self, client, id, method, params, message):
        log.info(self.handle_message.__name__ + "(): method '" + method
                    + "', message '" + str(message) + "'")
        if (method == file_store_app.odata_refresh
            or method == file_store_app.odata_capabilities):
            client.send_notification(file_store_app.odata_capabilities,
                                     file_store_app.open_data)
            client.send_notification('app_info', self.list_array())
        elif method == file_store_app.odata_remove:
            self.handle_remove(client, id, method, params, message)
        elif method == file_store_app.odata_push:
            self.handle_push(client, id, method, params, message)

    def handle_notification(self, client, method, params, message):
        log.info(self.handle_notification.__name__ + "(): method '" + method
                    + "', message '" + str(message) + "'")
        if method == file_store_app.odata_capabilities:
            client.send_notification(method, file_store_app.open_data)

    def handle_new_client(self, client):
        log.info(self.handle_new_client.__name__ + "()")
        self.clients.append(client)
        client.send_notification(file_store_app.odata_capabilities,
                                 file_store_app.open_data)
        client.send_notification('app_info', self.list_array())

    def handle_term_client(self, client):
        self.clients.remove(client)
        pass

    def open_data_load_status(self, params):
        pass

    def open_data_save_status(self):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost',
                        help='set the app address for open data (WebSocket): localhost (default)')
    parser.add_argument('--app-port', metavar='[option]', action='store', type=int,
                        required=False, default=8083,
                        help='set the app port for open data (WebSocket): 8083 (default)')
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='info',
                        help='set the log level: debug, info (default), warning, error, critical')
    parser.add_argument('--directory', metavar='[option]', action='store', type=str,
                        required=False, default='/tmp/netstore/',
                        help='directory to store received objects')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args()

    log = flexran_sdk.logger(log_level = args.log,
                             format = "[%(levelname)s] %(message)s").init_logger()

    app = file_store_app(log = log, directory=args.directory)

    # open data, i.e. exposing an interface to the drone app
    app_rest_data = app_sdk.app_builder(log = log,
                                        app = file_store_app.name,
                                        address = args.app_url,
                                        port = args.app_port)
    app_rest_data.add_http_handler("push/([A-Za-z0-9_+-]+)", post = app.push)
    app_rest_data.add_http_handler("retrieve/([A-Za-z0-9_+-]+)", get = app.retrieve)
    app_rest_data.add_http_handler("list", get = app.list)
    app_rest_data.add_http_handler("remove/([A-Za-z0-9_+-]+)", delete = app.remove)

    ws_handler = app_sdk.app_handler(file_store_app.name,
                                      log = log,
                                      callback = app.handle_message,
                                      notification = app.handle_notification,
                                      init = app.handle_new_client,
                                      save = app.open_data_save_status,
                                      load = app.open_data_load_status,
                                      term = app.handle_term_client)
    app_rest_data.add_options("info", handler = ws_handler)
    app_rest_data.run_app()
    app_sdk.run_all_apps()
