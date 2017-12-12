'''
   The MIT License (MIT)

   Copyright (c) 2017

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:
   
   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.
   
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.
'''

'''
    File name: te_app.py
    Author: navid nikaein
    Description: This app triggers an external event based on the predefined threshold through FLEXRAN SDK
    version: 1.0
    Date created: 7 July 2017
    Date last modified: 7 July 2017 
    Python Version: 2.7
    
'''



import json
# Make it work for Python 2+3 and with Unicode
import io
import requests
import time
import logging
import argparse
import os
import pprint
import sys 
from sys import *

from array import *
from threading import Timer
from time import sleep

import rrm_app_vars

from lib import flexran_sdk 
from lib import logger

import signal

def sigint_handler(signum,frame):
    print 'Exiting, wait for the timer to expire... Bye'
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

class monitoring_app(object):
    """trigger external events happend in the underlying RAN
    """
    # stats vars
    enb_sfn={}
    # pdcp
    enb_ue_pdcp_tx={}
    enb_ue_pdcp_tx_bytes={}
    enb_ue_pdcp_tx_sn={}
    enb_ue_pdcp_tx_aiat={}
    enb_ue_pdcp_tx_rate_s={}
    enb_ue_pdcp_tx_throughput_s={}
    enb_ue_pdcp_tx_aiat_s={}



    enb_pdcp_tx={}
    enb_pdcp_tx_bytes={}
    enb_pdcp_tx_sn={}
    enb_pdcp_tx_aiat={}
    enb_pdcp_tx_rate_s={}
    enb_pdcp_tx_throughput_s={}
    enb_pdcp_tx_aiat_s={}

    enb_ue_pdcp_rx={}
    enb_ue_pdcp_rx_bytes={}
    enb_ue_pdcp_rx_sn={}
    enb_ue_pdcp_rx_aiat={}
    enb_ue_pdcp_rx_rate_s={}
    enb_ue_pdcp_rx_goodput_s={}
    enb_ue_pdcp_rx_aiat_s={}
    enb_ue_pdcp_rx_oo={}

    enb_pdcp_rx={}
    enb_pdcp_rx_bytes={}
    enb_pdcp_rx_sn={}
    enb_pdcp_rx_aiat={}
    enb_pdcp_rx_rate_s={}
    enb_pdcp_rx_goodput_s={}
    enb_pdcp_rx_aiat_s={}
    enb_pdcp_rx_oo={}
    #RRC
    enb_ue_rsrp={}
    enb_ue_rsrq={}
    enb_ue_trigger_meas={}
    # MAC
    enb_ulrb={}
    enb_dlrb={}
    enb_ulmaxmcs={}
    enb_dlmaxmcs={}

    ue_dlwcqi={}
        
    ue_phr={}

    lc_ue_bsr={}
    lc_ue_report={}

    # 

    def __init__(self, log, url='http://localhost',port='9999',url_app='http://localhost',port_app='9090', log_level='info', op_mode='test'):
        super(monitoring_app, self).__init__()
        
        self.url = url+':'+port
        self.log = log
        self.log_level = log_level
        self.status = 'none'
        self.op_mode = op_mode
        
        
    def get_statistics(self, sm):
            
        for enb in range(0, sm.get_num_enb()) :
            monitoring_app.enb_ue_trigger_meas[enb]=1
            
            monitoring_app.enb_pdcp_tx[enb]=0
            monitoring_app.enb_pdcp_tx_bytes[enb]=0
            monitoring_app.enb_pdcp_tx_sn[enb]=0
            monitoring_app.enb_pdcp_tx_aiat[enb]=0
            monitoring_app.enb_pdcp_tx_rate_s[enb]=0
            monitoring_app.enb_pdcp_tx_throughput_s[enb]=0
            monitoring_app.enb_pdcp_tx_aiat_s[enb]=0

            monitoring_app.enb_pdcp_rx[enb]=0
            monitoring_app.enb_pdcp_rx_bytes[enb]=0
            monitoring_app.enb_pdcp_rx_sn[enb]=0
            monitoring_app.enb_pdcp_rx_aiat[enb]=0
            monitoring_app.enb_pdcp_rx_rate_s[enb]=0
            monitoring_app.enb_pdcp_rx_goodput_s[enb]=0
            monitoring_app.enb_pdcp_rx_aiat_s[enb] = 0
            monitoring_app.enb_pdcp_rx_oo[enb] = 0


            monitoring_app.enb_dlrb[enb] = sm.get_cell_rb(enb,dir='DL')
            monitoring_app.enb_ulrb[enb] = sm.get_cell_rb(enb,dir='UL')
            monitoring_app.enb_ulmaxmcs[enb] = sm.get_cell_maxmcs(enb,dir='UL')
            monitoring_app.enb_dlmaxmcs[enb] = sm.get_cell_maxmcs(enb,dir='DL')

            log.info('Num UE ' + str(sm.get_num_ue(enb=enb)))
            
            for ue in range(0, sm.get_num_ue(enb=enb)) :
          	monitoring_app.enb_sfn[enb,ue]  = sm.get_enb_sfn(enb,ue)
		monitoring_app.ue_dlwcqi[enb,ue]=sm.get_ue_dlwbcqi(enb,ue)
                monitoring_app.ue_phr[enb,ue] =sm.get_ue_phr(enb,ue)
                                                
                # per eNB UE stats 
                monitoring_app.enb_ue_pdcp_tx[enb,ue]=sm.get_ue_pdcp_pkt(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_bytes[enb,ue]=sm.get_ue_pdcp_pkt_bytes(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_sn[enb,ue]=sm.get_ue_pdcp_pkt_sn(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_aiat[enb,ue]=sm.get_ue_pdcp_pkt_aiat(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_rate_s[enb,ue]=sm.get_ue_pdcp_pkt_rate_per_s(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_throughput_s[enb,ue] = sm.get_ue_pdcp_pkt_throughput(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_aiat_s[enb,ue]= sm.get_ue_pdcp_pkt_aiat_s(enb,ue, 'dl')

                monitoring_app.enb_ue_pdcp_rx[enb,ue]=sm.get_ue_pdcp_pkt(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_bytes[enb,ue]=sm.get_ue_pdcp_pkt_bytes(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_sn[enb,ue]=sm.get_ue_pdcp_pkt_sn(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_aiat[enb,ue]=sm.get_ue_pdcp_pkt_aiat(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_rate_s[enb,ue]=sm.get_ue_pdcp_pkt_rate_per_s(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_goodput_s[enb,ue] = sm.get_ue_pdcp_pkt_throughput(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_aiat_s[enb,ue]= sm.get_ue_pdcp_pkt_aiat_s(enb,ue, 'ul')
                monitoring_app.enb_ue_pdcp_rx_oo[enb,ue] = sm.get_ue_pdcp_pkt_oo(enb,ue, 'ul')


                log.info('UE ' + str(ue) + ' PDCP Tx pkts: '+str(monitoring_app.enb_ue_pdcp_tx[enb,ue]))
                log.info('UE ' + str(ue) + ' PDCP Tx pkt/s: '+str(monitoring_app.enb_ue_pdcp_tx_rate_s[enb,ue]))

                log.info('UE ' + str(ue) + ' PDCP Rx pkts: '+str(monitoring_app.enb_ue_pdcp_rx[enb,ue]))
                log.info('UE ' + str(ue) + ' PDCP Rx pkts/s: '+str(monitoring_app.enb_ue_pdcp_rx_rate_s[enb,ue]))

                # per eNB aggregated stas 
                monitoring_app.enb_pdcp_tx[enb]+=monitoring_app.enb_ue_pdcp_tx[enb,ue]
                monitoring_app.enb_pdcp_tx_bytes[enb]+=sm.get_ue_pdcp_pkt_bytes(enb,ue,'dl')
                monitoring_app.enb_pdcp_tx_sn[enb]+=sm.get_ue_pdcp_pkt_sn(enb,ue,'dl')
                monitoring_app.enb_pdcp_tx_aiat[enb]+=sm.get_ue_pdcp_pkt_aiat(enb,ue,'dl')
                monitoring_app.enb_pdcp_tx_rate_s[enb]+=sm.get_ue_pdcp_pkt_rate_per_s(enb,ue,'dl')
                monitoring_app.enb_pdcp_tx_throughput_s[enb]+= sm.get_ue_pdcp_pkt_throughput(enb,ue,'dl')
                monitoring_app.enb_pdcp_tx_aiat_s[enb]+= sm.get_ue_pdcp_pkt_aiat_s(enb,ue, 'dl')
               
                monitoring_app.enb_pdcp_rx[enb]+=sm.get_ue_pdcp_pkt(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_bytes[enb]+=sm.get_ue_pdcp_pkt_bytes(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_sn[enb]+=sm.get_ue_pdcp_pkt_sn(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_aiat[enb]+=sm.get_ue_pdcp_pkt_aiat(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_rate_s[enb]+=sm.get_ue_pdcp_pkt_rate_per_s(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_goodput_s[enb]+= sm.get_ue_pdcp_pkt_throughput(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_aiat_s[enb]+= sm.get_ue_pdcp_pkt_aiat_s(enb,ue, 'ul')
                monitoring_app.enb_ue_pdcp_rx_oo[enb] = sm.get_ue_pdcp_pkt_oo(enb,ue, 'ul')
                
                # RRC 
                monitoring_app.enb_ue_rsrp[enb,ue]=sm.get_ue_rsrp(enb,ue)
                monitoring_app.enb_ue_rsrq[enb,ue]=sm.get_ue_rsrq(enb,ue)

                log.info('UE ' + str(ue) + ' RSRP '+str(monitoring_app.enb_ue_rsrp[enb,ue]))
                log.info('UE ' + str(ue) + ' RSRQ '+str(monitoring_app.enb_ue_rsrq[enb,ue]))


                if monitoring_app.enb_ue_rsrp[enb,ue] == 0 : # and monitoring_app.enb_ue_trigger_meas[enb] == 1 :
                    monitoring_app.enb_ue_trigger_meas[enb] = 0
                    
                
                
            log.info('eNB ' + str(enb) +' PDCP Tx pkts'+str(monitoring_app.enb_pdcp_tx[enb]))
            log.info('eNB ' + str(enb) +' PDCP Rx pkts'+str(monitoring_app.enb_pdcp_rx[enb]))

                
      
    def run(self, sm,rrc):
        log.info('1. Reading the status of the underlying eNBs')
        sm.stats_manager('all')

        log.info('2. Gather statistics')
        monitoring_app.get_statistics(sm)

        for enb in range(0, sm.get_num_enb()) :
            if monitoring_app.enb_ue_trigger_meas[enb] == 0 :
                log.info('2.1 Enable RRC trigger measurement event for eNB ' + str(enb))
                rrc.trigger_meas()
                monitoring_app.enb_ue_trigger_meas[enb] = 1
       
        
        t = Timer(5, self.run,kwargs=dict(sm=sm,rrc=rrc))
        t.start()
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    
    parser.add_argument('--url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost', 
                        help='set the FlexRAN RTC URL: loalhost (default)')
    parser.add_argument('--port', metavar='[option]', action='store', type=str,
                        required=False, default='9999', 
                        help='set the FlexRAN RTC port: 9999 (default)')
    parser.add_argument('--url-app', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost', 
                        help='set the application server URL: loalhost (default)')
    parser.add_argument('--port-app', metavar='[option]', action='store', type=str,
                        required=False, default='9090', 
                        help='set the application server port: 9999 (default)')
    parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
                        required=False, default='test', 
                        help='Set the app operation mode either with FlexRAN or with the test json files: test(default), sdk')
    parser.add_argument('--rrc_meas', metavar='[option]', action='store', type=str,
                        required=False, default='periodical', 
                        help='Set the RRC trigger measurement type: one-shot, perodical(default), event-driven')
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='info', 
                        help='set the log level: debug, info (default), warning, error, critical')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()

    log=flexran_sdk.logger(log_level=args.log).init_logger()
    
    monitoring_app = monitoring_app(log=log,
                                    url=args.url,
                                    port=args.port,
                                    url_app=args.url_app,
                                    port_app=args.port_app,
                                    log_level=args.log,
                                    op_mode=args.op_mode)
    
    sm = flexran_sdk.stats_manager(log=log,
                                   url=args.url,
                                   port=args.port,
                                   op_mode=args.op_mode)


    rrc= flexran_sdk.rrc_trigger_meas(log=log,
                                      url=args.url,
                                      port=args.port,
                                      op_mode=args.op_mode)
    
    
    py3_flag = version_info[0] > 2 
    
    t = Timer(3, monitoring_app.run,kwargs=dict(sm=sm,rrc=rrc))
    t.start() 

            
