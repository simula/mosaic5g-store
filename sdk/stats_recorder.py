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
    File name: stats_recorder_app.
    Author: navid nikaein
    Description: This app triggers an external event based on the predefined threshold through FLEXRAN SDK
    version: 1.0
    Date created: 7 July 2017
    Date last modified: 7 July 2017 
    Python Version: 2.7
    
"""


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
    parser.add_argument('--app-period',  metavar='[option]', action='store', type=float,
                        required=False, default=0.1, 
                        help='set the period of the app: 1s (default)')
    parser.add_argument('--num-samples',  metavar='[option]', action='store', type=int,
                        required=False, default=100, 
                        help='set the number of samples to record: (default 100)')
    
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    
    args = parser.parse_args()
    
    log=logger.sdk_logger(log_level=args.log).init_logger()
    
    sm = flexran_sdk.stats_manager(log=log,
                                   url=args.url,
                                   port=args.port,
                                   op_mode=args.op_mode)

    period=args.app_period
    n_samples=args.num_samples
    c_sample=0
    py3_flag = version_info[0] > 2
    
    
    log.info('App period : ' + str(period))
    log.info('Num samples is set to : ' + str(n_samples))

    sm.start_recorder()
    while c_sample < n_samples :
        sm.stats_manager('all')
        c_sample+=1
        sleep(period)

    sm.stop_recorder()
    log.info('recording is finished')


