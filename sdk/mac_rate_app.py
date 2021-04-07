#! /usr/bin/python
from __future__ import print_function

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
    File name: mac_rate_app.py
    Author: Robert Schmidt
    Description: This app shows the data rate for every UE as well as the whole
        cell (last column) periodically..
    version: 1.0
"""

import json
import argparse

# webserver
import tornado
# periodic loop
import tornado.ioloop

from lib import flexran_sdk
from lib import app_sdk
from lib import logger

class mac_rate_app(object):

    name = "mac_rate_app"

    def __init__(self, log, url, port, op_mode, dl_interval, ul_interval, no_ue):
        super(mac_rate_app, self).__init__()

        self.url = url + ':' + port
        self.log = log
        self.op_mode = op_mode
        self.no_ue = no_ue

        self.dl_bytes = {} # bytes per RNTI
        self.dl_time = 0.0
        self.dl_interval = dl_interval
        if dl_interval > 0:
            tornado.ioloop.PeriodicCallback(lambda: self.dl_tick(), self.dl_interval * 1000).start()

        self.ul_bytes = {} # bytes per RNTI
        self.ul_time = 0.0
        self.ul_interval = ul_interval
        if ul_interval > 0:
            tornado.ioloop.PeriodicCallback(lambda: self.ul_tick(), self.ul_interval * 1000).start()

    def dl_tick(self):
        sm.stats_manager('all')
        self.dl_time += self.dl_interval
        print("DL {:5.1f}  ".format(self.dl_time), end = '')
        for bs in range(0, sm.get_num_enb()):
            bs_id = sm.get_enb_id(bs)
            cell = 0.0
            for ue in range(0, sm.get_num_ue(bs)):
                rnti = sm.get_ue_rnti(bs, ue)
                B = sm.get_ue_total_tbs(bs, ue, 'DL')
                if rnti not in self.dl_bytes:
                    self.dl_bytes[rnti] = B
                diff = B - self.dl_bytes[rnti]
                self.dl_bytes[rnti] = B
                cell += diff
                thr = diff * 8 / self.dl_interval / 1000000
                if not self.no_ue:
                    print("{:04x} {:5.2f}  ".format(rnti, thr), end = '')
            thr = cell * 8 / self.dl_interval / 1000000
            print("{} {:5.2f}".format(bs_id, thr), end = '')
        print("") # so "DL" gets always printed

    def ul_tick(self):
        sm.stats_manager('all')
        self.ul_time += self.ul_interval
        print("UL {:5.1f} ".format(self.ul_time), end = '')
        for bs in range(0, sm.get_num_enb()):
            bs_id = sm.get_enb_id(bs)
            cell = 0.0
            for ue in range(0, sm.get_num_ue(bs)):
                rnti = sm.get_ue_rnti(bs, ue)
                B = sm.get_ue_total_tbs(bs, ue, 'UL')
                if rnti not in self.ul_bytes:
                    self.ul_bytes[rnti] = B
                diff = B - self.ul_bytes[rnti]
                self.ul_bytes[rnti] = B
                cell += diff
                thr = diff * 8 / self.ul_interval / 1000000
                if not self.no_ue:
                    print("{:04x} {:5.2f} ".format(rnti, thr), end = '')
            thr = cell * 8 / self.ul_interval / 1000000
            print("{} {:5.2f}".format(bs_id, thr), end = '')
        print("") # so "UL" gets always printed

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost',
                        help='set the FlexRAN RTC URL: loalhost (default)')
    parser.add_argument('--port', metavar='[option]', action='store', type=str,
                        required=False, default='9999',
                        help='set the FlexRAN RTC port: 9999 (default)')
    parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
                        required=False, default='test',
                        help='Set the app operation mode either with FlexRAN or with the test json files: test(default), sdk')
    parser.add_argument('--dl-interval', metavar='[option]', action='store', type=float,
                        required=False, default=1.0,
                        help='interval at which DL throughput should be shown (0 -> off)')
    parser.add_argument('--ul-interval', metavar='[option]', action='store', type=float,
                        required=False, default=0.0,
                        help='interval at which UL throughput should be shown (0 -> off)')
    parser.add_argument('--no-ue', action='store_true', default=False,
                        help='do not show UEs\' throughput')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()

    log = flexran_sdk.logger().init_logger()

    sm = flexran_sdk.stats_manager(log = log,
                                   url = args.url,
                                   port = args.port,
                                   op_mode = args.op_mode)

    mac_rate_app = mac_rate_app(log = log,
                                url = args.url,
                                port = args.port,
                                op_mode = args.op_mode,
                                dl_interval = args.dl_interval,
                                ul_interval = args.ul_interval,
                                no_ue = args.no_ue)

    app_sdk.run_all_apps()
