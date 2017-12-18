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
from lib import app_sdk
import signal

def sigint_handler(signum,frame):
    print 'Exiting, wait for the timer to expire... Bye'
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

class monitoring_app(object):
    """trigger external events happend in the underlying RAN
    """
    name='monitoring_app'
    # stats vars
    enb_sfn={}
    # pdcp
    enb_pdcp_sfn={}
    enb_ue_pdcp_tx={}
    enb_ue_pdcp_tx_bytes={}
    enb_ue_pdcp_tx_sn={}
    enb_ue_pdcp_tx_aiat={}
    enb_ue_pdcp_tx_w={}
    enb_ue_pdcp_tx_bytes_w={}
    enb_ue_pdcp_tx_aiat_w={}

    enb_pdcp_tx={}
    enb_pdcp_tx_bytes={}
    enb_pdcp_tx_sn={}
    enb_pdcp_tx_aiat={}
    enb_pdcp_tx_w={}
    enb_pdcp_tx_bytes_w={}
    enb_pdcp_tx_aiat_w={}

    enb_ue_pdcp_rx={}
    enb_ue_pdcp_rx_bytes={}
    enb_ue_pdcp_rx_sn={}
    enb_ue_pdcp_rx_aiat={}
    enb_ue_pdcp_rx_w={}
    enb_ue_pdcp_rx_bytes_w={}
    enb_ue_pdcp_rx_aiat_w={}
    enb_ue_pdcp_rx_oo={}

    enb_pdcp_rx={}
    enb_pdcp_rx_bytes={}
    enb_pdcp_rx_sn={}
    enb_pdcp_rx_aiat={}
    enb_pdcp_rx_w={}
    enb_pdcp_rx_bytes_w={}
    enb_pdcp_rx_aiat_w={}
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
    lc_ue_bo={}

    # App specific vars
    period=1.0
    name="monitoring"

    def __init__(self, log, url='http://localhost',port='9999',url_app='http://localhost',port_app='9090', log_level='info', op_mode='test'):
        super(monitoring_app, self).__init__()
        
        self.url = url+':'+port
        self.log = log
        self.log_level = log_level
        self.status = 'none'
        self.op_mode = op_mode
        
    def get_rrc_statistics(self, sm):
            
        for enb in range(0, sm.get_num_enb()) :
	   

            for ue in range(0, sm.get_num_ue(enb=enb)) :
		
                monitoring_app.enb_ue_rsrp[enb,ue]=sm.get_ue_rsrp(enb,ue)
                monitoring_app.enb_ue_rsrq[enb,ue]=sm.get_ue_rsrq(enb,ue)

                log.info('UE ' + str(ue) + ' RSRP: '+str(monitoring_app.enb_ue_rsrp[enb,ue]))
                log.info('UE ' + str(ue) + ' RSRQ: '+str(monitoring_app.enb_ue_rsrq[enb,ue]))


                if sm.get_ue_measid(enb,ue) == -1 : # and monitoring_app.enb_ue_trigger_meas[enb] == 1 :
                   log.info('2.1 Enable RRC trigger measurement event for eNB ' + str(enb))
                   rrc.trigger_meas()


    def get_pdcp_statistics(self, sm):
            
        for enb in range(0, sm.get_num_enb()) :
           
            
            monitoring_app.enb_pdcp_tx[enb]=0
            monitoring_app.enb_pdcp_tx_bytes[enb]=0
            monitoring_app.enb_pdcp_tx_sn[enb]=0
            monitoring_app.enb_pdcp_tx_aiat[enb]=0
            monitoring_app.enb_pdcp_tx_w[enb]=0
            monitoring_app.enb_pdcp_tx_bytes_w[enb]=0
            monitoring_app.enb_pdcp_tx_aiat_w[enb]=0

            monitoring_app.enb_pdcp_rx[enb]=0
            monitoring_app.enb_pdcp_rx_bytes[enb]=0
            monitoring_app.enb_pdcp_rx_sn[enb]=0
            monitoring_app.enb_pdcp_rx_aiat[enb]=0
            monitoring_app.enb_pdcp_rx_w[enb]=0
            monitoring_app.enb_pdcp_rx_bytes_w[enb]=0
            monitoring_app.enb_pdcp_rx_aiat_w[enb] = 0
            monitoring_app.enb_pdcp_rx_oo[enb] = 0

            # PDCP SFN 
            monitoring_app.enb_pdcp_sfn[enb]=sm.get_enb_pdcp_sfn(enb)

            log.info('Num UE ' + str(sm.get_num_ue(enb=enb)))
            log.info('PDCP SFN : ' + str(monitoring_app.enb_pdcp_sfn[enb]))
            
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                                                              
                # per eNB UE stats 
                monitoring_app.enb_ue_pdcp_tx[enb,ue]=sm.get_ue_pdcp_pkt(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_bytes[enb,ue]=sm.get_ue_pdcp_pkt_bytes(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_sn[enb,ue]=sm.get_ue_pdcp_pkt_sn(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_aiat[enb,ue]=sm.get_ue_pdcp_pkt_aiat(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_w[enb,ue]=sm.get_ue_pdcp_pkt_w(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_bytes_w[enb,ue] = sm.get_ue_pdcp_pkt_bytes_w(enb,ue,'dl')
                monitoring_app.enb_ue_pdcp_tx_aiat_w[enb,ue]= sm.get_ue_pdcp_pkt_aiat_w(enb,ue, 'dl')

                monitoring_app.enb_ue_pdcp_rx[enb,ue]=sm.get_ue_pdcp_pkt(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_bytes[enb,ue]=sm.get_ue_pdcp_pkt_bytes(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_sn[enb,ue]=sm.get_ue_pdcp_pkt_sn(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_aiat[enb,ue]=sm.get_ue_pdcp_pkt_aiat(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_w[enb,ue]=sm.get_ue_pdcp_pkt_w(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_bytes_w[enb,ue] = sm.get_ue_pdcp_pkt_bytes_w(enb,ue,'ul')
                monitoring_app.enb_ue_pdcp_rx_aiat_w[enb,ue]= sm.get_ue_pdcp_pkt_aiat_w(enb,ue, 'ul')
                monitoring_app.enb_ue_pdcp_rx_oo[enb,ue] = sm.get_ue_pdcp_pkt_oo(enb,ue, 'ul')


                log.info('UE ' + str(ue) + ' PDCP Tx pkts: '+str(monitoring_app.enb_ue_pdcp_tx[enb,ue]))
                log.info('UE ' + str(ue) + ' PDCP Tx pkt/w: '+str(monitoring_app.enb_ue_pdcp_tx_w[enb,ue]))
                log.info('UE ' + str(ue) + ' PDCP Tx bytes/w: '+str(monitoring_app.enb_ue_pdcp_tx_bytes_w[enb,ue]))
                log.info('UE ' + str(ue) + ' PDCP Tx aiat/w: '+str(monitoring_app.enb_ue_pdcp_tx_aiat_w[enb,ue]))

                log.info('UE ' + str(ue) + ' PDCP Rx pkts: '+str(monitoring_app.enb_ue_pdcp_rx[enb,ue]))
                log.info('UE ' + str(ue) + ' PDCP Rx pkts/w: '+str(monitoring_app.enb_ue_pdcp_rx_w[enb,ue]))
                log.info('UE ' + str(ue) + ' PDCP Rx bytes/w: '+str(monitoring_app.enb_ue_pdcp_rx_bytes_w[enb,ue]))
                log.info('UE ' + str(ue) + ' PDCP Rx aiat/w: '+str(monitoring_app.enb_ue_pdcp_rx_aiat_w[enb,ue]))

                # per eNB aggregated stas 
                monitoring_app.enb_pdcp_tx[enb]+=monitoring_app.enb_ue_pdcp_tx[enb,ue]
                monitoring_app.enb_pdcp_tx_bytes[enb]+=sm.get_ue_pdcp_pkt_bytes(enb,ue,'dl')
                monitoring_app.enb_pdcp_tx_sn[enb]+=sm.get_ue_pdcp_pkt_sn(enb,ue,'dl')
                monitoring_app.enb_pdcp_tx_aiat[enb]+=sm.get_ue_pdcp_pkt_aiat(enb,ue,'dl')
                monitoring_app.enb_pdcp_tx_w[enb]+=sm.get_ue_pdcp_pkt_w(enb,ue,'dl')
                monitoring_app.enb_pdcp_tx_bytes_w[enb]+= sm.get_ue_pdcp_pkt_bytes_w(enb,ue,'dl')
                monitoring_app.enb_pdcp_tx_aiat_w[enb]+= sm.get_ue_pdcp_pkt_aiat_w(enb,ue, 'dl')
               
                monitoring_app.enb_pdcp_rx[enb]+=sm.get_ue_pdcp_pkt(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_bytes[enb]+=sm.get_ue_pdcp_pkt_bytes(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_sn[enb]+=sm.get_ue_pdcp_pkt_sn(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_aiat[enb]+=sm.get_ue_pdcp_pkt_aiat(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_w[enb]+=sm.get_ue_pdcp_pkt_w(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_bytes_w[enb]+= sm.get_ue_pdcp_pkt_bytes_w(enb,ue,'ul')
                monitoring_app.enb_pdcp_rx_aiat_w[enb]+= sm.get_ue_pdcp_pkt_aiat_w(enb,ue, 'ul')
                monitoring_app.enb_ue_pdcp_rx_oo[enb] = sm.get_ue_pdcp_pkt_oo(enb,ue, 'ul')
                                  
                
                
            #log.info('eNB ' + str(enb) +' PDCP Tx pkts: '+str(monitoring_app.enb_pdcp_tx[enb]))
            #log.info('eNB ' + str(enb) +' PDCP Rx pkts: '+str(monitoring_app.enb_pdcp_rx[enb]))

    def get_mac_statistics(self, sm):
            
        for enb in range(0, sm.get_num_enb()) :
           
            monitoring_app.enb_dlrb[enb] = sm.get_cell_rb(enb,dir='DL')
            monitoring_app.enb_ulrb[enb] = sm.get_cell_rb(enb,dir='UL')
            monitoring_app.enb_ulmaxmcs[enb] = sm.get_cell_maxmcs(enb,dir='UL')
            monitoring_app.enb_dlmaxmcs[enb] = sm.get_cell_maxmcs(enb,dir='DL')

          
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                monitoring_app.enb_sfn[enb,ue]  = sm.get_enb_sfn(enb,ue)
                monitoring_app.ue_dlwcqi[enb,ue]=sm.get_ue_dlwbcqi(enb,ue)
                monitoring_app.ue_phr[enb,ue] =sm.get_ue_phr(enb,ue)
                                                
                log.info('eNB ' + str(enb) +' DL CQI: '+str(monitoring_app.ue_dlwcqi[enb,ue]))
                log.info('eNB ' + str(enb) +' UL PHR: '+str(monitoring_app.ue_phr[enb,ue]))

		for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :
                    # for each lcgid rater than lc
                    monitoring_app.lc_ue_bsr[enb,ue,lc] = sm.get_ue_bsr(enb,ue,lc=lc)
                    monitoring_app.lc_ue_bo[enb, ue, lc] = sm.get_ue_lc_bo(enb=enb, ue=ue, lc=lc)
			
                    log.info('eNB ' + str(enb) +' DL BO: '+str(monitoring_app.lc_ue_bo[enb, ue, lc]))		    
                    log.info('eNB ' + str(enb) +' UL BSR: '+str(monitoring_app.lc_ue_bsr[enb,ue,lc]))


      
    def run(self, sm,rrc):
        log.info('1. Reading the status of the underlying eNBs')
        sm.stats_manager('all')

	log.info('2.1 Gather MAC statistics')
        monitoring_app.get_mac_statistics(sm)

        log.info('2.2 Gather PDCP statistics')
        monitoring_app.get_pdcp_statistics(sm)

	log.info('2.3 Gather RRC statistics')
        monitoring_app.get_rrc_statistics(sm)        
       
        
        t = Timer(monitoring_app.period, self.run,kwargs=dict(sm=sm,rrc=rrc))
        t.start()
        
    def handle_open_data(self, client, message):
	client.send(json.dumps({'monitoring_app':'please fill this function'}))
        
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
                        help='set the application server port: 9090 (default)')
# need to may be rename parameters - do not know
    parser.add_argument('--app-url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost', 
                        help='set the App address to open data: loalhost (default)')
    parser.add_argument('--app-port', metavar='[option]', action='store', type=int,
                        required=False, default=8080, 
                        help='set the App port to open data: 8080 (default)')

    parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
                        required=False, default='test', 
                        help='Set the app operation mode either with FlexRAN or with the test json files: test(default), sdk')
    parser.add_argument('--rrc_meas', metavar='[option]', action='store', type=str,
                        required=False, default='periodical', 
                        help='Set the RRC trigger measurement type: one-shot, perodical(default), event-driven')
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='info', 
                        help='set the log level: debug, info (default), warning, error, critical')
    parser.add_argument('--period',  metavar='[option]', action='store', type=float,
                        required=False, default=1, 
                        help='set the period of the app: 1s (default)')

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
    
    # open data additions 
    app_open_data=app_sdk.app_builder(log=log,
				      app=monitoring_app.name,
                                      address=args.app_url,
                                      port=args.app_port)

    monitoring_open_data = app_sdk.app_handler(log=log, callback=monitoring_app.handle_open_data)


    app_open_data.add_options(monitoring_app.name, handler=monitoring_open_data)
    app_open_data.run_app()

    sm = flexran_sdk.stats_manager(log=log,
                                   url=args.url,
                                   port=args.port,
                                   op_mode=args.op_mode)


    rrc= flexran_sdk.rrc_trigger_meas(log=log,
                                      url=args.url,
                                      port=args.port,
                                      op_mode=args.op_mode)
    
    
    py3_flag = version_info[0] > 2 
    
    monitoring_app.period=args.period
    log.info('App period is set to : ' + str(monitoring_app.period))
    t = Timer(monitoring_app.period, monitoring_app.run,kwargs=dict(sm=sm,rrc=rrc))
    t.start() 
    app_sdk.run_all_apps()
            
