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
    File name: monitoring_app.py
    Author: navid nikaein
    Description: This app gathers RAN statistics per function and provides open data API for other apps to access RAN stats. Also it provides dynamic graphs to monitor the RAN statistic of interest.
    version: 1.0
    Date created: 7 July 2017
    Date last modified: 22 Fev 2018
    Python Version: 2.7
    
"""

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

import rrm_app_vars

from lib import app_graphs
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

    # Time between receiving a PHY SDU (TB) and receiving a 
    # HARQ ACK for the sent PHY PDU 
    dc_enb_ue_dl_succ_rx_delay_moments={}#[enb,ue][]
    # Time between receiving a MAC SDU and receiving a 
    # HARQ ACK for the sent PHY PDU. This is a combination of 
    # the scheduling and the phy delays  
    dc_enb_ue_dl_mac_phy_delay_moments={}#[enb,ue][]
    # Time between the eNB receiving a scheduling request from a UE and time instant at 
    # which resource is granted to the UE. 
    dc_enb_ue_ul_sch_delay_moments={}#[enb,ue][]
    # Time between the instant at which UL data was expected (based on UL grant) 
    # and time at which HARQ ACK was sent to the UE
    dc_enb_ue_ul_succ_rx_delay_moments={}#[enb,ue][]


    # App specific vars
    period=1.0
    name="monitoring_app"
    first_time=True
    

    #-------------------------------------------- PDCP-------------------------------------
    # Dl
    enb_dl_pdcp_sfn={}# super frame number (length 10 ms)
    enb_ue_dl_pdcp={}# number of Dl packets running counter from t=0 
    enb_ue_dl_pdcp_bytes={}# numer of Dl bytes running counter from t=0 
    enb_ue_dl_pdcp_sn={}# last PDCP packet sequence number sent Dl to PDCP 
    enb_ue_dl_pdcp_aiat={}# aggregated interarrival time between PDCP packets. (A new value is updated when a new packet is received. It can maintain this over multiple TTIs is the arrival rate is slow.

    enb_ue_dl_pdcp_w={}# number Dl packets in window t=100ms  
    enb_ue_dl_pdcp_bytes_w={}# number of Dl bytes in window t=100ms
    enb_ue_dl_pdcp_aiat_w={}# aggregated interarrival time between PDCP packets over all logical channels in window t=100ms

    # Ul
    enb_ue_ul_pdcp={}
    enb_ue_ul_pdcp_bytes={}
    enb_ue_ul_pdcp_sn={}# last PDCP packet sequence number received Ul at PDCP 
    enb_ue_ul_pdcp_aiat={}
    enb_ue_ul_pdcp_oo={}# number of PDCP packets received out of order. It is an upcounter. 
    
    enb_ue_ul_pdcp_w={}
    enb_ue_ul_pdcp_bytes_w={}
    enb_ue_ul_pdcp_aiat_w={}
    
    #---------------------------------------------- RLC ------------------------------------
    # Dl
    enb_ue_dl_rlc_queue_len_bytes={}# Length in number of bytes of the RLC queue (Where PDUs wait to get scheduled)
    enb_ue_dl_rlc_queue_num_pdu={}# Length in number of bytes of the RLC queue (Where PDUs wait to get scheduled)
    enb_ue_dl_rlc_bytes={}
    enb_ue_dl_rlc_hol_delay={}# Head of line delay. Which is the Dl scheduling delay. 
 
    enb_ue_dl_rlc_w={}# number of SDUs received Dl in window
    enb_ue_dl_rlc_bytes_w={}

    # Ul
    enb_ue_ul_rlc={}# number of SDUs received Ul
    enb_ue_ul_rlc_bytes={}

    enb_ue_ul_rlc_w={}# number of SDUs received Ul in window
    enb_ue_ul_rlc_bytes_w={}

    #---------------------------------------------- RRC -----------------------------------------
    enb_ue_rsrp={}
    enb_ue_rsrq={}
    enb_ue_trigger_meas={}

    #------------------------------------- ????---------------------------------------------------
    enb_ue_ul_snr={}
    
    # ----------------------------------------------MAC-------------------------------------
    # Dl
    enb_dl_mac_sfn={}
    enb_ue_dl_mac_rb={}# number of Ul resource blocks scheduled by eNB for UE 
    enb_dl_mac_maxmcs={}# Fixed
    enb_ue_dl_mac_wcqi={}# Dl wideband CQI      
    enb_ue_dl_mac_tbs={} # Transport block size
    enb_ue_dl_mac_retx_rb={} # Transport block size
    enb_ue_dl_mac_mcs={} # MCS
    enb_ue_dl_mac_bytes={} # 

    # To do: learn what these are
    ue_phr={} # Ul power headrome
    lc_ue_bsr={} # buffer status report from UE 
    lc_ue_bo={} # buffer occupancy ???

    enb_ue_ul_mac_retx_rb={}
    enb_ue_dl_mac_w={}   
    enb_ue_dl_mac_bytes_w={}


    # Ul
    enb_ue_ul_mac_rb={}# number of Dl resource blocks scheduled by eNB for UE   
    ue_ul_mac_maxmcs={}# Fixed 
    enb_ue_ul_mac_tbs={} # Transport block size
    enb_ue_dl_mac_retx_rb={} # Transport block size
    enb_ue_ul_mac_mcs={} # MCS
    enb_ue_ul_mac_bytes={}


    enb_ue_ul_mac_w={}   
    enb_ue_ul_mac_bytes_w={}

    # -----------------------------------------------------PHY------------------------------ 
    # Dl
    enb_dl_phy_tti_num={} # TTI number or subframe number
    enb_dl_phy_sfn={} # Super frame number 

    enb_ue_dl_phy_harq_acked_bytes_w={}
    enb_ue_dl_phy_harq_etx_w={}

    # Ul
    enb_ue_ul_phy_harq_acked_bytes_w={}
    enb_ue_ul_phy_harq_etx_w={}    

    enb_ue_hid_dl_phy_tx_delay_cnt={}#[enb,ue,hpid]
    enb_ue_dl_phy_tx_ack_delay={}#[enb,ue]
    enb_ue_dl_phy_tx_ack_attempts={}#[enb,ue]
    enb_ue_hid_dl_phy_tx_attempts_cnt={}#[enb,ue,hid]

    enb_ue_dl_phy_acked_bytes={}#[enb,ue]
    enb_ue_prev_hid_tbs={}#[enb,ue,hid]

    def __init__(self, log, url='http://localhost',port='9999',url_app='http://localhost',port_app='9090', log_level='info', op_mode='test'):
        super(monitoring_app, self).__init__()
        
        self.url = url+':'+port
        self.log = log
        self.log_level = log_level
        self.status = 'none'
        self.op_mode = op_mode

    def init_data_holders(self,sm):
	 sm.stats_manager('all')
         for enb in range(0, sm.get_num_enb()) :
            self.enb_dl_pdcp_sfn[enb]=0# super frame number (length 10 ms)
            self.enb_dl_mac_maxmcs[enb]=0# Fixed
            self.enb_dl_mac_sfn[enb]=0
            self.enb_dl_phy_tti_num[enb]=0 # TTI number or subframe number
            self.enb_dl_phy_sfn[enb]=0 # Super frame number
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                self.enb_ue_dl_pdcp[enb,ue]=0# number of Dl packets running counter from t=0 
                self.enb_ue_dl_pdcp_bytes[enb,ue]=0# numer of Dl bytes running counter from t=0 
                self.enb_ue_dl_pdcp_sn[enb,ue]=0# last PDCP packet sequence number sent Dl to PDCP 
                self.enb_ue_dl_pdcp_aiat[enb,ue]=0# aggregated interarrival time between PDCP packets. (A new value is updated when a new packet is received. It can maintain this over multiple TTIs is the arrival rate is slow.
                self.enb_ue_dl_pdcp_w[enb,ue]=0# number Dl packets in window t=100ms  
                self.enb_ue_dl_pdcp_bytes_w[enb,ue]=0# number of Dl bytes in window t=100ms
                self.enb_ue_dl_pdcp_aiat_w[enb,ue]=0# aggregated interarrival time between PDCP packets over all logical channels in window t=100ms
                self.enb_ue_ul_pdcp[enb,ue]=0
                self.enb_ue_ul_pdcp_bytes[enb,ue]=0
                self.enb_ue_ul_pdcp_sn[enb,ue]=0# last PDCP packet sequence number received Ul at PDCP 
                self.enb_ue_ul_pdcp_aiat[enb,ue]=0
                self.enb_ue_ul_pdcp_oo[enb,ue]=0# number of PDCP packets received out of order. It is an upcounter. 
                self.enb_ue_ul_pdcp_w[enb,ue]=0
                self.enb_ue_ul_pdcp_bytes_w[enb,ue]=0
                self.enb_ue_ul_pdcp_aiat_w[enb,ue]=0

                for lc in range(0,3) :
                    self.enb_ue_dl_rlc_hol_delay[enb,ue,lc]=0# Head of line delay. Which is the Dl scheduling delay.
                    self.enb_ue_dl_rlc_queue_len_bytes[enb,ue,lc]=0# Length in number of bytes of the RLC queue (Where PDUs wait to get scheduled)
                    self.enb_ue_dl_rlc_queue_num_pdu[enb,ue,lc]=0# Length in number of bytes of the RLC queue (Where PDUs wait to get scheduled)
                
                self.enb_ue_dl_rlc_bytes[enb,ue]=0
                self.enb_ue_dl_rlc_w[enb,ue]=0# number of SDUs received Dl in window
                self.enb_ue_dl_rlc_bytes_w[enb,ue]=0
                self.enb_ue_ul_rlc[enb,ue]=0# number of SDUs received Ul
                self.enb_ue_ul_rlc_bytes[enb,ue]=0
                self.enb_ue_ul_rlc_w[enb,ue]=0# number of SDUs received Ul in window
                self.enb_ue_ul_rlc_bytes_w[enb,ue]=0

                self.enb_ue_rsrp[enb,ue]=0
                self.enb_ue_rsrq[enb,ue]=0
                self.enb_ue_trigger_meas[enb,ue]=0
                self.enb_ue_ul_snr[enb,ue]=0

                self.enb_ue_dl_mac_rb[enb,ue]=0# number of Ul resource blocks scheduled by eNB for UE 
                self.enb_ue_dl_mac_wcqi[enb,ue]=0# Dl wideband CQI   
                self.enb_ue_dl_mac_bytes[enb,ue]=0
                # To do: fill in the right format
                self.ue_phr[enb,ue]=0 # Ul power headrome
                self.enb_ue_dl_mac_w[enb,ue]=0  
                self.enb_ue_dl_mac_bytes_w[enb,ue]=0
                self.enb_ue_ul_mac_rb[enb,ue]=0# number of Dl resource blocks scheduled by eNB for UE   
                self.ue_ul_mac_maxmcs[ue]=0# Fixed 
                self.enb_ue_ul_mac_w[enb,ue]=0  
                self.enb_ue_ul_mac_bytes_w[enb,ue]=0
                for lc in range(0,4) :
                    self.lc_ue_bsr[enb,ue,lc]=0 # buffer status report from UE 
                    self.lc_ue_bo[enb,ue,lc]=0# buffer occupancy ???

                self.enb_ue_dl_mac_tbs[enb,ue]=0 # Transport block size
                self.enb_ue_dl_mac_retx_rb[enb,ue]=0 # Retx Transport block size
                self.enb_ue_dl_mac_mcs[enb,ue]=0 # MCS
                self.enb_ue_dl_phy_harq_acked_bytes_w[enb,ue]=0
                self.enb_ue_dl_phy_harq_etx_w[enb,ue]=0
                self.enb_ue_ul_mac_tbs[enb,ue]=0 # Transport block size
                self.enb_ue_ul_mac_retx_rb[enb,ue]=0 # retx Transport block size
                self.enb_ue_ul_mac_mcs[enb,ue]=0 # MCS
                self.enb_ue_ul_mac_bytes[enb,ue]=0

                self.enb_ue_ul_phy_harq_acked_bytes_w[enb,ue]=0
                self.enb_ue_ul_phy_harq_etx_w[enb,ue]=0

                self.enb_ue_dl_phy_tx_ack_delay[enb,ue]=0
                self.enb_ue_dl_phy_tx_ack_attempts[enb,ue]=0
                self.enb_ue_dl_phy_acked_bytes[enb,ue]=0

                for harq_id in range(0,8):
                    self.enb_ue_hid_dl_phy_tx_delay_cnt[enb,ue,harq_id]=0
                    self.enb_ue_hid_dl_phy_tx_attempts_cnt[enb,ue,harq_id]=0
                    self.enb_ue_prev_hid_tbs[enb,ue,harq_id]=0


    def get_pdcp_statistics(self, sm):
            
        for enb in range(0, sm.get_num_enb()) :
            self.enb_dl_pdcp_sfn[enb]=sm.get_enb_pdcp_sfn(enb)
            
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                                     
                self.enb_ue_dl_pdcp[enb,ue]=sm.get_ue_pdcp_pkt(enb,ue,'dl')# number of Dl packets running counter from t=0 
                self.enb_ue_dl_pdcp_bytes[enb,ue]=sm.get_ue_pdcp_pkt_bytes(enb,ue,'dl')# numer of Dl bytes running counter from t=0 
                self.enb_ue_dl_pdcp_sn[enb,ue]=sm.get_ue_pdcp_pkt_sn(enb,ue,'dl')# last PDCP packet sequence number sent Dl to PDCP 
                self.enb_ue_dl_pdcp_aiat[enb,ue]=sm.get_ue_pdcp_pkt_aiat(enb,ue,'dl')# aggregated interarrival time between PDCP packets. (A new value is updated when a new packet is received. It can maintain this over multiple TTIs is the arrival rate is slow.
                self.enb_ue_dl_pdcp_w[enb,ue]=sm.get_ue_pdcp_pkt_w(enb,ue,'dl')# number Dl packets in window t=100ms  
                self.enb_ue_dl_pdcp_bytes_w[enb,ue]=sm.get_ue_pdcp_pkt_bytes_w(enb,ue,'dl')# number of Dl bytes in window t=100ms
                self.enb_ue_dl_pdcp_aiat_w[enb,ue]=sm.get_ue_pdcp_pkt_aiat_w(enb,ue, 'dl')# aggregated interarrival time between PDCP packets over all logical channels in window t=100ms
                self.enb_ue_ul_pdcp[enb,ue]=sm.get_ue_pdcp_pkt(enb,ue,'ul')
                self.enb_ue_ul_pdcp_bytes[enb,ue]=sm.get_ue_pdcp_pkt_bytes(enb,ue,'ul')
                self.enb_ue_ul_pdcp_sn[enb,ue]=sm.get_ue_pdcp_pkt_sn(enb,ue,'ul')# last PDCP packet sequence number received Ul at PDCP 
                self.enb_ue_ul_pdcp_aiat[enb,ue]=sm.get_ue_pdcp_pkt_aiat(enb,ue,'ul')
                self.enb_ue_ul_pdcp_oo[enb,ue]= sm.get_ue_pdcp_pkt_oo(enb,ue, 'ul')# number of PDCP packets received out of order. It is an upcounter. 
                self.enb_ue_ul_pdcp_w[enb,ue]=sm.get_ue_pdcp_pkt_w(enb,ue,'ul')
                self.enb_ue_ul_pdcp_bytes_w[enb,ue]= sm.get_ue_pdcp_pkt_bytes_w(enb,ue,'ul')
                self.enb_ue_ul_pdcp_aiat_w[enb,ue]= sm.get_ue_pdcp_pkt_aiat_w(enb,ue, 'ul')

                # If I want to visulatize this
                #viz.update(self.enb_ue_dl_pdcp[enb,ue])


    def get_rlc_statistics(self, sm):

        for enb in range(0, sm.get_num_enb()) :
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                for lc in range (0,3) :
                    self.enb_ue_dl_rlc_queue_len_bytes[enb,ue,lc]=sm.get_ue_lc_bo(enb,ue,lc)# Length in number of bytes of the RLC queue (Where PDUs wait to get scheduled)
                    self.enb_ue_dl_rlc_queue_num_pdu[enb,ue,lc]=sm.get_ue_lc_num_pdus(enb,ue,lc)# Length in number of bytes of the RLC queue (Where PDUs wait to get scheduled)
                    self.enb_ue_dl_rlc_hol_delay[enb,ue,lc]=sm.get_ue_lc_hol_delay(enb,ue,lc)# Head of line delay. Which is the Dl scheduling delay. 
                
                self.enb_ue_ul_rlc[enb,ue]=0# number of SDUs received Ul
                self.enb_ue_ul_rlc_bytes[enb,ue]=0


    def get_mac_statistics(self, sm):
            
        for enb in range(0, sm.get_num_enb()) :
            self.enb_dl_mac_maxmcs[enb]=0# Fixed
          
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                # To hook_ most of them 
                self.enb_dl_mac_sfn[enb]= sm.get_enb_sfn(enb,ue)# Fixed
                self.enb_ue_dl_mac_rb[enb,ue]=sm.get_ue_prb(enb,ue,dir='DL')# number of Ul resource blocks scheduled by eNB for UE 
                self.enb_ue_dl_mac_retx_rb[enb,ue]=sm.get_ue_prb_retx(enb,ue,dir='DL') # Transport block size
                self.enb_ue_dl_mac_wcqi[enb,ue]=sm.get_ue_dlwbcqi(enb,ue)# Dl wideband CQI    

                self.enb_ue_dl_mac_bytes[enb,ue]=sm.get_ue_mac_sdu_length(enb, ue, dir='DL') 
                self.enb_ue_dl_mac_tbs[enb,ue]=sm.get_ue_tbs(enb, ue, dir='DL') # Transport block size
                h=int(self.enb_dl_pdcp_sfn[enb]) % 8
                self.enb_ue_prev_hid_tbs[enb,ue,h]=self.enb_ue_dl_mac_tbs[enb,ue]
                self.enb_ue_dl_mac_mcs[enb,ue]=sm.get_ue_mcs1(enb, ue, dir='DL') # MCS
                # To do: fill in the right format
                self.ue_phr[enb,ue]=sm.get_ue_phr(enb,ue) # Ul power headrome
                self.enb_ue_ul_mac_rb[enb,ue]=sm.get_ue_prb(enb, ue, dir='UL')# number of Dl resource blocks scheduled by eNB for UE   
                self.enb_ue_ul_mac_retx_rb[enb,ue]=sm.get_ue_prb_retx(enb, ue, dir='UL') # Transport block size
                self.ue_ul_mac_maxmcs[ue]=0# Fixed 
                self.enb_ue_ul_mac_bytes[enb,ue]=sm.get_ue_mac_sdu_length(enb, ue, dir='UL') 
                self.enb_ue_ul_mac_tbs[enb,ue]=sm.get_ue_tbs(enb, ue, dir='UL') # Transport block size
                self.enb_ue_ul_mac_mcs[enb,ue]=sm.get_ue_mcs1(enb, ue, dir='UL') # MCS

                #for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :
                    # for each lcgid rater than lc
                for lc in range(0,4):
                    self.lc_ue_bsr[enb,ue,lc] = sm.get_ue_bsr(enb,ue,lc=lc)    
                

    def get_phy_statistics(self, sm):
            
        # To hook. All of them 
        for enb in range(0, sm.get_num_enb()) :
            self.enb_dl_phy_tti_num[enb]=0 # TTI number or subframe number
            self.enb_dl_phy_sfn[enb]=0 # Super frame number
            for ue in range(0, sm.get_num_ue(enb=enb)) :

                self.enb_ue_dl_phy_harq_acked_bytes_w[enb,ue]=0
                self.enb_ue_dl_phy_harq_etx_w[enb,ue]=0
                self.enb_ue_ul_phy_harq_acked_bytes_w[enb,ue]=0
                self.enb_ue_ul_phy_harq_etx_w[enb,ue]=0

        self.process_harq_stats(sm)


    def get_rrc_statistics(self, sm):
       
        for enb in range(0, sm.get_num_enb()) :
            for ue in range(0, sm.get_num_ue(enb=enb)) :
        
                self.enb_ue_rsrp[enb,ue]=sm.get_ue_rsrp(enb,ue)
                self.enb_ue_rsrq[enb,ue]=sm.get_ue_rsrq(enb,ue)

                # if sm.get_ue_measid(enb,ue) == -1 : # and monitoring_app.enb_ue_trigger_meas[enb] == 1 :
                #    self.log.info('2.1 Enable RRC trigger measurement event for eNB ' + str(enb))
                #    rrc.trigger_meas()

    def get_ul_signal_statistics(self, sm):

        for enb in range(0, sm.get_num_enb()) :
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                self.enb_ue_ul_snr[enb,ue]=0 # To hook 


    def process_harq_stats(self, sm):
        print "processing harq stats"
        for enb in range(0, sm.get_num_enb()) :
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                # This is the harq_pid of the TB in this TTI for which the mac stats was just reported. 
                #hid = sm.get_harq_pid(enb=enb,ue=ue)
                hid = int(self.enb_dl_pdcp_sfn[enb]) % 8
                # Harq round for the harq_pid
                curr_round = sm.get_harq_round(enb=enb,ue=ue)
                log.info('TEST sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) + 
                        ' harq_pid ' + str(hid) +      
                        ' curr_round ' + str(curr_round))
                # Save this round as prev round to use later
                #prev_round[enb,ue,hid]=curr_round
                # increment the ttl counter. To be done every TTI.
                self.enb_ue_hid_dl_phy_tx_delay_cnt[enb,ue,hid]+=1
                log.info('TEST sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) + 
                        ' harq_pid ' + str(hid) +      
                        ' enb_ue_hid_dl_phy_tx_delay_cnt ' + str(self.enb_ue_hid_dl_phy_tx_delay_cnt[enb,ue,hid]))

                # Stopping condition to save the counters.
                # The stopping condition is either an ack is received or the TB is dropped.
                # Currently we are not handling the event of a TB being dropped after mac retx
                # This is for when a tx is complete and a new tx has begun. 
                # The curr_round can change from <8 to 8 meaning a multiple attempt tx just finished or
                # It can change from 8 to 8 meaning that a single attempt tx just finished. 
                # Either ways if the curr_round is 8 then a previous tx was successful.
                if curr_round == 8 :

                #if (curr_round == 8 and (prev_tx_was_new == True ) :
                    # save the ttl and reset it
                    self.enb_ue_dl_phy_tx_ack_delay[enb,ue]=self.enb_ue_hid_dl_phy_tx_delay_cnt[enb,ue,hid]
                    self.enb_ue_hid_dl_phy_tx_delay_cnt[enb,ue,hid]=0
                    # save the tx attempt counter and then reset it
                    self.enb_ue_dl_phy_tx_ack_attempts[enb,ue]=self.enb_ue_hid_dl_phy_tx_attempts_cnt[enb,ue,hid]
                    log.info('TEST sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) +     
                        ' enb_ue_dl_phy_tx_ack_attempts ' + str(self.enb_ue_dl_phy_tx_ack_attempts[enb,ue]))
                    self.enb_ue_hid_dl_phy_tx_attempts_cnt[enb,ue,hid]=1
                    # reset the boolean to track if previous Tx was new
                    #prev_tx_was_new=False
                    # Number of bytes successfully delivered
                    # Find the TBS of the TB that was just acked using the ue_id and harq_pid.
                    # Then, I will need to save enb_ue_hid_tbs[enb,ue,hid] in each TTI
                    # OR
                    # It can also be found using the delay counter if I save the tbs values over windows.
                    # First option seems cleaner to understand and implement, so I shall use that.  
                    # The prev_hid_tbs is used here because the get_mac_stats will replace 
                    # this value when the new TB is received on the same harq_id in this current TTI
                    # get_phy_stats is called after get_mac_stats, so to save the ttrouble of always 
                    # ensuring the order we can just have another variable
                    self.enb_ue_dl_phy_acked_bytes[enb,ue]=self.enb_ue_prev_hid_tbs[enb,ue,hid]
                    log.info('TEST sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) +      
                        ' enb_ue_dl_phy_acked_bytes ' + str(self.enb_ue_dl_phy_acked_bytes[enb,ue]))
                    # set the prev_hid_tbs to the current value for use when round is complete. 
                    self.enb_ue_prev_hid_tbs[enb,ue,hid] = self.enb_ue_dl_mac_tbs[enb,ue]

                # I think this code block is redundant
                    
                # # Update the counters 
                # # If current TTI is a first time transmission TTI
                # # If current round is 8 then isn't it impled that it is a Tx TTI ?? 
                # if enb_ue_dl_mac_rb[enb,ue] > 0 and curr_round == 8:
                #     # This is actually current_tx_is_new, but will be interpreted as 
                #     # prev_tx_was_new at the end of the tx attempt
                #     #prev_tx_was_new = True
                #     # this is a new Tx so attempt counter starts from 1
                #     enb_ue_hid_dl_phy_tx_attempts_cnt[enb,ue,hid]=1
                    #
                # else if it was a retx TTI
                # again if the harq round is < 8 then it must be a retx round right ? 
                # So I dont need to check for retx_prbs
                elif curr_round < 8 :
                #elif enb_ue_dl_mac_retx_rb[enb,ue] > 0 and harq_round < 8 :
                   # if (prev_round[enb,ue,hid]+1)%8 == 1 :
                    self.enb_ue_hid_dl_phy_tx_attempts_cnt[enb,ue,hid]+=1
                    log.info('TEST sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) + 
                        ' harq_pid ' + str(hid) +      
                        ' enb_ue_hid_dl_phy_tx_attempts_cnt ' + str(self.enb_ue_hid_dl_phy_tx_attempts_cnt[enb,ue,hid]))

                else:
                    print "I DON'T KNOW WHY I'M HERE !!!"


    def print_logs(self,sm):
        for enb in range(0, sm.get_num_enb()) :
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                # PDCP
                log.info('sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) +
                        ' enb_ue_dl_pdcp ' + str(self.enb_ue_dl_pdcp[enb,ue]) +
                        ' enb_ue_dl_pdcp_bytes ' + str(self.enb_ue_dl_pdcp_bytes[enb,ue]) +
                        ' enb_ue_dl_pdcp_aiat ' + str(self.enb_ue_dl_pdcp_aiat[enb,ue]))
                log.info('------------------------------------------------------------------------------------')
                log.info('sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) +        
                        ' enb_ue_ul_pdcp ' + str(self.enb_ue_ul_pdcp[enb,ue]) +
                        ' enb_ue_ul_pdcp_bytes ' + str(self.enb_ue_ul_pdcp_bytes[enb,ue]) +
                        ' enb_ue_ul_pdcp_aiat ' + str(self.enb_ue_ul_pdcp_aiat[enb,ue]) +
                        ' enb_ue_ul_pdcp_oo ' + str(self.enb_ue_ul_pdcp_oo[enb,ue]))
                log.info('------------------------------------------------------------------------------------')
                log.info('sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) +        
                        ' enb_ue_dl_pdcp_w ' + str(self.enb_ue_dl_pdcp_w[enb,ue]) +
                        ' enb_ue_dl_pdcp_bytes_w ' + str(self.enb_ue_dl_pdcp_bytes_w[enb,ue]) +
                        ' enb_ue_dl_pdcp_aiat_w ' + str(self.enb_ue_dl_pdcp_aiat_w[enb,ue]))
                log.info('------------------------------------------------------------------------------------')
                # RLC
                for lc in range(0,3) :
                    log.info('sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                            ' tti=' + str(0) + 
                            ' eNB ' + str(enb) +
                            ' ue ' + str(ue) +
                            ' lc ' + str(lc) +        
                            ' enb_ue_dl_rlc_queue_len_bytes ' + str(self.enb_ue_dl_rlc_queue_len_bytes[enb,ue,lc]) +
                            ' enb_ue_dl_rlc_queue_num_pdu ' + str(self.enb_ue_dl_rlc_queue_num_pdu[enb,ue,lc]) +
                            ' enb_ue_dl_rlc_hol_delay ' + str(self.enb_ue_dl_rlc_hol_delay[enb,ue,lc]))
                # MAC    
                log.info('------------------------------------------------------------------------------------')
                log.info('sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) +        
                        ' enb_ue_dl_mac_rb ' + str(self.enb_ue_dl_mac_rb[enb,ue]) +
                        ' enb_ue_dl_mac_retx_rb ' + str(self.enb_ue_dl_mac_retx_rb[enb,ue]) +
                        ' enb_ue_dl_mac_wcqi ' + str(self.enb_ue_dl_mac_wcqi[enb,ue]) +
                        ' enb_ue_dl_mac_bytes ' + str(self.enb_ue_dl_mac_bytes[enb,ue]) +
                        ' enb_ue_dl_mac_tbs ' + str(self.enb_ue_dl_mac_tbs[enb,ue]) +
                        ' enb_ue_dl_mac_mcs ' + str(self.enb_ue_dl_mac_mcs[enb,ue]))

                log.info('------------------------------------------------------------------------------------')
                log.info('sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) + 
                        ' ue_phr ' + str(self.ue_phr[enb,ue]) +
                        ' enb_ue_ul_mac_rb ' + str(self.enb_ue_ul_mac_rb[enb,ue]) +
                        ' enb_ue_ul_mac_retx_rb ' + str(self.enb_ue_ul_mac_retx_rb[enb,ue]) +
                        ' enb_ue_ul_mac_bytes ' + str(self.enb_ue_ul_mac_bytes[enb,ue]) +
                        ' enb_ue_ul_mac_tbs ' + str(self.enb_ue_ul_mac_tbs[enb,ue]) +
                        ' enb_ue_ul_mac_mcs ' + str(self.enb_ue_ul_mac_mcs[enb,ue]))
                log.info('------------------------------------------------------------------------------------')
                for lc in range(0,4) :
                    log.info('sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) +
                        ' lc ' + str(lc) +
                        ' lc_ue_bsr ' + str(self.lc_ue_bsr[enb,ue,lc]))

                log.info('------------------------------------------------------------------------------------')
                log.info('sfn=' + str(self.enb_dl_pdcp_sfn[enb]) + 
                        ' tti=' + str(0) + 
                        ' eNB ' + str(enb) +
                        ' ue ' + str(ue) + 
                        ' enb_ue_rsrp ' + str(self.enb_ue_rsrp[enb,ue]) +
                        ' enb_ue_rsrq ' + str(self.enb_ue_rsrq[enb,ue]))
                log.info('------------------------------------------------------------------------------------')
                log.info('------------------------------------------------------------------------------------')

    def get_graphs_data(self, sm):
	output = []
	for enb in range(0, sm.get_num_enb()) :
            for ue in range(0, sm.get_num_ue(enb=enb)):
	        if self.enb_ue_dl_pdcp_bytes[enb, ue] > 20: # LIMIT 
		      output.append({'enb':enb,'ue':ue,'dl_pdcp_bytes':self.enb_ue_dl_pdcp_bytes[enb, ue]})
	print(output)
	return output



    def run(self, sm,rrc):
        # update the all stats 
        sm.stats_manager('all')

        self.log.info('2.1 Gather PDCP statistics')
        monitoring_app.get_pdcp_statistics(sm)

        self.log.info('2.2 Gather RLC statistics')
        monitoring_app.get_rlc_statistics(sm)

        self.log.info('2.3 Gather MAC statistics')
        monitoring_app.get_mac_statistics(sm)

        self.log.info('2.4 Gather PHY statistics')
        monitoring_app.get_phy_statistics(sm)

        self.log.info('2.5 Gather RRC statistics')
        monitoring_app.get_rrc_statistics(sm)     

        monitoring_app.print_logs(sm)   
       
        
        t = Timer(monitoring_app.period, self.run,kwargs=dict(sm=sm,rrc=rrc))
        t.start()
        
    def handle_open_data(self, client, message):
	   client.send(json.dumps({'monitoring_app':'please fill this function'}))

# main thread function - because shows GUI 
def visualisation(monitoring_app, fm, sm, period, enable):
    graphs = []
    while True:
	time.sleep(period)
	if enable:
	    data = monitoring_app.get_graphs_data(sm)
            used = []
	    for i in data:
		name = str(i['enb'])+'-'+str(i['ue'])
		if not name in graphs: 
 		    graphs.append(name)
		    fm.create(name=name)
		    fm.show(name=name, x=1, y=i['dl_pdcp_bytes'], fig_type=app_graphs.FigureType.Plot)
		elif name in graphs:
		    fm.append(name=name, y=i['dl_pdcp_bytes'], fig_type=app_graphs.FigureType.Plot)
		used.append(name)
		fm.update(name=name)
	    for i, name in enumerate(graphs):
		if not name in used:
		    fm.close(name=name)
		    del graphs[i]
		    
	         


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
    parser.add_argument('--app-period',  metavar='[option]', action='store', type=float,
                        required=False, default=1, 
                        help='set the period of the app: 1s (default)')
    parser.add_argument('--graph', action='store_true',
                        required=False, default=False, 
                        help='set true to visualize (default true)')
    parser.add_argument('--graph-period',  metavar='[option]', action='store', type=int,
                        required=False, default=5, 
                        help='set the period of the app visualisation: 5s (default)')
    parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
                        required=False, default='test', 
                        help='Set the app operation mode either with FlexRAN or with the test json files: test(default), sdk')
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='info', 
                        help='set the log level: debug, info (default), warning, error, critical')
   
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args() 

    log=flexran_sdk.logger(log_level=args.log).init_logger()
    


    # If this block is uncommented then monitoring app does not do the run loop.
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

    fm = app_graphs.FigureManager() 
    
    py3_flag = version_info[0] > 2 
    sm.log.info('1. Reading the status of the underlying eNBs')
    sm.stats_manager('all')
    monitoring_app = monitoring_app(log=log,
                                url=args.url,
                                port=args.port,
                                url_app=args.url_app,
                                port_app=args.port_app,
                                log_level=args.log,
                                op_mode=args.op_mode)

    monitoring_app.period=args.app_period
    monitoring_app.init_data_holders(sm)
    log.info('App period is set to : ' + str(monitoring_app.period))
    monitoring_app.run(sm=sm,rrc=rrc)

    t2 = Timer(1,app_sdk.run_all_apps) 
    t2.start()
    
    visualisation(monitoring_app, fm, sm, args.graph_period, args.graph)
