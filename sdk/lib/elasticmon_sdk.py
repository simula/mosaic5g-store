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

""" FlexRAN software development kit (SDK)

    @file: elasticmon_sdk.py
    @author: Dwi Hartati Izaldi
    @brief: Library to get data: average, max, min, sum, count, and range from ElasticSearch
    @version: 1.0
    @date create: 28 June 2019
    @date last modified: 21 August 2019
    Python Version: 2.7
"""

import requests


class url_api(object):

    url_mac_stats = 'http://192.168.12.98:9200/mac_stats/_search'
    url_enb_config = 'http://192.168.12.98:9200/enb_config/_search'


class check_key(object):

    key_mac_stats = ['rnti', 'phr', 'wbcqi', 'rsrp', 'rsrq', 'enb_sfn', 'pdcp_sfn', 'ue_pdcp_pkt', 'ue_pdcp_pkt_bytes',
                     'ue_pdcp_pkt_sn', 'ue_pdcp_pkt_w', 'ue_pdcp_pkt_aiat', 'ue_pdcp_pkt_bytes_w', 'ue_pdcp_pkt_aiat_w',
                     'ue_pdcp_pkt_oo', 'txqueuesize', 'num_ue_lc']
    key_enb_config = ['cell_rb', 'cell_freq', 'cell_power', 'cell_band', 'cell_maxmcs', 'num_enb']


class mac_stats(object):

    def __init__(self, enb, ue, key, t_start, t_end, dir):
        super(mac_stats, self).__init__()
        self.data = []
        self.enb = enb
        self.ue = ue
        self.key = key
        self.t_start = t_start
        self.t_end = t_end
        self.dir = dir
        self.value_list = []
        self.date_list = []
        self.txqueuesize_list = []

        if self.key in check_key.key_mac_stats:
            self.path_key = self.get_path_key()

            requestbody = {"query": {"constant_score": {"filter": {
                "bool": {"must": [{"range": {"date_time": {"gte": "now", "lt": "now"}}},
                                  {"exists": {"field": "mac_stats.mac_stats"}}],
                         "must_not": {"term": {"mac_stats.mac_stats": ""}}}}}},
                "sort": {"date_time": {"order": "desc"}},
                "aggs": {"value_in_range": {
                    "date_range": {"field": "date_time", "ranges": {"from": "now", "to": "now"}},
                    "aggs": {"stats_value": {"stats": {"field": "mac_stats.mac_stats."}}}}}}

            requestbody['query']['constant_score']['filter']['bool']['must'][0]['range']['date_time'][
                'gte'] = "now" + "-" + self.t_start
            requestbody['query']['constant_score']['filter']['bool']['must'][0]['range']['date_time'][
                'lt'] = "now" + "-" + self.t_end
            requestbody['aggs']['value_in_range']['date_range']['ranges']['from'] = "now" + "-" + self.t_start
            requestbody['aggs']['value_in_range']['date_range']['ranges']['to'] = "now" + "-" + self.t_end
            requestbody['aggs']['value_in_range']['aggs']['stats_value']['stats'][
                'field'] = "mac_stats.mac_stats." + self.path_key

            try:
                response = requests.get(url_api.url_mac_stats, headers={'Content-Type': 'application/json'},
                                        data=str(requestbody).replace("'", '"'))
                self.data = response.json()
            except:
                error = self.data['error']['root_cause'][0]['reason']
                return error
        else:
            error = self.data['error']['root_cause'][0]['reason']
            return error

    def get_path_key(self):
        if self.key == 'rnti':
            path = 'rnti'
        elif self.key == 'phr':
            path = 'phr'
        elif self.key == 'wbcqi':
            path = 'dlCqiReport.csiReport.p10csi.wbCqi'
        elif self.key == 'rsrp':
            path = 'rrcMeasurements.pcellRsrp'
        elif self.key == 'rsrq':
            path = 'rrcMeasurements.pcellRsrq'
        elif self.key == 'enb_sfn':
            path = 'dlCqiReport.sfnSn'
        elif self.key == 'pdcp_sfn':
            path = 'pdcpStats.sfn'
        elif self.key == 'ue_pdcp_pkt':
            if self.dir == 'ul':
                path = 'pdcpStats.pktRx'
            else:
                path = 'pdcpStats.pktTx'
        elif self.key == 'ue_pdcp_pkt_bytes':
            if self.dir == 'ul':
                path = 'pdcpStats.pktRxBytes'
            else:
                path = 'pdcpStats.pktTxBytes'
        elif self.key == 'ue_pdcp_pkt_sn':
            if self.dir == 'ul':
                path = 'pdcpStats.pktRxSn'
            else:
                path = 'pdcpStats.pktTxSn'
        elif self.key == 'ue_pdcp_pkt_w':
            if self.dir == 'ul':
                path = 'pdcpStats.pktRxW'
            else:
                path = 'pdcpStats.pktTxW'
        elif self.key == 'ue_pdcp_pkt_aiat':
            if self.dir == 'ul':
                path = 'pdcpStats.pktRxAiat'
            else:
                path = 'pdcpStats.pktTxAiat'
        elif self.key == 'ue_pdcp_pkt_bytes_w':
            if self.dir == 'ul':
                path = 'pdcpStats.pktRxBytesW'
            else:
                path = 'pdcpStats.pktTxBytesW'
        elif self.key == 'ue_pdcp_pkt_aiat_w':
            if self.dir == 'ul':
                path = 'pdcpStats.pktRxAiatW'
            else:
                path = 'pdcpStats.pktTxAiatW'
        elif self.key == 'ue_pdcp_pkt_oo':
            if self.dir == 'ul':
                path = 'pdcpStats.pktRxOo'
            else:
                path = 'pdcpStats.pktRxOo'
        elif self.key == 'txqueuesize':
            path = 'rlcReport.txQueueSize'
        elif self.key == 'num_ue_lc':
            path = 'rlcReport'
        else:
            return 0
        return path

    def get_avg(self):
        return self.data['aggregations']['value_in_range']['buckets'][0]['stats_value']['avg']

    def get_min(self):
        return self.data['aggregations']['value_in_range']['buckets'][0]['stats_value']['min']

    def get_max(self):
        return self.data['aggregations']['value_in_range']['buckets'][0]['stats_value']['max']

    def get_sum(self):
        return self.data['aggregations']['value_in_range']['buckets'][0]['stats_value']['sum']

    def get_count(self):
        return self.data['aggregations']['value_in_range']['buckets'][0]['stats_value']['count']

    def get_range(self, key):
        for i in self.data['hits']['hits']:
            date_time = i['_source']['date_time']
            self.date_list.append(date_time)
            if key == 'rnti':
                value = i['_source']['mac_stats']['rnti']
                self.value_list.append(value)
            elif key == 'phr':
                value = i['_source']['mac_stats']['mac_stats']['phr']
                self.value_list.append(value)
            elif key == 'wbcqi':
                value = i['_source']['mac_stats']['mac_stats']['dlCqiReport']['csiReport'][self.ue]['p10csi']['wbCqi']
                self.value_list.append(value)
            elif key == 'rsrp':
                value = i['_source']['mac_stats']['mac_stats']['rrcMeasurements']['pcellRsrp']
                self.value_list.append(value)
            elif key == 'rsrq':
                value = i['_source']['mac_stats']['mac_stats']['rrcMeasurements']['pcellRsrq']
                self.value_list.append(value)
            elif key == 'enb_sfn':
                value = i['_source']['mac_stats']['mac_stats']['dlCqiReport']['sfnSn']
                self.value_list.append(value)
            elif key == 'enb_pdcp_sfn':
                value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['sfn']
                self.value_list.append(value)
            elif key == 'ue_pdcp_pkt':
                if self.dir == 'ul':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktRx']
                elif self.dir == 'dl':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktTx']
                self.value_list.append(value)
            elif key == 'ue_pdcp_pkt_bytes':
                if self.dir == 'ul':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktRxBytes']
                elif self.dir == 'dl':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktTxBytes']
                self.value_list.append(value)
            elif key == 'ue_pdcp_pkt_sn':
                if self.dir == 'ul':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktRxSn']
                elif self.dir == 'dl':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktTxSn']
                self.value_list.append(value)
            elif key == 'ue_pdcp_pkt_w':
                if self.dir == 'ul':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktRxW']
                elif self.dir == 'dl':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktTxW']
                self.value_list.append(value)
            elif key == 'ue_pdcp_pkt_aiat':
                if self.dir == 'ul':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktRxAiat']
                elif self.dir == 'dl':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktTxAiat']
                self.value_list.append(value)
            elif key == 'ue_pdcp_pkt_bytes_w':
                if self.dir == 'ul':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktRxBytesW']
                elif self.dir == 'dl':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktTxBytesW']
                self.value_list.append(value)
            elif key == 'ue_pdcp_pkt_aiat_w':
                if self.dir == 'ul':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktRxAiatW']
                elif self.dir == 'dl':
                    value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktTxAiatW']
                self.value_list.append(value)
            elif key == 'ue_pdcp_pkt_oo':
                value = i['_source']['mac_stats']['mac_stats']['pdcpStats']['pktRxOo']
                self.value_list.append(value)
            elif key == 'txqueuesize':
                value = i['_source']['mac_stats']['mac_stats']['rlcReport'][0]['txQueueSize']
                self.value_list.append(value)
            elif key == 'num_ue_lc':
                value = i['_source']['mac_stats']['mac_stats']['rlcReport']
                self.value_list.append(len(value))
        # return json.dumps(self.date_list), self.value_list
        return self.value_list

    def get_avg_txqueuesize(self, lc):
        for i in self.data['hits']['hits']:
            value = i['_source']['mac_stats']['mac_stats']['rlcReport'][lc]['txQueueSize']
            self.txqueuesize_list.append(value)
        return sum(self.txqueuesize_list) / len(self.txqueuesize_list)


class enb_config(object):

    def __init__(self, enb, ue, key, t_start, t_end, dir):
        super(enb_config, self).__init__()
        self.data = []
        self.enb = enb
        self.ue = ue
        self.key = key
        self.t_start = t_start
        self.t_end = t_end
        self.dir = dir
        self.value_list = []

        if self.key in check_key.key_enb_config:
            self.path_key = self.get_path_key()

            requestbody = {"query": {"constant_score": {"filter": {"bool": {
                "must": [{"range": {"date_time": {"gte": "now", "lt": "now"}}},
                         {"exists": {"field": "eNB_config"}}],
                "must_not": {"term": {"eNB_config": ""}}}}}}, "sort": {"date_time": {"order": "asc"}}, "aggs": {
                "value_in_range": {"date_range": {"field": "date_time", "ranges": {"from": "now", "to": "now"}},
                                   "aggs": {"stats_value": {"stats": {"field": "eNB_config."}}}}}}
            requestbody['query']['constant_score']['filter']['bool']['must'][0]['range']['date_time'][
                'gte'] = "now" + "-" + self.t_start
            requestbody['query']['constant_score']['filter']['bool']['must'][0]['range']['date_time'][
                'lt'] = "now" + "-" + self.t_end
            requestbody['aggs']['value_in_range']['date_range']['ranges']['from'] = "now" + "-" + self.t_start
            requestbody['aggs']['value_in_range']['date_range']['ranges']['to'] = "now" + "-" + self.t_end
            requestbody['aggs']['value_in_range']['aggs']['stats_value']['stats'][
                'field'] = "eNB_config." + self.path_key

            try:
                response = requests.get(url_api.url_enb_config, headers={'Content-Type': 'application/json'},
                                        data=str(requestbody).replace("'", '"'))
                self.data = response.json()
            except:
                error = self.data['error']['root_cause']['reason']
                return error
        else:
            error = self.data['error']['root_cause'][0]['reason']
            return error

    def get_path_key(self):
        if self.key == 'num_enb':
            path = ''
        elif self.key == 'cell_rb':
            if self.dir == 'ul':
                path = 'eNB.cellConfig.ulBandwidth'
            else:
                path = 'eNB.cellConfig.dlBandwidth'
        elif self.key == 'cell_freq':
            if self.dir == 'ul':
                path = 'eNB.cellConfig.ulFreq'
            else:
                path = 'eNB.cellConfig.dlFreq'
        elif self.key == 'cell_power':
            if self.dir == 'ul':
                path = 'eNB.cellConfig.ulPuschPower'
            else:
                path = 'eNB.cellConfig.dlPdschPower'
        elif self.key == 'cell_band':
            path = 'eNB.cellConfig.eutraBand'
        elif self.key == 'cell_maxmcs':
            path = 'eNB.cellConfig.enable64QAM'
        return path

    def get_avg(self):
        return self.data['aggregations']['value_in_range']['buckets'][0]['stats_value']['avg']

    def get_min(self):
        return self.data['aggregations']['value_in_range']['buckets'][0]['stats_value']['min']

    def get_max(self):
        return self.data['aggregations']['value_in_range']['buckets'][0]['stats_value']['max']

    def get_sum(self):
        return self.data['aggregations']['value_in_range']['buckets'][0]['stats_value']['sum']

    def get_count(self):
        return self.data['aggregations']['value_in_range']['buckets'][0]['stats_value']['count']

    def get_cell_rb(self):
        rb_list = []
        for i in self.data['hits']['hits']:
            if dir == 'ul':
                rb = i['_source']['eNB_config'][self.enb]['eNB']['cellConfig'][self.ue]['ulBandwidth']
                rb_list.append(rb)
            elif dir == 'dl':
                rb = i['_source']['eNB_config'][self.enb]['eNB']['cellConfig'][self.ue]['dlBandwidth']
                rb_list.append(rb)
        return rb_list

    def get_range(self, key):
        for i in self.data['hits']['hits']:
            if key == 'num_enb':
                value = i['_source']['eNB_config']
                self.value_list.append(len(value))
            elif key == 'cell_rb':
                if self.dir == 'ul':
                    value = i['_source']['eNB_config'][self.enb]['eNB']['cellConfig'][self.ue]['ulBandwidth']
                elif self.dir == 'dl':
                    value = i['_source']['eNB_config'][self.enb]['eNB']['cellConfig'][self.ue]['dlBandwidth']
                self.value_list.append(value)
            elif key == 'cell_freq':
                if self.dir == 'ul':
                    value = i['_source']['eNB_config'][self.enb]['eNB']['cellConfig'][self.ue]['ulFreq']
                elif self.dir == 'dl':
                    value = i['_source']['eNB_config'][self.enb]['eNB']['cellConfig'][self.ue]['dlFreq']
                self.value_list.append(value)
            elif key == 'cell_power':
                if self.dir == 'ul':
                    value = i['_source']['eNB_config'][self.enb]['eNB']['cellConfig'][self.ue]['ulPuschPower']
                elif self.dir == 'dl':
                    value = i['_source']['eNB_config'][self.enb]['eNB']['cellConfig'][self.ue]['dlPdschPower']
                self.value_list.append(value)
            elif key == 'cell_band':
                value = i['_source']['eNB_config'][self.enb]['eNB']['cellConfig'][self.ue]['eutraBand']
                self.value_list.append(value)
            elif key == 'cell_maxmcs':
                if self.dir == 'dl':
                    value = 28
                elif i['_source']['eNB_config'][self.enb]['eNB']['cellConfig'][self.ue]['enable64QAM'] == 0:
                    value = 16
                else:
                    value = 28
                self.value_list.append(value)
        return self.value_list
