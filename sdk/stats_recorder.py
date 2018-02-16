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

# Naming convention 
# enb, ue, lc are idices which mean that the observed measurement depends on these parameters
# dl, ul. 
# _w means it is over a window. Without it means it is for tti. 
# It is assumed that all measurements are obtained from the eNB, but tis can contain measurements made dl and sent ul by UE
# I am only interested in the impact on data channel. But the control channel traffic can have impact on the data channel. 
# I have decided to ignore this for simplicity.   
# Commenting convention 
# tti - means this is updated every tti. 
# tti uc - means it is updated every tti and a counter is incremented.  
# window - means it is updated every window


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

from lib import flexran_sdk 
from lib import logger
import signal


def sigint_handler(signum,frame):
    print 'Exiting, wait for the timer to expire... Bye'
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

class recording_app(object):
    period=0.01

    def __init__(self, log, log_level='error', op_mode='test'):
        super(recording_app, self).__init__()
        
        self.log = log
        self.log_level = log_level
        self.op_mode = op_mode
        
    def run(self,sm):

        self.log.info('Updating all the stats')
        sm.stats_manager('all')
        
        t = Timer(recording_app.period, self.run,kwargs=dict(sm))
        t.start()
        
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
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='error', 
                        help='set the log level: debug, info (default), warning, error, critical')
    parser.add_argument('--period',  metavar='[option]', action='store', type=float,
                        required=False, default=0.01, 
                        help='set the period of the app: 1s (default)')
    
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    
    args = parser.parse_args()
    
    log=flexran_sdk.logger(log_level=args.log).init_logger()
    
    sm = flexran_sdk.stats_manager(log=log,
                                   url=args.url,
                                   port=args.port,
                                   op_mode=args.op_mode)
    
    recording_app = recording_app(log=log,
                                  log_level=args.log,
                                  op_mode=args.op_mode)

    recording_app.period=args.period
    
    py3_flag = version_info[0] > 2
    
    
    sm.set_recorder_status(record='on')
    log.info('App period is set to : ' + str(recording_app.period))
    recording_app.run(sm)

