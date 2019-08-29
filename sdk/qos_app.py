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
  File name: qos_app.py
  Author: Dwi Hartati Izaldi - hartati@eurecom.fr
  Description: This app dynamically get the statistic from elasticmon sdk, calculate and monitor the throughput
  version: 1.0
  Date created: 7 August 2019
  Date last modified: 29 August 2017
  Python Version: 2.7

"""


from lib import elasticmon_sdk
from lib import app_sdk
import rrm_app_vars
from lib import flexran_sdk
import json
import argparse
import socket
import requests
import tornado.ioloop
import tornado.web
import time


ElasticMON_URL = "192.168.12.98:9200"
url_flexran = "http://192.168.12.98:9999"


class qos_app(object):
    name = 'qos app'

    # UE vars
    ue_dlwcqi = []
    ue_avg_dlwcqi = 0
    ue_phr = ''
    ue_rnti = []
    ue_dlmcs = ''
    ue_dlrb = 0
    ue_dltbs = {}
    ue_lc_txqsize = ''

    lc_ue_dltbs = {}
    lc_ue_dlrb = {}

    # ENB vars
    enb_available_dlrb = 0
    enb_avg_dlrb = 0
    enb_dlrb = ''

    slice_dlrb_share = {}

    # variable to monitor, it means that it will monitor per 10 seconds and the direction is downlink.
    # The threshold of wbcqi is 5
    start = '10s'
    end = '0s'
    dir = 'dl'
    threshold_wbcqi = 12
    lc = 0

    def get_statistic(self):
        cqi_stats = elasticmon_sdk.mac_stats(enb=0, ue=0, key='wbcqi', t_start=qos_app.start, t_end=qos_app.end,
                                             dir=qos_app.dir)
        rnti_stats = elasticmon_sdk.mac_stats(enb=0, ue=0, key='rnti', t_start=qos_app.start, t_end=qos_app.end,
                                              dir=qos_app.dir)
        rb_config = elasticmon_sdk.enb_config(enb=0, ue=0, key='cell_rb', t_start=qos_app.start, t_end=qos_app.end,
                                              dir=qos_app.dir)
        txqsize_stats = elasticmon_sdk.mac_stats(enb=0, ue=0, key='txqueuesize', t_start=qos_app.start,
                                                 t_end=qos_app.end, dir=qos_app.dir)
        try:
            qos_app.ue_dlwcqi = cqi_stats.get_range('wbcqi')
            qos_app.ue_avg_dlwcqi = int(cqi_stats.get_avg())
            qos_app.ue_rnti = rnti_stats.get_range('rnti')
            qos_app.enb_dlrb = int(rb_config.get_avg())
            qos_app.ue_lc_txqsize = txqsize_stats.get_avg_txqueuesize(qos_app.lc)
            #print "avg dlwcqi is " + str(qos_app.ue_avg_dlwcqi)
            #print "range of rnti is " + str(qos_app.ue_rnti)
            #print "enb dlrb is " + str(qos_app.enb_dlrb)
            #print "ue lc txqsize is " + str(qos_app.ue_lc_txqsize)
        except:
            pass

    def update_slice(self, percentage=5):
        if (qos_app.slice_dlrb_share != percentage) or (qos_app.slice_dlrb_share == ''):
            slice_percentage = 'percentage:' + str(percentage)
            print slice_percentage

            policy = {}
            policy['dl'] = []

            policy['dl'].append('id:0')
            policy['dl'].append('label:xmbb')
            policy['dl'].append(slice_percentage)

            enb_id = 0
            print json.dumps(policy)
            # rrm.rrm_apply_policy(enb=enb_id, policy=policy)
        else:
            print "None action taken"

    def associate_ue(self):
        rrm.associate_ues_slices(0, qos_app.ue_rnti[0])

    def monitor_ue_qos(self):
        # read
        print "monitor ue qos function got cqi range is "
        print qos_app.ue_dlwcqi
        # wait sometime to have a value inside the time range
        if len(self.ue_dlwcqi) != 0:
            # compare with threshold
            # decision to update or not the slice RB by K PRB --> set  slice_dlrb_share to a new percentage
            for a, b in zip(qos_app.ue_dlwcqi, qos_app.ue_dlwcqi[1:]):
                if b < qos_app.threshold_wbcqi:
                    dif = a-b
                    if dif == 2:
                        prtg = 10
                    elif dif == 3:
                        prtg = 15
                    else:
                        prtg = 20
                    self.update_slice(percentage=prtg)
                    break
                else:
                    print "Relax, everything is under control"
        else:
            print "None data within this period"

    def calculate_req_rb(self):
        qos_app.enb_available_dlrb = qos_app.enb_dlrb # following the rrm_kpi_app code
        qos_app.ue_dlrb = 0 # following the rrm_kpi_app code
        qos_app.lc_ue_dlrb = 2 # following the rrm_kpi_app code
        qos_app.ue_dlmcs = rrm_app_vars.cqi_to_mcs[qos_app.ue_avg_dlwcqi]
        dl_itbs = rrm_app_vars.mcs_to_itbs[qos_app.ue_dlmcs]
        qos_app.lc_ue_dltbs = rrm_app_vars.tbs_table[dl_itbs][qos_app.lc_ue_dlrb]
        while qos_app.ue_lc_txqsize > qos_app.lc_ue_dltbs:
            if qos_app.lc_ue_dlrb > qos_app.enb_available_dlrb:
                print "no available dlrb"
                break
            qos_app.lc_ue_dlrb += 2
            qos_app.lc_ue_dltbs = rrm_app_vars.tbs_table[dl_itbs][qos_app.lc_ue_dlrb]

        qos_app.ue_dlrb += qos_app.lc_ue_dlrb
        qos_app.enb_available_dlrb -= qos_app.ue_dlrb

    def calculate_throughput(self):
        qos_app.enb_available_dlrb = qos_app.enb_dlrb
        qos_app.lc_ue_dlrb = 2 # following the rrm_kpi_app code
        qos_app.ue_dlrb = 100 # assume following the default value

        # required RB for DL
        qos_app.ue_dlmcs = rrm_app_vars.cqi_to_mcs[qos_app.ue_avg_dlwcqi]
        dl_itbs = rrm_app_vars.mcs_to_itbs[qos_app.ue_dlmcs]
        qos_app.lc_ue_dltbs = rrm_app_vars.tbs_table[dl_itbs][qos_app.lc_ue_dlrb]

        # calculate the throughput
        qos_app.ue_dlrb += qos_app.lc_ue_dlrb
        qos_app.ue_dltbs = rrm_app_vars.tbs_table[dl_itbs][qos_app.ue_dlrb]
        throughput = float(qos_app.ue_dltbs/1000.0)

        print "value of Itbs is " + str(dl_itbs)
        print "value of DL Tbs is " + str(qos_app.ue_dltbs)
        print "value of DL RB is " + str(qos_app.ue_dlrb)
        print "value of MCS is " + str(qos_app.ue_dlmcs)
        print "average throughput value over the last 10 seconds is " + str(throughput) + " Mbps"

    def run(self):
        print "------------------------------"
        run_app = qos_app()
        # run_app.test_list()
        run_app.get_statistic()
        run_app.update_slice(percentage=5)
        ## run_app.associate_ue()
        run_app.monitor_ue_qos()
        run_app.calculate_throughput()

    def handle_new_client(self, client):
        client.send_notification('capabilities', qos_app.open_data_capabilities)

    def open_data_load_status(self, params):
        pass

    def open_data_save_status(self):
        pass

    def handle_message(self, client, id, method, params, message):
        pass

    def handle_notification(self, client, method, params, message):
        if method == 'capabilities':
            client.send_notification(method, self.open_data_capabilities)
            #      client.send_notification('get-list', self.open_data_all_options)

    open_data_capabilities = {
        'get-list': {'help': 'Get the current list'},
        'update-slices': {
            'help': 'Create a slice given a policy',
            'schema': [
                {'name': 'enb_id', 'type': 'number', 'choice': ['#ENBID'], 'help': 'Select eNB'},
                {'name': 'dl_slice', 'array': {'length': 1, 'schema': [{'name': 'id', 'type': 'number'},
                                                                       {'name': 'percentage',
                                                                        'range': [0, 0, 100, 1]}]},
                 'help': 'Create DL Slice'},
                {'name': 'ul_slice', 'array': {'length': 1, 'schema': [{'name': 'id', 'type': 'number'},
                                                                       {'name': 'percentage',
                                                                        'range': [0, 0, 100, 1]},
                                                                       {'name': 'firstRb', 'type': 'number'}]},
                 'help': 'Create UL Slice'},
                {'name': 'intersliceShareActive', 'type': 'boolean', 'choice': ['True', 'False'],
                 'help': 'Enable Resource Sharing'}
            ]
        },
        'ue-slices': {
            'help': 'Associate a UE to a slice in DL and UL',
            'schema': [
                {'name': 'enb_id', 'type': 'number', 'choice': ['#ENBID'], 'help': 'Select eNB'},
                {'name': 'ue_id', 'type': 'number', 'choice': ['#UEID'], 'help': 'Select UE'},
                {'name': 'dl_slice', 'type': 'number', 'choice': ['#DLSLICE'], 'help': 'Select DL Slice'},
                {'name': 'ul_slice', 'type': 'number', 'choice': ['#ULSLICE'], 'help': 'Select UL Slice'}
            ],
        },
        'delete slices': {
            'help': 'remove existing slices',
            'schema': [
                {'name': 'enb_id', 'type': 'number', 'choice': ['#ENBID'], 'help': 'Select eNB'},
                {'name': 'dl_slice', 'type': 'number', 'checkbox': ['#DLSLICE'], 'help': 'Select DL Slice'},
                {'name': 'ul_slice', 'type': 'number', 'checkbox': ['#ULSLICE'], 'help': 'Select UL Slice'}
            ]
        }
    }


if __name__ == '__main__':

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect = sock.connect_ex(('192.168.12.98', 9999))
    if connect == 0:
        sock.close()
        print "FlexRAN is running"
        req = requests.get(url_flexran + '/elasticmon')
        json_data = json.loads(req.text)
        flex_producer = str(json_data['active'])
        endpoint = json_data['endpoint']
        response = {}

        if not any(ElasticMON_URL in s for s in endpoint):
            req = requests.post(url_flexran + '/elasticmon/endpoint/' + ElasticMON_URL)
            print "ElasticSearch endpoint has been added to FlexRAN"
        else:
            print "ElasticSearch endpoint exists in FlexRAN"

        if flex_producer == 'False':
            req_enable = requests.post(url_flexran + '/elasticmon/enable')
            if req_enable.status_code == 200:
                print "OK"
            else:
                print json.dumps(response), 400
        else:
            print "FlexRAN producer has been activated"

    else:
        sock.close()
        print "Make sure FlexRAN is running!"

    # wait for flexRAN producer produce enough data to Elastic
    time.sleep(5)

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost',
                        help='set the FlexRAN RTC URL: loalhost (default)')
    parser.add_argument('--app-url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost',
                        help='set the App address to open data: loalhost (default)')
    parser.add_argument('--port', metavar='[option]', action='store', type=str,
                        required=False, default='9999',
                        help='set the FlexRAN RTC port: 9999 (default)')
    parser.add_argument('--app-port', metavar='[option]', action='store', type=int,
                        required=False, default=8080,
                        help='set the App port to open data: 8080 (default)')
    parser.add_argument('--template', metavar='[option]', action='store', type=str,
                        required=False, default='template_1',
                        help='set the slice template to indicate the type of each slice: template_1(default), .... template_4')
    parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
                        required=False, default='sdk',
                        help='Set the app operation mode either with FlexRAN or with the test json files: test, sdk(default)')
    parser.add_argument('--log', metavar='[level]', action='store', type=str,
                        required=False, default='info',
                        help='set the log level: debug, info (default), warning, error, critical')
    parser.add_argument('--period', metavar='[option]', action='store', type=int,
                        required=False, default=10,
                        help='set the period of the app: 1s (default)')

    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()

    qos_app.period = args.period

    log = flexran_sdk.logger(log_level=args.log).init_logger()

    rrm = flexran_sdk.rrm_policy(log=args.log, url=args.url, port=args.port, op_mode=args.op_mode)

    app_open_data = app_sdk.app_builder(log=log, app=qos_app.name, address=args.url, port=args.port)

    qos_open_data = app_sdk.app_handler(qos_app.name, log=log, callback=qos_app.handle_message,
                                        notification=qos_app.handle_notification, init=qos_app.handle_new_client,
                                        save=qos_app.open_data_save_status, load=qos_app.open_data_load_status)

    app_open_data.add_options("qos", handler=qos_open_data)

    app_open_data.run_app()

    log.info('Starting periodic for ' + str(qos_app.period) + ' seconds...')

    init = qos_app()
    tornado.ioloop.PeriodicCallback(lambda: init.run(), qos_app.period * 1000).start()
    app_sdk.run_all_apps()
