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
    File name: test_app.py
    Author: navid nikaein
    Description: This app tests the llmec_sdk lib
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


from lib import llmec_sdk 
from lib import logger

import signal

import ipcalc

NUM_UES=10
NUM_ENBS=2
NUM_EPS_BEARERS_PER_UE=2

DEFAULT_EPS_BEARER=5
NUM_SLICE=2
NUM_TRIALS=3




def sigint_handler(signum,frame):
    print 'Exiting, wait for the timer to expire... Bye'
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

class test_app(object):
    """test test app that makes use of llmec SDK
    """

    def __init__(self, log, url='http://localhost',port='9999',log_level='info', op_mode='test'):
        super(test_app, self).__init__()
        
        self.url = url+port
        self.log = log
        self.log_level = log_level
        self.status = 0
        self.op_mode = op_mode
        
        self.ul_teid = 0x0
        self.dl_teid = 0x0
        self.ue_drb  = 5
        self.ue_imsi = 208950000000000
#       self.ue_ip = '172.16.0.0/27'
#        self.ue_ip = '172.16.0.0/24' # 255 
        self.ue_ip = '172.16.0.0/20'  # 4094 

        self.enb_ip = '192.168.12.79/30'

        self.remote_ip = '193.55.113.118'

        self.mec_ip = '192.168.12.100/20'

        self.num_added_ues = 0
        self.num_redirected_ues = 0
        self.num_removed_redirected_ues = 0
        self.num_removed_ues = 0
        
        
        self.py3_flag = version_info[0] > 2 

    def get_status(self, bm, fm):
        fm.flow_status()
        bm.get_all_bearer_context()

        self.log.info('Total number of applied UEs ' + str(fm.get_num_ues()))
        self.log.info('Total number of applied rules ' + str(fm.get_num_rules()))
        print '-----------------------------------------------------------------------------------------'
    
        for ue_id in range(0, fm.get_num_ues()) :
            fm.get_num_bytes(ue_id)
            fm.get_num_bytes(ue_id,dir='dl')
            fm.get_num_packets(ue_id)
            fm.get_num_packets(ue_id,dir='dl')
            print '-----------------------------------------------------------------------------------------'

        for ue_id in range(0, bm.get_num_ues()) :
            self.log.info('UE id ' + str(ue_id) + ', IMSI=' + bm.bearer_context[ue_id]['imsi'] + ', s1 uplink tunnel ID=' + str(bm.bearer_context[ue_id]['s1_ul_teid']) + ', s1 downlink tunnel ID=' + str(bm.bearer_context[ue_id]['s1_dl_teid']))
            print '-----------------------------------------------------------------------------------------'

    def add_ue_bearer(self, bm):
        
        
        ue_network = ipcalc.Network(self.ue_ip)
        ue_host_first = ue_network.host_first()
        ue_addresses = (ue_host_first + i for i in range(ue_network.size()-2))

        enb_network = ipcalc.Network(self.enb_ip)
        enb_host_first = enb_network.host_first()
        enb_addresses = (enb_host_first + i for i in range(enb_network.size()-2))
        
        
        #self.log.info('add ue bearer for ' + str(ue_network.size()-2) + ' UEs' )
        for enb in range(0, NUM_ENBS-1) :
            enb_address=next(enb_addresses)
            for ue in range(0, NUM_UES-1) :
                for drb in range(0, NUM_EPS_BEARERS_PER_UE-1):
                    self.log.info('adding UE ' + str(ue) + ' bearer' + str(drb) + ' for eNB ' +str(enb))
                    slice_id = drb % NUM_SLICE
                        
                    state=bm.add_ue_bearer_rule(imsi=str(self.ue_imsi+ue),eps_drb=self.ue_drb+drb,slice_id=slice_id, ul_teid=str(ue+drb), dl_teid=str(ue+drb),ue_ip=str(next(ue_addresses)), enb_ip=str(enb_address))

                    if state == 'connected':
                        self.num_added_ues+=1
                    # testing if the UE is actually added
                    state = bm.get_ue_bearer_context(imsi=str(self.ue_imsi+ue),eps_drb=str(self.ue_drb+drb))
                    if state == 'connected':
                        self.log.info('got context for the UE bearer assocaited with mec id')
                    else:
                        self.log.warn('failed to get UE bearer assocaited with mec id ')
                        
    def redirect_ue_bearer(self, bm):

        mec_network = ipcalc.Network(self.mec_ip)
        mec_host_first = mec_network.host_first()
        mec_addresses = (mec_host_first + i for i in range(mec_network.size()-2))

             
        #self.log.info('redirecting ue bearer for ' + str(mec_network.size()-2) + ' UEs' )
#        for mec_id in range(1, self.num_added_ues+1) :

        for mec_id in range(1, NUM_UES) :
            self.log.info('redirecting UE bearer assocaited with mec id ' + str(mec_id))
            #self.log.debug(bm.get_ue_bearer_context_by_mecid(mec_id))
            
            state=bm.redirect_ue_bearer_rule_by_mec_id(mec_id=mec_id,remote_ip=self.remote_ip,mec_ip=str(next(mec_addresses)))
            if state == 'connected':
                self.num_redirected_ues+=1
                        
    def remove_redirected_ue_bearer(self, bm):

        
       # for mec_id in range(1, self.num_redirected_ues+1) :
        for mec_id in range(1, NUM_UES) :
            self.log.info('removing redirected UE bearer assocaited with mec id ' + str(mec_id))
            #self.log.debug(bm.get_ue_bearer_context_by_mecid(mec_id))
            
            state=bm.remove_redirected_ue_bearer_by_mecid(mec_id=mec_id)
            if state == 'connected':
                self.num_removed_redirected_ues+=1
                
    def remove_ue_bearer(self, bm):

        
       for mec_id in range(1, NUM_UES) :
            self.log.info('removing UE bearer assocaited with mec id ' + str(mec_id))
            #self.log.debug(bm.get_ue_bearer_context_by_mecid(mec_id))
            
            state=bm.remove_ue_bearer_by_id(mec_id=mec_id)
            if state == 'connected':
                self.num_removed_ues+=1          
                
    def cmd(self, bm, fm):
        user_in=''
        try:
            if self.py3_flag:
                user_in = input("************ Enter the command to execut(flush,redirect):  ************")
            else:
                user_in = raw_input("************ Enter the command to execut(flush,redirect): ************")
                
        except ValueError:
            self.log.warning('Please enter a string!')

        
        if user_in == 'flush' :
            self.log.info('flusing the rules')
            fm.flush_flows()

        elif user_in == 'redirect' :
            network = ipcalc.Network(self.ue_ip)
            host_first = network.host_first()
            addresses = (host_first + i for i in range(network.size()-2))
            next(addresses) # skip the  even numbers
            # redirect all UEs to the local video server
            self.log.info('redirecting flows towards MEC apps for ' + str(network.size()-2) + ' UEs' )
            for i in range(0, network.size()-2) :
                
                bm.redirect_ue_rule(ul_teid=str(self.ul_teid), dl_teid=str(self.dl_teid),ue_ip=str(next(addresses)),enb_ip=self.enb_ip, remote_ip=self.remote_ip, local_ip=self.local_ip)
                self.ul_teid+=1
                self.dl_teid+=1
                if  2* i + 2 < network.size()-2 : 
                    next(addresses) # skip the  even numbers
                else :
                    break;
        
        elif user_in != ' ' :
            self.log.info('unknow command ' + str(user_in))
        else :
          self.log.debug('no command entered')
        
        t2 = Timer(5, self.cmd,kwargs=dict(bm=bm,fm=fm))
        t2.start()        

      
        #for 
        #data= {'s1_ul_teid': ul_teid, 's1_dl_teid' : dl_teid, 'ue_ip': ue_ip, 'enb_ip' : enb_ip,'from':remote_ip, 'to': local_ip}
        
     
        
    def run(self, bm, fm):
        log.info('2. Reading the status of the underlying flows')
        
        self.get_status(bm, fm)

        self.add_ue_bearer(bm)

        self.redirect_ue_bearer(bm)

        self.remove_redirected_ue_bearer(bm)

        self.remove_ue_bearer(bm)

        log.info('num added ue bearer ' + str(self.num_added_ues))
        log.info('num redirected ue bearer ' + str(self.num_redirected_ues))
        log.info('num removed redirected ue bearer ' + str(self.num_removed_redirected_ues))
        log.info('num removed ue bearer ' + str(self.num_removed_ues))
        
        t1 = Timer(10, self.run,kwargs=dict(bm=bm, fm=fm))
        t1.start()        
                  
   
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    
    parser.add_argument('--url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost', 
                        help='set the LLMEC URL: loalhost (default)')
    parser.add_argument('--port', metavar='[option]', action='store', type=str,
                        required=False, default='9999', 
                        help='set the LLMEC port: 9999 (default)')
    parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
                        required=False, default='sdk', 
                        help='Test SDK with already generated json files: test (default), sdk')
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='info', 
                        help='set the log level: debug, info (default), warning, error, critical')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()

    log=llmec_sdk.logger(log_level=args.log).init_logger()
    
    test_app = test_app(log=log,
                   url=args.url,
                   port=args.port,
                   log_level=args.log,
                   op_mode=args.op_mode)
    

    fm = llmec_sdk.flow_manager(log=log,
                                url=args.url,
                                port=args.port,
                                op_mode=args.op_mode)
    bm = llmec_sdk.bearer_manager(log=log,
                                  url=args.url,
                                  port=args.port,
                                  op_mode=args.op_mode)
    fm.flow_status()
    bm.get_all_bearer_context()
    #test_app.run(bm,fm)
    
    t1 = Timer(10, test_app.run,kwargs=dict(bm=bm, fm=fm))
    t1.start()


    #t2 = Timer(5, test_app.cmd,kwargs=dict(um=um, fm=fm))
    #t2.start()

