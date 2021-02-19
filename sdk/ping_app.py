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
    File name: ping_app.py
    Author: Robert Schmidt
    Description: This app performs ping to phones and shows it in the drone
    version: 1.0
    Python Version: 2.7
"""

import argparse
import json
import random

from pythonping import ping

# webserver
import tornado
# periodic loop
import tornado.ioloop

from lib import flexran_sdk
from lib import app_sdk
from lib import logger

class ping_app(object):

    name = "ping_app"
    odata_capabilities = 'capabilities'
    odata_refresh = 'Refresh'
    odata_start_ping = 'Start Ping'
    odata_stop_ping = 'Stop Ping'
    open_data = {
        odata_refresh: { 'help': 'Refresh the current list' },
        odata_start_ping: {
            'help': 'Start Ping to a UE',
            'schema': [
                {
                    'name': 'BS',
                    'type': 'number',
                    'choice': ['#ENBID'],
                    'help': 'Select BS'
                },
                {
                    'name': 'UE',
                    'type': 'number',
                    'choice': ['#UEID'],
                    'help': 'Select UE'
                },
                {
                    'name': 'Interval',
                    'type': 'number',
                    'choice': [0.25, 1],
                    'help': 'ping interval times'
                },
                {
                    'name': 'IP',
                    'type': 'text',
                    'text': '',
                    'help': 'IP address of UE'
                }
            ]
        },
        odata_stop_ping: {
            'help': 'Stop Ping to a UE',
            'schema': [
                {
                    'name': 'BS-UE',
                    'type': 'text',
                    'choice': [],
                    'help': 'Select BS-UE'
                }
            ]
        }
    }

    def __init__(self, log, url='http://localhost', port='9999'):
        super(ping_app, self).__init__()

        self.url = url+port
        self.log = log
        self.pings = {}
        self.clients = []

    def stop_cb(self, bs, rnti, msg):
        name = str(bs)+'-'+str(rnti)
        self.pings[name]['cb'].stop()
        del self.pings[name]
        l = ping_app.open_data[ping_app.odata_stop_ping]['schema'][0]['choice']
        ping_app.open_data[ping_app.odata_stop_ping]['schema'][0]['choice'] = [i for i in l if i != name]
        for client in self.clients:
            client.send_notification(ping_app.odata_capabilities,
                                     ping_app.open_data)
        for client in self.clients:
            client.send_notification('ue_info', { 'bs_id': int(bs), 'rnti': int(rnti), 'text': msg, 'app': 'ping' } )

    def send_ping(self, bs_id, rnti, ip, interval):
        try:
            rl = ping(ip, verbose=True, size=100, count=1)
        except Exception as error:
            self.stop_cb(bs_id, rnti, 'Exception: {}'.format(error))
            return
        if not rl.success:
            self.stop_cb(bs_id, rnti, rl.error_message)
            return
        rtt = rl.rtt_max_ms
        num = 3/interval
        alpha = 2/(num+1)
        name = str(bs_id)+'-'+str(rnti)
        avg = self.pings[name]['avg']
        avg = (1-alpha) * avg + alpha * rtt
        self.pings[name]['avg'] = avg
        params = {
            'bs_id': bs_id,
            'rnti': rnti,
            'text': 'avg {:5.1f} ms'.format(avg),
            'app': 'ping'
        }
        for client in self.clients:
            client.send_notification('ue_info', params)

    def handle_start_ping(self, client, id, method, params, message):
        bs = params['BS']
        ue = params['UE']
        ip = params['IP']
        interval = params['Interval']
        #self.log.info(params)
        name = str(bs)+'-'+str(ue)
        self.pings[name] = {'cb': tornado.ioloop.PeriodicCallback(lambda: app.send_ping(bs, ue, ip, interval), interval * 1000), 'avg': 0}
        self.pings[name]['cb'].start()
        ping_app.open_data[ping_app.odata_stop_ping]['schema'][0]['choice'] += [name]
        self.log.info(name + ': start ping for BS ' + str(bs) + ', UE ' + str(ue) + ' at IP ' + ip + ' at interval ' + str(interval))
        for client in self.clients:
            client.send_notification(ping_app.odata_capabilities,
                                     ping_app.open_data)
        pass

    def handle_stop_ping(self, client, id, method, params, message):
        #self.log.info(params)
        name = params['BS-UE']
        [bs, ue] = name.split('-')
        self.stop_cb(int(bs),str(ue),"undefined")
        pass

    def handle_new_client(self, client):
        log.info(self.handle_new_client.__name__ + "()")
        self.clients.append(client)
        client.send_notification(ping_app.odata_capabilities, ping_app.open_data)

    def handle_term_client(self, client):
        self.clients.remove(client)

    def open_data_load_status(self, params):
        pass

    def open_data_save_status(self):
        pass

    def handle_message(self, client, id, method, params, message):
        log.info(self.handle_message.__name__ + "(): method '" + method
                    + "', message '" + str(message) + "'")
        if   (method == ping_app.odata_refresh or
                method == ping_app.odata_capabilities):
            client.send_notification(ping_app.odata_capabilities, ping_app.open_data)
        elif (method == ping_app.odata_start_ping):
            self.handle_start_ping(client, id, method, params, message)
        elif (method == ping_app.odata_stop_ping):
            self.handle_stop_ping(client, id, method, params, message)

    def handle_notification(self, client, method, params, message):
        log.info(self.handle_notification.__name__ + "(): method '" + method
                    + "', message '" + str(message) + "'")
        if method == ping_app.odata_capabilities:
            client.send_notification(method, ping_app.open_data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost',
                        help='set the FlexRAN RTC URL: loalhost (default)')
    parser.add_argument('--port', metavar='[option]', action='store', type=str,
                        required=False, default='9999',
                        help='set the FlexRAN RTC port: 9999 (default)')
    parser.add_argument('--app-url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost',
                        help='set the App address to open data: loalhost (default)')
    parser.add_argument('--app-port', metavar='[option]', action='store', type=int,
                        required=False, default=8080,
                        help='set the App port to open data: 8080 (default)')
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='info',
                        help='set the log level: debug, info (default), warning, error, critical')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args()

    log = logger.sdk_logger(log_level=args.log,
                            format="[%(levelname)s] %(message)s").init_logger()
    app = ping_app(log = log,
                   url = args.url,
                   port = args.port)

    # open data, i.e. exposing an interface to the drone app
    app_open_data=app_sdk.app_builder(log=log,
                                      app=ping_app.name,
                                      address=args.app_url,
                                      port=args.app_port)
    ho_open_data = app_sdk.app_handler(ping_app.name,
                                       log = log,
                                       callback = app.handle_message,
                                       notification = app.handle_notification,
                                       init = app.handle_new_client,
                                       save = app.open_data_save_status,
                                       load = app.open_data_load_status,
                                       term = app.handle_term_client)

    app_open_data.add_options("list", handler=ho_open_data)
    app_open_data.run_app()

    app_sdk.run_all_apps()
