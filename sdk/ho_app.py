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
    File name: ho_app.py
    Author: Robert Schmidt
    Description: This app assists in handling network-initiated handovers
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

class ue_prb_share():
    def __init__(self, time, dl_prbs, dl_share, ul_prbs, ul_share):
        self.time = time
        self.dl_prbs = dl_prbs
        self.dl_share = dl_share
        self.ul_prbs = ul_prbs
        self.ul_share = ul_share

class ho_app(object):

    name = "ho_app"
    odata_capabilities = 'capabilities'
    odata_refresh = 'Refresh'
    odata_ho      = 'Handover'
    odata_ho_sbs  = 'Source BS'
    odata_ho_ue   = 'UE'
    odata_ho_tbs  = 'Target BS'
    odata_netcontrol = "X2 HO NetControl"
    odata_pingpong = "Ping-Pong"
    open_data = {
        odata_refresh: { 'help': 'Refresh the current list' },
        odata_ho: {
            'help': 'Perform a HO for a UE from source to target BS',
            'schema' : [
                {
                    'name': odata_ho_sbs,
                    'type': 'number',
                    'choice': ['#ENBID'],
                    'help': 'Select source BS'
                },
                {
                    'name': odata_ho_ue,
                    'type': 'number',
                    'choice': [], # filled in handle_message()
                    'help': 'Select UE'
                },
                {
                    'name': odata_ho_tbs,
                    'type': 'number',
                    'choice': ['#ENBID'],
                    'help': 'Select target BS'
                }
            ]
        },
        odata_netcontrol: {
            'help': 'Switch X2 HO NetControl. If true, HO are only triggered through the control. If false, UE HO requests are followed.',
            'schema': [
                {
                    'name': 'BS',
                    'type': 'number',
                    'checkbox': ['#ENBID'],
                    'help': 'Select BS'
                },
                {
                    'name': 'NetControl',
                    'type': 'bool',
                    'choice': [True, False]
                }
            ]
        },
        odata_pingpong: {
            'help': 'Handover users in ping-pong fashion.',
            'schema': [
                {
                    'name': 'Periodicity',
                    'type': 'string',
                    'choice': ['Off', '5s', '10s', '20s'],
                    'help': 'Select periodicity for ping-pong HO events.'
                }
            ]
        }
    }

    def __init__(self, log, sm, rrc, url='http://localhost', port='9999', op_mode='test'):
        super(ho_app, self).__init__()

        self.url = url+port
        self.log = log
        self.sm  = sm
        self.rrc = rrc
        self.op_mode = op_mode
        self.ue_load = {}
        self.clients = [] # list of clients, used to push notifications of new UEs
        self.last_e = 0
        self.ho_cmd_text = []
        self.ho_cmd_text_timeout = 0
        self.pingpong = None
        self.pingpong_text = ["Ping-Pong Off"]

    @staticmethod
    def inc_calc_share(num_rb, time_diff, used_rbs):
        """!@brief calculate share of resources
        @param num_rb: system bandwidth
        @param time_diff: difference since last call, in ms
        @param used_rbs: used RBs by a user/system
        """
        if time_diff == 0:
            return 0.0
        else:
            return used_rbs / (num_rb * time_diff)

    def clean_structures(self):
        """!@brief remove BSs that are kept internally but are not present
        anymore. BS/UE new to add is handled in update_load
        """
        # count number of all UEs
        ues = sum([len (u) for u in self.ue_load.values()])

        # retain all BSs in the map that are present in the sm
        bs_list = sm.get_enb_id_list()
        self.ue_load = { k:v for k,v in self.ue_load.items() if k in bs_list }

        # retain all UEs in the map that are present in the sm
        # loop over index of eNB, but since an eNB might not be added yet, we
        # skip it in that case
        for e in range(0, sm.get_num_enb()):
            bs_id = sm.get_enb_id(e)
            # skip this BS if it is not present internally yet
            if bs_id not in self.ue_load.keys():
                continue
            rntis = sm.get_rnti_list(e)
            self.ue_load[bs_id] = { k:v for k,v in self.ue_load[bs_id].items() if k in rntis }

        # notify if UEs were removed
        ues2 = sum([len (u) for u in self.ue_load.values()])
        if ues - ues2 > 0:
            self.notify_ues()

    def enable_x2_ho_net_control(self):
        """!@brief enable X2 HO net control on all new BSs and create it if
        necessary
        """
        for e in range(0, sm.get_num_enb()):
            bs_id = sm.get_enb_id(e)
            if not bs_id in self.ue_load:
                self.ue_load[bs_id] = {}
                self.rrc.switch_x2_ho_net_control(bs_id, True)
                self.log.info("new BS " + str(bs_id) + ", enable X2 HO NetControl")

    def update_load(self):
        for e in range(0, sm.get_num_enb()):
            bs_id = sm.get_enb_id(e)
            rbs = sm.get_cell_rb(e)
            for u in range(0, sm.get_num_ue(e)):
                rnti = sm.get_ue_rnti(e, u)
                time = sm.get_enb_sfn(e, u)
                total_rb_dl = sm.get_ue_total_prb(e,u,'dl')
                total_rb_ul = sm.get_ue_total_prb(e,u,'ul')
                if not rnti in self.ue_load[bs_id]:
                    self.ue_load[bs_id][rnti] = ue_prb_share(time, total_rb_dl, 0.0, total_rb_ul, 0.0)
                    self.notify_ues()
                else:
                    # get the PRB difference in UL/DL since last call
                    ddl = total_rb_dl - self.ue_load[bs_id][rnti].dl_prbs
                    self.ue_load[bs_id][rnti].dl_prbs = total_rb_dl
                    dul = total_rb_ul - self.ue_load[bs_id][rnti].ul_prbs
                    self.ue_load[bs_id][rnti].ul_prbs = total_rb_ul

                    # Get the time difference since the last call
                    #dt = time - self.ue_load[bs_id][rnti].time
                    dt = 1000
                    self.ue_load[bs_id][rnti].time = time

                    # calculate moving average for the DL/UL share
                    self.ue_load[bs_id][rnti].dl_share = ho_app.inc_calc_share(rbs, dt, ddl)
                    self.ue_load[bs_id][rnti].ul_share = ho_app.inc_calc_share(rbs, dt, dul)

                    log.debug("dt=" + str(dt) + ", ddl=" + str(ddl) + ", dul=" + str(dul))

    def send_load(self):
        text = []
        if len(self.ue_load) > 0:
            text += ["BS load:"]
        for bs_id in self.ue_load:
            dl = sum([self.ue_load[bs_id][u].dl_share for u in self.ue_load[bs_id].keys()])
            text += [str(bs_id) + "=%.1f" % (dl * 100) + " %"]
        if len(self.ho_cmd_text) > 0:
            text += self.ho_cmd_text
            self.ho_cmd_text_timeout -= 1
            if self.ho_cmd_text_timeout == 0:
                self.ho_cmd_text = []
        else:
            text += self.pingpong_text

        for client in self.clients:
            client.send_notification('app_info', text)

    def print_resources(self):
        for bs_id in self.ue_load:
            ul = 0
            dl = 0
            for ue_id in self.ue_load[bs_id]:
                log.info("  UE " + str(ue_id) + ": DL load " + str(self.ue_load[bs_id][ue_id].dl_share))
                log.info("  UE " + str(ue_id) + ": UL load " + str(self.ue_load[bs_id][ue_id].ul_share))
                dl += self.ue_load[bs_id][ue_id].dl_share
                ul += self.ue_load[bs_id][ue_id].ul_share
            log.info("eNB " + str(bs_id) + ": DL load " + str(dl))
            log.info("eNB " + str(bs_id) + ": UL load " + str(ul))

    def log_data(self):
        # log the most important values: phys cell Id, neighboring cells, RBs,
        # timediff for resource usage, etc
        for e in range(0, sm.get_num_enb()):
            log.info('*****************************')
            log.info('enb=' + str(e))
            log.info('num RBs=' + str(sm.get_cell_rb(e)))
            log.info('phyCellId=' + str(sm.get_phy_cell_id(e)))
            log.info('x2HoNetCtrl=' + str(sm.get_x2_ho_net_controlled(e)))
            for u in range(0, sm.get_num_ue(e)):
                log.info(' > ue=' + str(u))
                log.info('   rnti=' + str(sm.get_ue_rnti(e,u)))
                log.info('   neighCells=' + str(sm.get_ue_neighboring_cells(e,u)))
                log.info('   RSRQ=' + str(sm.get_ue_rsrq(e,u)))
                log.info('   RSRP=' + str(sm.get_ue_rsrp(e,u)))
                log.info('   totalPrbDl=' + str(sm.get_ue_total_prb(e,u,'dl')))
                log.info('   totalPrbUl=' + str(sm.get_ue_total_prb(e,u,'ul')))
                log.info('   sfnSn=' + str(sm.get_enb_sfn(e,u)))
            log.info('*****************************')

    def monitor_resources(self):
        sm.stats_manager('all')
        # compare internal state to stats manager and remove/add BSs/UEs that
        # were not present before.
        self.clean_structures()
        # automatically enable X2 HO Network control on all new BSs
        self.enable_x2_ho_net_control()
        #self.log_data()
        self.update_load()
        #self.print_resources()
        self.send_load()

    def ping_pong(self):
        """!@brief search for the first UE in the first BS (i.e. empty BSs are
        skipped). Then, check the next free BS that is in this UE's neighboring
        cells and issue a handover command. If there are two BS with one UE,
        then this will result in a ping-pong type of handover
        """
        # find the first UE in the BS visited last
        found = False
        e = 0
        for ne in range(0, sm.get_num_enb()):
            e = (ne + self.last_e) % sm.get_num_enb()
            s_bs_id = sm.get_enb_id(e)
            if sm.get_num_ue(e) > 0:
                rnti = sm.get_ue_rnti(e, 0)
                teid = sm.get_ue_teid_sgw(e, 0)
                found = True
                break
        if not found:
            self.log.warn("no UE to handover")
            return
        self.last_e = e
        neigh = sm.get_ue_neighboring_cells(e, 0)
        # check all BS, starting after the source BS
        for f in range(0, sm.get_num_enb() - 1):
            nx = (f + e + 1) % sm.get_num_enb() # start from e + until before e again (rotate list)
            phyCellId = sm.get_phy_cell_id(nx)
            # is this BS in the UEs neighboring list? Fire!! (well, HO)
            if phyCellId in neigh:
                self.ho_cmd_text = [
                    "HO: UE " + str(rnti) + "/TEID " + str(teid),
                    "from BS " + str(s_bs_id) + " to BS " + str(sm.get_enb_id(nx))
                ]
                self.ho_cmd_text_timeout = 3
                self.rrc.trigger_ho(s_bs_id, rnti, sm.get_enb_id(nx))
                return

        self.log.warn("no suitable BS to handover in neighboring cells with phyCellIds " + str(neigh))

    def handle_new_client(self, client):
        log.info(self.handle_new_client.__name__ + "()")
        self.clients.append(client)
        client.send_notification(ho_app.odata_capabilities, ho_app.open_data)

    def handle_term_client(self, client):
        self.clients.remove(client)

    def open_data_load_status(self, params):
        pass

    def open_data_save_status(self):
        pass

    def handle_message(self, client, id, method, params, message):
        log.info(self.handle_message.__name__ + "(): method '" + method
                    + "', message '" + str(message) + "'")
        if   (method == ho_app.odata_refresh or
                method == ho_app.odata_capabilities):
            self.update_odata_capabilities_ue()
            client.send_notification(ho_app.odata_capabilities, ho_app.open_data)
        elif (method == ho_app.odata_ho):
            self.handle_message_ho(client, id, method, params, message)
        elif (method == ho_app.odata_netcontrol):
            self.handle_message_netcontrol(client, id, method, params, message)
        elif (method == ho_app.odata_pingpong):
            self.handle_message_pingpong(client, id, method, params, message)

    def update_odata_capabilities_ue(self):
        ho_app.open_data[self.odata_ho]['schema'][1]['choice'] = []
        for e in range(0, sm.get_num_enb()):
            ho_app.open_data[self.odata_ho]['schema'][1]['choice'] += [
                str(sm.get_ue_rnti(e, u)) + ' (' + str(sm.get_ue_teid_sgw(e, u)) + ')'
                for u in range(0, sm.get_num_ue(e)) ]

    def handle_message_ho(self, client, id, method, params, message):
        if (ho_app.odata_ho_sbs not in params):
            log.error('no ' + ho_app.odata_ho_sbs + ' in params')
            return
        if (ho_app.odata_ho_ue not in params):
            log.error('no ' + ho_app.odata_ho_ue + ' in params')
            return
        if (ho_app.odata_ho_tbs not in params):
            log.error('no ' + ho_app.odata_ho_tbs + ' in params')
            return
        self.rrc.trigger_ho(params[ho_app.odata_ho_sbs],
                            params[ho_app.odata_ho_ue],
                            params[ho_app.odata_ho_tbs])

    def handle_message_netcontrol(self, client, id, method, params, message):
        if 'BS' not in params:
            log.error('no BS in params')
            return
        if 'NetControl' not in params:
            log.error('no NetControl in params')
            return
        for bs in params['BS']:
            self.rrc.switch_x2_ho_net_control(bs, params['NetControl'] == 'true')


    def notify_ues(self):
        self.update_odata_capabilities_ue()
        for client in self.clients:
            client.send_notification(ho_app.odata_capabilities, ho_app.open_data)

    def handle_notification(self, client, method, params, message):
        log.info(self.handle_notification.__name__ + "(): method '" + method
                    + "', message '" + str(message) + "'")
        if method == ho_app.odata_capabilities:
            client.send_notification(method, ho_app.open_data)

    def handle_message_pingpong(self, client, id, method, params, message):
        log.info(self.handle_message_pingpong.__name__)
        if 'Periodicity' not in params:
            log.error('no Periodicity in params')
            return
        if params['Periodicity'] == 'Off':
            self.stop_pingpong()
        elif params['Periodicity'] == '5s':
            self.start_pingpong(5)
        elif params['Periodicity'] == '10s':
            self.start_pingpong(10)
        elif params['Periodicity'] == '20s':
            self.start_pingpong(20)
        pass

    def start_pingpong(self, interval_s):
        self.stop_pingpong()
        self.pingpong = tornado.ioloop.PeriodicCallback(lambda: app.ping_pong(), interval_s * 1000)
        self.pingpong.start()
        self.pingpong_text = ["Ping-Pong every " + str(interval_s) + "s"]

    def stop_pingpong(self):
        self.pingpong_text = ["Ping-Pong Off"]
        if self.pingpong is not None:
            self.pingpong.stop()
            self.pingpong = None

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
    parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
                        required=False, default='test',
                        help='Test SDK with already generated json files: test (default), sdk')
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='info',
                        help='set the log level: debug, info (default), warning, error, critical')
    parser.add_argument('--ping-pong-interval', metavar='[level]', action='store', type=int,
                        required=False, default=0,
                        help='set the interval at which the first UE in the first BS should be handed over to the second free BS.  Default 0 is switched off')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args()

    log = flexran_sdk.logger(log_level=args.log,
                             format="[%(levelname)s] %(message)s").init_logger()

    sm = flexran_sdk.stats_manager(log = log,
                                   url = args.url,
                                   port = args.port,
                                   op_mode = args.op_mode)
    sm.stats_manager('all')
    rrc = flexran_sdk.rrc_trigger_meas(log = log,
                                       url = args.url,
                                       port = args.port,
                                       op_mode = args.op_mode)

    app = ho_app(log = log,
                 sm = sm,
                 rrc = rrc,
                 url = args.url,
                 port = args.port,
                 op_mode = args.op_mode)


    # open data, i.e. exposing an interface to the drone app
    app_open_data=app_sdk.app_builder(log=log,
                                      app=ho_app.name,
                                      address=args.app_url,
                                      port=args.app_port)
    ho_open_data = app_sdk.app_handler(ho_app.name,
                                       log = log,
                                       callback = app.handle_message,
                                       notification = app.handle_notification,
                                       init = app.handle_new_client,
                                       save = app.open_data_save_status,
                                       load = app.open_data_load_status,
                                       term = app.handle_term_client)

    app_open_data.add_options("list", handler=ho_open_data)
    app_open_data.run_app()

    if args.ping_pong_interval > 0:
        app.start_pingpong(args.ping_pong_interval)
    tornado.ioloop.PeriodicCallback(lambda: app.monitor_resources(), 1000).start()
    app_sdk.run_all_apps()
