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
    File name: ue_id_app.py
    Author: Robert Schmidt
    Description: This app assists with UE IDs, mostly related to after-HO UE
    identification (might be extended to joint FlexRAN/LL-MEC operation)
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

class ue_id_app(object):

    name = "ue_id_app"

    def __init__(self, log, sm, url='http://localhost', port='9999', op_mode='test'):
        super(ue_id_app, self).__init__()
        self.url = url + port
        self.log = log
        self.sm  = sm
        self.op_mode = op_mode
        self.ue_gtp_to_imsi = {}
        self.timer = 0
        self.time_expiry = 5

    def update_ue_id(self, bs_id, rnti, teid, imsi):
        data = self.ue_gtp_to_imsi.get(teid)
        if imsi is not None and imsi != "" and imsi != "0" and data is None:
            self.log.info("new UE IMSI " + imsi)
            # if there is a new IMSI and we have no such UE, we assume it is
            # the initial connection
            self.ue_gtp_to_imsi[teid] = { "hist_bs_id" : [],
                                          "hist_rnti" : [],
                                          "bs_id" : bs_id,
                                          "rnti" : rnti,
                                          "imsi" : imsi,
                                          "time" : self.timer
                                        }
        else:
            # no IMSI, check whether GTP is known and update fields if
            # necessary
            if data is None:
                self.log.warn("no data and no IMSI for UE " + str(rnti)
                        + " at BS " + str(bs_id))
            else:
                self.log.info("update UE IMSI " + data["imsi"])
                data["time"] = self.timer
                if bs_id != data["bs_id"] or rnti != data["rnti"]:
                    data["hist_bs_id"] += [data["bs_id"]]
                    data["hist_rnti"] += [data["rnti"]]
                    data["bs_id"] = bs_id
                    data["rnti"] = rnti
                self.ue_gtp_to_imsi[teid] = data

    def monitor_ues(self):
        sm.stats_manager('all')
        self.timer += 1
        for bs in range(0, sm.get_num_enb()):
            bs_id = sm.get_enb_id(bs)
            for ue in range(0, sm.get_num_ue(bs)):
                rnti = sm.get_ue_rnti(bs, ue)
                teid = sm.get_ue_teid_sgw(bs, ue)
                imsi = sm.get_ue_imsi(bs, ue)
                self.log.debug("BS " + str(bs_id) + ", rnti="
                        + str(rnti) + ", teid=" + str(teid) + ", imsi=" + str(imsi))
                self.update_ue_id(bs_id, rnti, teid, imsi)

        self.ue_gtp_to_imsi = { k : v for k, v in self.ue_gtp_to_imsi.iteritems()
                                if self.timer - v['time'] < self.time_expiry }
        self.log.debug(self.ue_gtp_to_imsi)

    def serve_ue_ids(self, client, *args):
        l = []
        for k, v in self.ue_gtp_to_imsi.iteritems():
            v.update({ 'teid_sgw' : k })
            l += [v]
        client.write(json.dumps(l))
        client.set_header("Content-Type", "application/json")

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
                        help='set the App address for open data (HTTP): localhost (default)')
    parser.add_argument('--app-port', metavar='[option]', action='store', type=int,
                        required=False, default=8080,
                        help='set the App port for open data: 8080 (default)')
    parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
                        required=False, default='test',
                        help='Test SDK with already generated json files: test (default), sdk')
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='info',
                        help='set the log level: debug, info (default), warning, error, critical')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args()

    log = flexran_sdk.logger(log_level = args.log,
                             format = "[%(levelname)s] %(message)s").init_logger()

    sm = flexran_sdk.stats_manager(log = log,
                                   url = args.url,
                                   port = args.port,
                                   op_mode = args.op_mode)

    app = ue_id_app(log = log,
                    sm = sm,
                    url = args.url,
                    port = args.port,
                    op_mode = args.op_mode)

    # open data, i.e. exposing an interface to the drone app
    app_open_data = app_sdk.app_builder(log = log,
                                        app = ue_id_app.name,
                                        address = args.app_url,
                                        port = args.app_port)
    app_open_data.add_http_handler("ue_gtp_tracking", get = app.serve_ue_ids)
    app_open_data.run_app()

    tornado.ioloop.PeriodicCallback(lambda: app.monitor_ues(), 1000).start()
    app_sdk.run_all_apps()
