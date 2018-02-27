import json
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
import math
import monitoring_app

class data_collection_app(object):
    ### Data holders for data collection
    
    ## Per Wm stats
    # RSRP, RSRQ and RSSI are reported by the UE with a minimum period of 120 ms.
    dc_enb_ue_dl_rsrp={}#[enb,ue]  
    dc_enb_ue_dl_rsrq={}#[enb,ue]

    dc_enb_ue_ul_rssi={}#[enb,ue] # yes

    ## First second and third moments of these metrics are obtaind in time window W_m
    # Dl CQI received at eNB every (1 ms ?)
    dc_enb_ue_dl_cqi_moments={}#[enb,ue][] # yes
    # Time between receiving a MAC SDU and sending the MAC PDU to PHY
    # This is the time spent waiting to be assigned DL PRB resources.  
    dc_enb_ue_dl_sch_delay_moments={}#[enb,ue][]
    # Time between receiving a PHY SDU (TB) and receiving a 
    # HARQ ACK for the sent PHY PDU 
    dc_enb_ue_dl_succ_rx_delay_moments={}#[enb,ue][]
    # Time between receiving a MAC SDU and receiving a 
    # HARQ ACK for the sent PHY PDU. This is a combination of 
    # the scheduling and the phy delays  
    dc_enb_ue_dl_mac_phy_delay_moments={}#[enb,ue][]
    # Expected number of transmissions. Number of attempts taken to successfully deliver a TB
    # i.e. to receive a HARQ ACK for a TB
    dc_enb_ue_dl_etx_moments={}#[enb,ue][]
    # PDCP pkt level stats
    dc_enb_ue_dl_pdcp_sdu_pkt_len_moments={}#[enb,ue][]
    dc_enb_ue_dl_pdcp_sdu_inter_pkt_time_moments={}#[enb,ue][]
    dc_enb_ue_dl_pdcp_sdu_arr_rate={}#[enb,ue][]

    # Ul MCS obtained from uplink reception of TBs
    dc_enb_ue_ul_mcs_moments={}#[enb,ue][cqi]
    # Time between the eNB receiving a scheduling request from a UE and time instant at 
    # which resource is granted to the UE. 
    dc_enb_ue_ul_sch_delay_moments={}#[enb,ue][]
    # Time between the instant at which UL data was expected (based on UL grant) 
    # and time at which HARQ ACK was sent to the UE
    dc_enb_ue_ul_succ_rx_delay_moments={}#[enb,ue][]
    # Expected number of transmissions. Number of attempts taken to successfully deliver a TB
    # i.e. to receive a HARQ ACK for a TB
    dc_enb_ue_ul_etx_moments={}#[enb,ue][]

    measurement_time_window_ms=100 # ms
    dc_enb_ue_wm_sample_counter={}#[enb,ue]


    ## Per TTI stats
    # TTI number
    dc_enb_ue_dl_tti_seq_num={}#[enb]
    # Dl Frame number
    dc_enb_ue_dl_frame_seq_num={}#[enb]

    # Dl number of PRBs allocated to a UE in this TTI
    dc_enb_ue_dl_num_prb_sch={}#[enb,ue]
    # Dl PDCP SDU bytes received  
    dc_enb_ue_dl_pdcp_sdu_bytes={}#[enb,ue]
    # Dl RLC SDU bytes received  
    dc_enb_ue_dl_rlc_sdu_bytes={}#[enb,ue]
    # Dl MAC SDU bytes received
    dc_enb_ue_dl_mac_sdu_bytes={}#[enb,ue]
    # MAC queue length. This is when the bytes are waiting to be scheduled. 
    dc_enb_ue_dl_mac_queue_len_bytes={}#[enb,ue]
    # Dl TBS of TB of UE in this TTI (PHY SDU bytes)
    dc_enb_ue_dl_tbs={}#[enb,ue]
    # Dl CQI for UE
    dc_enb_ue_dl_cqi={}#[enb,ue]    
    # Dl number of bytes ACKed (bytes successfully received at UE) 
    dc_enb_ue_dl_phy_harq_acked_bytes={}#[enb,ue]

    # Ul number of PRBs granted to a UE 
    dc_enb_ue_ul_num_prb_sch={}#[enb,ue]
    # Ul TBS of TB from UE
    dc_enb_ue_ul_tbs={}#[enb,ue]
    # Ul MCS from UE
    dc_enb_ue_ul_mcs={}#[enb,ue]   
    # Number of bytes received successfully at eNB
    dc_enb_ue_ul_phy_harq_acked_bytes={}#[enb,ue]
    
    tti_ms=1 # ms
    dc_enb_ue_tti_sample_counter={}#[enb,ue]

    tti_log_file = None
    wm_log_file = None



    # Class constructor, which is run when a class object is created. 
    # This can accept arguments that are passed when the object is created
    def __init__(self,measurement_time_window_ms):
        self.measurement_time_window_ms = measurement_time_window_ms
       # self.initialize_data_holders(self)

    def __del__(self):
            self.tti_log_file.close()
            self.wm_log_file.close()

    # Initialize the dictionaries and arrays required to store the metrics 
    # obtained from the monitroing_app.
    # An initialization function for the aquamet variables because the 
    # initialization depends on the number of ues and enbs and window size, 
    # so it should be done after the rest of the things are initialized.
    def initialize_data_holders(self):
        for enb in range(0, sm.get_num_enb()) :    
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                data_collection_app.dc_enb_ue_dl_rsrp[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_dl_rsrq[enb,ue]=0#[enb,ue]

                data_collection_app.dc_enb_ue_ul_rssi[enb,ue]=0#[enb,ue]

                data_collection_app.dc_enb_ue_dl_cqi_moments[enb,ue]=[]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_sch_delay_moments[enb,ue]=[]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_succ_rx_delay_moments[enb,ue]=[]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_mac_phy_delay_moments[enb,ue]=[]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_etx_moments[enb,ue]=[]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_pdcp_sdu_pkt_len_moments[enb,ue]=[]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_pdcp_sdu_inter_pkt_time_moments[enb,ue]=[]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_pdcp_sdu_arr_rate[enb,ue]=[]#[enb,ue][]

                data_collection_app.dc_enb_ue_ul_mcs_moments[enb,ue]=[]#[enb,ue][]
                data_collection_app.dc_enb_ue_ul_sch_delay_moments[enb,ue]=[]#[enb,ue][]
                data_collection_app.dc_enb_ue_ul_succ_rx_delay_moments[enb,ue]=[]#[enb,ue][]
                data_collection_app.dc_enb_ue_ul_etx_moments[enb,ue]=[]#[enb,ue][]

                data_collection_app.dc_enb_ue_dl_tti_seq_num[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_dl_frame_seq_num[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_dl_num_prb_sch[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_dl_pdcp_sdu_bytes[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_dl_rlc_sdu_bytes[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_dl_mac_sdu_bytes[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_dl_mac_queue_len_bytes[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_dl_tbs[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_dl_cqi[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_dl_phy_harq_acked_bytes[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_ul_num_prb_sch[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_ul_tbs[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_ul_mcs[enb,ue]=0#[enb,ue]
                data_collection_app.dc_enb_ue_ul_phy_harq_acked_bytes[enb,ue]=0#[enb,ue]

                tti_log_file = open("tti_log.txt", "w")
                wm_log_file = open("wm_log.txt", "w")


    def log_tti_measurements (self,sm,monitoring_app):
        for enb in range(0,sm.get_num_enb()) :
            # WARNING !! Does this imply that the ues of each enb always ave ids starting from 1 ? 
            # How can we uniquely identify ues across enbs ???
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                # Increment sample counter that counts number of TTIs elapsed since begin of log
                data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]+=1

                data_collection_app.dc_enb_ue_dl_tti_seq_num[enb,ue]=monitoring_app.enb_ue_dl_tti_seq_num[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_dl_frame_seq_num[enb,ue]=monitoring_app.enb_ue_dl_frame_seq_num[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_dl_num_prb_sch[enb,ue]=monitoring_app.enb_ue_dl_num_prb_sch[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_dl_pdcp_sdu_bytes[enb,ue]=monitoring_app.enb_ue_dl_pdcp_sdu_bytes[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_dl_rlc_sdu_bytes[enb,ue]=monitoring_app.enb_ue_dl_rlc_sdu_bytes[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_dl_mac_sdu_bytes[enb,ue]=monitoring_app.enb_ue_dl_mac_sdu_bytes[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_dl_mac_queue_len_bytes[enb,ue]=monitoring_app.enb_ue_dl_mac_queue_len_bytes[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_dl_tbs[enb,ue]=monitoring_app.enb_ue_dl_tbs[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_dl_cqi[enb,ue]=monitoring_app.enb_ue_dl_cqi[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_dl_phy_harq_acked_bytes[enb,ue]=monitoring_app.enb_ue_dl_phy_harq_acked_bytes[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_ul_num_prb_sch[enb,ue]=monitoring_app.enb_ue_ul_num_prb_sch[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_ul_tbs[enb,ue]=monitoring_app.enb_ue_ul_tbs[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_ul_mcs[enb,ue]=monitoring_app.enb_ue_ul_mcs[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_ul_phy_harq_acked_bytes[enb,ue]=monitoring_app.enb_ue_ul_phy_harq_acked_bytes[enb,ue]#[enb,ue]


                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_tti_seq_num ' + str(data_collection_app.dc_enb_ue_dl_tti_seq_num[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_frame_seq_num ' + str(data_collection_app.dc_enb_ue_dl_frame_seq_num[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_num_prb_sch ' + str(data_collection_app.dc_enb_ue_dl_num_prb_sch[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_pdcp_sdu_bytes ' + str(data_collection_app.dc_enb_ue_dl_pdcp_sdu_bytes[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_rlc_sdu_bytes ' + str(data_collection_app.dc_enb_ue_dl_rlc_sdu_bytes[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_mac_sdu_bytes ' + str(data_collection_app.dc_enb_ue_dl_mac_sdu_bytes[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_mac_queue_len_bytes ' + str(data_collection_app.dc_enb_ue_dl_mac_queue_len_bytes[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_tbs ' + str(data_collection_app.dc_enb_ue_dl_tbs[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_cqi ' + str(data_collection_app.dc_enb_ue_dl_cqi[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_phy_harq_acked_bytes ' + str(data_collection_app.dc_enb_ue_dl_phy_harq_acked_bytes[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_ul_num_prb_sch ' + str(data_collection_app.dc_enb_ue_ul_num_prb_sch[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_ul_tbs ' + str(data_collection_app.dc_enb_ue_ul_tbs[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_ul_mcs ' + str(data_collection_app.dc_enb_ue_ul_mcs[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_ul_phy_harq_acked_bytes ' + str(data_collection_app.dc_enb_ue_ul_phy_harq_acked_bytes[enb,ue]))

                tti_log_file.write(str(data_collection_app.dc_enb_ue_tti_sample_counter[enb,ue]) + 
                    ' ' + str(enb) + ' ' + str(ue) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_dl_tti_seq_num[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_dl_frame_seq_num[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_dl_num_prb_sch[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_dl_pdcp_sdu_bytes[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_dl_rlc_sdu_bytes[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_dl_mac_sdu_bytes[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_dl_mac_queue_len_bytes[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_dl_tbs[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_dl_cqi[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_dl_phy_harq_acked_bytes[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_ul_num_prb_sch[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_ul_tbs[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_ul_mcs[enb,ue]) + ' ')
                tti_log_file.write(str(data_collection_app.dc_enb_ue_ul_phy_harq_acked_bytes[enb,ue]) + '\n')



    def log_wm_measurements (self,sm,monitoring_app):
        for enb in range(0,sm.get_num_enb()) :
            # WARNING !! Does this imply that the ues of each enb always ave ids starting from 1 ? 
            # How can we uniquely identify ues across enbs ???
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]+=1

                data_collection_app.dc_enb_ue_dl_rsrp[enb,ue]=monitoring_app.enb_ue_dl_rsrp[enb,ue]#[enb,ue]
                data_collection_app.dc_enb_ue_dl_rsrq[enb,ue]=monitoring_app.enb_ue_dl_rsrq[enb,ue]#[enb,ue]

                data_collection_app.dc_enb_ue_ul_rssi[enb,ue]=monitoring_app.enb_ue_ul_rssi[enb,ue]#[enb,ue]

                data_collection_app.dc_enb_ue_dl_cqi_moments[enb,ue]=monitoring_app.enb_ue_dl_cqi_moments[enb,ue]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_sch_delay_moments[enb,ue]=monitoring_app.enb_ue_dl_sch_delay_moments[enb,ue]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_succ_rx_delay_moments[enb,ue]=monitoring_app.enb_ue_dl_succ_rx_delay_moments[enb,ue]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_mac_phy_delay_moments[enb,ue]=monitoring_app.enb_ue_dl_mac_phy_delay_moments[enb,ue]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_etx_moments[enb,ue]=monitoring_app.enb_ue_dl_etx_moments[enb,ue]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_pdcp_sdu_pkt_len_moments[enb,ue]=monitoring_app.enb_ue_dl_pdcp_sdu_pkt_len_moments[enb,ue]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_pdcp_sdu_inter_pkt_time_moments[enb,ue]=monitoring_app.enb_ue_dl_pdcp_sdu_inter_pkt_time_moments[enb,ue]#[enb,ue][]
                data_collection_app.dc_enb_ue_dl_pdcp_sdu_arr_rate[enb,ue]=monitoring_app.enb_ue_dl_pdcp_sdu_arr_rate[enb,ue]#[enb,ue][]

                data_collection_app.dc_enb_ue_ul_mcs_moments[enb,ue]=monitoring_app.enb_ue_ul_mcs_moments[enb,ue]#[enb,ue][]
                data_collection_app.dc_enb_ue_ul_sch_delay_moments[enb,ue]=monitoring_app.enb_ue_ul_sch_delay_moments[enb,ue]#[enb,ue][]
                data_collection_app.dc_enb_ue_ul_succ_rx_delay_moments[enb,ue]=monitoring_app.enb_ue_ul_succ_rx_delay_moments[enb,ue]#[enb,ue][]
                data_collection_app.dc_enb_ue_ul_etx_moments[enb,ue]=monitoring_app.enb_ue_ul_etx_moments[enb,ue]#[enb,ue][]

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_rsrp ' + str(data_collection_app.dc_enb_ue_dl_rsrp[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_rsrq ' + str(data_collection_app.dc_enb_ue_dl_rsrq[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_ul_rssi ' + str(data_collection_app.dc_enb_ue_ul_rssi[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_cqi_moments ' + str(data_collection_app.dc_enb_ue_dl_cqi_moments[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_sch_delay_moments ' + str(data_collection_app.dc_enb_ue_dl_sch_delay_moments[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_succ_rx_delay_moments ' + str(data_collection_app.dc_enb_ue_dl_succ_rx_delay_moments[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_mac_phy_delay_moments ' + str(data_collection_app.dc_enb_ue_dl_mac_phy_delay_moments[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_etx_moments ' + str(data_collection_app.dc_enb_ue_dl_etx_moments[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_pdcp_sdu_pkt_len_moments ' + str(data_collection_app.dc_enb_ue_dl_pdcp_sdu_pkt_len_moments[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_pdcp_sdu_inter_pkt_time_moments ' + str(data_collection_app.dc_enb_ue_dl_pdcp_sdu_inter_pkt_time_moments[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_dl_pdcp_sdu_arr_rate ' + str(data_collection_app.dc_enb_ue_dl_pdcp_sdu_arr_rate[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_ul_mcs_moments ' + str(data_collection_app.dc_enb_ue_ul_mcs_moments[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_ul_sch_delay_moments ' + str(data_collection_app.dc_enb_ue_ul_sch_delay_moments[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_ul_succ_rx_delay_moments ' + str(data_collection_app.dc_enb_ue_ul_succ_rx_delay_moments[enb,ue]))

                log.info('k=' + str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' enb_ue_ul_etx_moments ' + str(data_collection_app.dc_enb_ue_ul_etx_moments[enb,ue]))

                wm_log_file.write(str(data_collection_app.dc_enb_ue_wm_sample_counter[enb,ue]) + 
                    ' ' + str(enb) + ' ' + str(ue) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_dl_rsrp[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_dl_rsrq[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_ul_rssi[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_dl_cqi_moments[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_dl_sch_delay_moments[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_dl_succ_rx_delay_moments[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_dl_mac_phy_delay_moments[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_dl_etx_moments[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_dl_pdcp_sdu_pkt_len_moments[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_dl_pdcp_sdu_inter_pkt_time_moments[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_dl_pdcp_sdu_arr_rate[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_ul_mcs_moments[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_ul_sch_delay_moments[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_ul_succ_rx_delay_moments[enb,ue]) + ' ')
                wm_log_file.write(str(data_collection_app.dc_enb_ue_ul_etx_moments[enb,ue]) + '\n')


    #  This runs in a loop. At the end of this function it is initilized again with a timer.
    # So this measn that we get the monitroing info periodically with this period.
    def run_tti(self, sm, rrc, monitoring_app):
        log.info('TTI timer fired')
        log.info('Reading the status of the underlying eNBs')
        sm.stats_manager('all')
        log.info('Gather measurements')
        monitoring_app.get_rsrp_rsrq(sm)
        monitoring_app.get_tti_level_measurements(sm)
        data_collection_app.log_tti_measurements(sm,monitoring_app)
        
        t1 = Timer(data_collection_app.tti_ms, 
            self.run,kwargs=dict(sm=sm,rrc=rrc,monitoring_app=monitoring_app))
        t1.start()


    #  This runs in a loop. At the end of this function it is initilized again with a timer.
    # So this measn that we get the monitroing info periodically with this period.
    def run_wm(self, sm, rrc, monitoring_app):
        log.info('Wm timer fired')
        log.info('Reading the status of the underlying eNBs')
        sm.stats_manager('all')
        log.info('Gather measurements')
        monitoring_app.get_rsrp_rsrq(sm)
        monitoring_app.get_wm_level_measurements(sm)
        data_collection_app.log_wm_measurements(sm,monitoring_app)
        
        t2 = Timer(data_collection_app.wm_ms, 
            self.run,kwargs=dict(sm=sm,rrc=rrc,monitoring_app=monitoring_app))
        t2.start()



# Main function 
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
    # Create logger object
    log=flexran_sdk.logger(log_level=args.log).init_logger()
    # Create monitoring_app object
    monitoring_app = monitoring_app.monitoring_app(log=log,
                                    url=args.url,
                                    port=args.port,
                                    url_app=args.url_app,
                                    port_app=args.port_app,
                                    log_level=args.log,
                                    op_mode=args.op_mode)
    # Create stats_manager object
    sm = flexran_sdk.stats_manager(log=log,
                                   url=args.url,
                                   port=args.port,
                                   op_mode=args.op_mode)
    # Create rrc_trigger_meas object
    rrc= flexran_sdk.rrc_trigger_meas(log=log,
                                      url=args.url,
                                      port=args.port,
                                      op_mode=args.op_mode)
    
    # Does this mean it does not work for python version 3 ???
    py3_flag = version_info[0] > 2 
    # This needs to be called after stats_manager has been instansiated 
    # since it used information from stats_manager
    data_collection_app = data_collection_app(measurement_time_window_ms=100)
    data_collection_app.initialize_data_holders()
    # Start the periodic timer for each TTI (1 ms)
    t1 = Timer(data_collection_app.tti_ms, data_collection_app.run_tti,kwargs=dict(sm=sm,rrc=rrc,monitoring_app=monitoring_app))
    t1.start() 
    # Start the periodic timer for each Wm (adjustable)
    t2 = Timer(data_collection_app.wm_ms, data_collection_app.run_wm,kwargs=dict(sm=sm,rrc=rrc,monitoring_app=monitoring_app))
    t2.start()

            
