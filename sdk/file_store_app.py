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

# webserver
import tornado
# periodic loop
import tornado.ioloop

from lib import flexran_sdk
from lib import app_sdk
from lib import logger

class file_store_app(object):

    name = "file_store_app"

    def __init__(self, log, directory='/tmp/'):
        super(file_store_app, self).__init__()
        self.log = log
        self.dir = directory
        self.file_list = self.dir + 'file_list'
        f = open(self.file_list, 'a')
        f.close()

    def push(self, client, *args):
        l = []
        name = args[0]
        body = client.request.body
        client.set_header("Content-Type", "text/plain")
        if body is "":
            client.write("no body")
        f = open(self.dir + name, 'wb')
        f.write(body)
        f.close()
        f = open(self.file_list, 'r+')
        for line in f.readlines():
            if line == name + "\n":
                f.close()
                client.write("updated\n")
                return
        # did not find, add it
        f.write(name)
        f.write("\n")
        f.close()
        client.write("ok\n")

    def retrieve(self, client, *args):
        name = args[0]
        client.set_header("Content-Type", "application/octet-stream")
        f = open(self.dir + name, 'rb')
        client.write(f.read())

    def list(self, client, *args):
        client.set_header("Content-Type", "text/plain")
        f = open(self.file_list, "r")
        client.write(f.read())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost',
                        help='set the App address for open data (HTTP): localhost (default)')
    parser.add_argument('--app-port', metavar='[option]', action='store', type=int,
                        required=False, default=8080,
                        help='set the App port for open data: 8080 (default)')
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='info',
                        help='set the log level: debug, info (default), warning, error, critical')
    parser.add_argument('--directory', metavar='[option]', action='store', type=str,
                        required=False, default='/tmp/',
                        help='directory to store received objects')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args()

    log = flexran_sdk.logger(log_level = args.log,
                             format = "[%(levelname)s] %(message)s").init_logger()

    app = file_store_app(log = log)

    # open data, i.e. exposing an interface to the drone app
    app_open_data = app_sdk.app_builder(log = log,
                                        app = file_store_app.name,
                                        address = args.app_url,
                                        port = args.app_port)
    app_open_data.add_http_handler("push/([A-Za-z0-9_+-]+)", post = app.push)
    app_open_data.add_http_handler("retrieve/([A-Za-z0-9_+-]+)", get = app.retrieve)
    app_open_data.add_http_handler("list", get = app.list)
    app_open_data.run_app()
    app_sdk.run_all_apps()
