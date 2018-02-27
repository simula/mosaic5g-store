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
#import matplotlib.pyplot as plt


class aquamet_app(object):
    # Data holders for aquamet

    # Input arrival rate downlink data for each ue in IP pkts/second 
    # as measured at the enb PDCP 
    aq_enb_ue_dl_pdcp_sdu_arr_rate_pps={}#[enb,ue][wind_ind]
    # Average pkt length in bytes of the input IP pkts at the enb PDCP layer
    aq_enb_ue_dl_pdcp_pkt_len_bytes={}#[enb,ue][wind_ind]
    # Noise at ue
    aq_ue_dl_noise={}#[ue]
    # RSRP in dBm
    aq_enb_ue_dl_rsrp={}#[enb,ue]
    # RSRQ in dB
    aq_enb_ue_dl_rsrq={}#[enb,ue]
    # Estimated downlink SNR from RSRP and noise
    aq_enb_ue_dl_est_snr={}#[enb,ue] in dB
    # The range of CQI is 0-15
    aq_enb_ue_dl_est_cqi={}#[enb,ue]
    # The range of CQI is 0-15
    aq_enb_ue_dl_meas_cqi={}#[enb,ue]
    # Estimated MCS from SNR. The range of MCS is 0-27
    aq_enb_ue_dl_est_mcs={}#[enb,ue][wind_ind]
    # Estimate of downlink resources allocated to a ue, in terms of fraction 
    # of total available resources in PRBs.
    aq_enb_ue_dl_est_ratio_of_frame_alloc={}#[enb,ue][wind_ind]
    aq_enb_ue_dl_meas_ratio_of_frame_alloc={}#[enb,ue][wind_ind]
    # Downlink Attainable throughput estimated for which association set  ???
    # in Kbps
    aq_enb_ue_dl_att_thput={}#[enb,ue][wind_ind]
    # The ratio of (number of windows where measured throughput
    # is larger than ?? large than or equal to the throughput threshold) 
    #  to the total numner windows in sliding window
    # in Lbps
    aq_meas_prob_good_thput={}#[enb,ue]
    # The ratio of (number of windows where attainable throughput
    # is larger than ?? large than or equal to the throughput threshold) 
    #  to the total numner windows in sliding window  
    # ??? for which association set   
    aq_est_prob_good_thput={}#[enb,ue]
    # The range of MCS is 0-27
    aq_enb_ue_dl_meas_mcs={}#[enb,ue][wind_ind]
    # Downlink throughput in Kbps as measured at the ???? 
    aq_enb_ue_dl_meas_thput={}#[enb,ue][wind_ind]
    # Current associations of enb to ues
    current_assoc_set={}#[enb][set of ues]
    # Potential association set of enb to ues
    enb_assn_set={}#[enb][set of ues]
    # ????
    aq_enb_ue_dl_thput_ratio_error={}#[enb,ue]
    # ????
    aq_enb_ue_sample_counter={}#[enb,ue]
    # Aquamet monitoring parameters. 
    num_meas_in_slid_wind=5
    thput_tolerance=0.7   
    ue_dl_thput_threshold={}#Kbps
    measurement_time_window_ms=100 # ms
    aquamet_log_file = None



    # Class constructor, which is run when a class object is created. 
    # This can accept arguments that are passed when the object is created
    def __init__(self,measurement_time_window_ms, num_meas_in_slid_wind=5,thput_tolerance=0.7):
    #def __init__(self):
        self.num_meas_in_slid_wind = num_meas_in_slid_wind
        self.thput_tolerance = thput_tolerance
        self.measurement_time_window_ms = measurement_time_window_ms
        #self.initialize_data_holders(self)

    # Initialize the dictionaries and arrays required to store the metrics 
    # obtained from the monitroing_app.
    # An initialization function for the aquamet variables because the 
    # initialization depends on the number of ues and enbs and window size, 
    # so it should be done after the rest of the things are initialized. 
    def initialize_data_holders(self):
        for ncell in range(0, sm.get_num_enb()) :
            aquamet_app.current_assoc_set[ncell]=[]
            aquamet_app.enb_assn_set[ncell]=[]#[enb][set of ues]        
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                aquamet_app.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[ncell,ue]=[]#[enb,ue][wind_ind]
                aquamet_app.aq_enb_ue_dl_pdcp_pkt_len_bytes[ncell,ue]=[]#[enb,ue][wind_ind]
                aquamet_app.aq_enb_ue_dl_est_mcs[ncell,ue]=[]#[enb,ue][wind_ind]
                aquamet_app.aq_enb_ue_dl_meas_mcs[ncell,ue]=[]#[enb,ue][wind_ind]
                aquamet_app.aq_enb_ue_dl_meas_thput[ncell,ue]=[]#[enb,ue][wind_ind]
                aquamet_app.aq_enb_ue_dl_est_ratio_of_frame_alloc[ncell,ue]=[0]*aquamet_app.num_meas_in_slid_wind#[enb,ue][wind_ind]
                aquamet_app.aq_enb_ue_dl_meas_ratio_of_frame_alloc[ncell,ue]=[0]*aquamet_app.num_meas_in_slid_wind#[enb,ue][wind_ind]
                aquamet_app.aq_enb_ue_dl_att_thput[ncell,ue]=[0]*aquamet_app.num_meas_in_slid_wind#[enb,ue][wind_ind]
                aquamet_app.aq_est_prob_good_thput[ncell,ue]=0#[enb,ue]
                aquamet_app.aq_meas_prob_good_thput[ncell,ue]=0#[enb,ue]
                aquamet_app.aq_enb_ue_dl_est_snr[ncell,ue]=0#[enb,ue]
                aquamet_app.aq_ue_dl_noise[ue]=0#[ue]
                # aquamet in between variable
                aquamet_app.aq_enb_ue_dl_rsrp[ncell,ue]=0#[enb,ue]
                aquamet_app.aq_enb_ue_dl_rsrq[ncell,ue]=0#[enb,ue]
                aquamet_app.aq_enb_ue_dl_cqi[ncell,ue]=0#[enb,ue]
                aquamet_app.aq_enb_ue_sample_counter[ncell,ue]=0#[enb,ue]
                aquamet_app.aq_enb_ue_dl_thput_ratio_error[ncell,ue]=0#[enb,ue]
                aquamet_app.current_assoc_set[ncell].append(ue)

                aquamet_app.aquamet_log_file = open("aquamet_log.txt", "w")


    def aggregate_and_add_metrics_to_sliding_window(self,sm,monitoring_app):
        for enb in range(0,sm.get_num_enb()) :
            # WARNING !! Does this imply that the ues of each enb always ave ids starting from 1 ? 
            # How can we uniquely identify ues across enbs ???
            for ue in range(0, sm.get_num_ue(enb=enb)) :
                aquamet_app.aq_enb_ue_sample_counter[enb,ue]+=1
                # RSRP and noise are assumed to be in dBm. SNR is in dB
                aquamet_app.aq_enb_ue_dl_est_snr[enb,ue]=monitoring_app.enb_ue_dl_rsrp[enb,ue]-monitoring_app.ue_dl_noise[ue]
                log.info('k=' + str(monitoring_app.aq_enb_ue_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' RSRP ' + str(monitoring_app.enb_ue_dl_rsrp[enb,ue]))

                log.info('k=' + str(monitoring_app.aq_enb_ue_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' RSRQ ' + str(monitoring_app.enb_ue_dl_rsrq[enb,ue]))

                log.info('k=' + str(monitoring_app.aq_enb_ue_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' Receiver_noise ' + str(monitoring_app.ue_dl_noise[ue]))

                log.info('k=' + str(monitoring_app.aq_enb_ue_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' Est_SNR ' + str(aquamet_app.aq_enb_ue_dl_est_snr[enb,ue]))

                aquamet_log_file.write(str(monitoring_app.aq_enb_ue_sample_counter[enb,ue]) + 
                    ' ' + str(enb) + ' ' + str(ue))
                aquamet_log_file.write(str(monitoring_app.enb_ue_dl_rsrp[enb,ue]) + ' ')
                aquamet_log_file.write(str(monitoring_app.enb_ue_dl_rsrq[enb,ue]) + ' ')
                aquamet_log_file.write(str(monitoring_app.ue_dl_noise[ue]) + ' ')
                aquamet_log_file.write(str(aquamet_app.aq_enb_ue_dl_est_snr[enb,ue]) + ' ')

                # SNR to CQI table imported from rrm_app_vars.py 
                # Warning !! SNR cannot be negative here. It will cause an error
                if aquamet_app.aq_enb_ue_dl_est_snr[enb,ue] < 0 :
                    log.info('ERROR!!! SNR is negative')

                aquamet_app.aq_enb_ue_dl_est_cqi[enb,ue]=rrm_app_vars.snrdb_to_cqi.index([i for i in rrm_app_vars.snrdb_to_cqi if i <= aquamet_app.aq_enb_ue_dl_est_snr[enb,ue]][-1])
                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' Est_wCQI '+str(aquamet_app.aq_enb_ue_dl_est_cqi[enb,ue]))

                aquamet_log_file.write(str(aquamet_app.aq_enb_ue_dl_est_cqi[enb,ue]) + ' ')
                # CQI to MCS
                (aquamet_app.aq_enb_ue_dl_est_mcs[enb,ue]).insert(0,rrm_app_vars.cqi_to_mcs[aquamet_app.aq_enb_ue_dl_est_cqi[enb,ue]])
                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' est_mcs '+str(rrm_app_vars.cqi_to_mcs[aquamet_app.aq_enb_ue_dl_est_cqi[enb,ue]]))

                aquamet_log_file.write(str(rrm_app_vars.cqi_to_mcs[aquamet_app.aq_enb_ue_dl_est_cqi[enb,ue]]) + ' ')
                
                # Pkt length in bytes. If pkt len is 0 because no pkts were received
                if monitoring_app.enb_ue_pdcp_tx_w[enb,ue] == 0 :
                    ((aquamet_app.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb,ue]).insert(0,0.0))
                else :
                    ((aquamet_app.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb,ue]).insert(0,monitoring_app.enb_ue_pdcp_tx_bytes_w[enb,ue]
                                                                                        /float(monitoring_app.enb_ue_pdcp_tx_w[enb,ue])))
                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' PDCP_avg_pkt_len_bytes '+str(aquamet_app.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb,ue][0]))

                aquamet_log_file.write(str(aquamet_app.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb,ue][0]) + ' ')
                
                # Pkt arrival rate in pkts/second.
                ((aquamet_app.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb,ue]).insert(0,monitoring_app.enb_ue_pdcp_tx_w[enb,ue]*1000
                                                                                        /float(aquamet_app.measurement_time_window_ms)))   
                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + 
                    ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                    ' PDCP_sdu_arr_rate_kbps '+str(aquamet_app.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb,ue][0]))

                aquamet_log_file.write(str(aquamet_app.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb,ue][0]) + ' ')
                
                # Do this only if ue is being served by enb 
                if ue in aquamet_app.current_assoc_set[enb]: 
                    aquamet_app.aq_enb_ue_dl_meas_cqi[enb.ue] = monitoring_app.enb_ue_dlwcqi[enb,ue]
                    (aquamet_app.aq_enb_ue_dl_meas_mcs[enb,ue]).insert(0,rrm_app_vars.cqi_to_mcs[aquamet_app.aq_enb_ue_dl_meas_cqi[enb.ue]])#Don't know where to get this from. I need either a median or an average
                    log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + 
                        ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                        ' Meas_wCQI '+str(aquamet_app.aq_enb_ue_dl_meas_cqi[enb.ue]))

                    log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + 
                        ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                        ' Meas_MCS '+str(rrm_app_vars.cqi_to_mcs[aquamet_app.aq_enb_ue_dl_meas_cqi[enb.ue]]))

                    aquamet_log_file.write(str(aquamet_app.aq_enb_ue_dl_meas_cqi[enb.ue]) + ' ')
                    aquamet_log_file.write(str(rrm_app_vars.cqi_to_mcs[aquamet_app.aq_enb_ue_dl_meas_cqi[enb.ue]]) + ' ')

                    (aquamet_app.aq_enb_ue_dl_meas_ratio_of_frame_alloc[enb,ue]).insert(0,
                        monitoring_app.enb_ue_mac_avg_prb_alloc_in_frame[enb,ue])
                    
                    log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + 
                        ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                        ' Meas_X ' + str(aquamet_app.aq_enb_ue_dl_meas_ratio_of_frame_alloc[enb,ue][0]))

                    aquamet_log_file.write(str(aquamet_app.aq_enb_ue_dl_meas_ratio_of_frame_alloc[enb,ue][0]) + ' ')

                    ((aquamet_app.aq_enb_ue_dl_meas_thput[enb,ue]).insert(0,
                        monitoring_app.enb_ue_pdcp_tx_bytes_w[enb,ue]*8
                                /float(aquamet_app.measurement_time_window_ms)))
                                # WARNING !! not yet added the right trace source
                    
                    log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + 
                        ' eNB ' + str(enb) + ' UE ' + str(ue) + 
                        ' Meas_thput_kbps '+str(aquamet_app.aq_enb_ue_dl_meas_thput[enb,ue][0]))

                    aquamet_log_file.write(str(aquamet_app.aq_enb_ue_dl_meas_thput[enb,ue][0]) + ' ')

                # WARNING!!! make sure that the overflow of this is handled. currrently it is not.

                # Check if the number of aggregated measurements in the sliding window is > window_size
                if aquamet_app.aq_enb_ue_sample_counter[enb,ue] > aquamet_app.num_meas_in_slid_wind :
                    del aquamet_app.aq_enb_ue_dl_est_mcs[ncell,ue][monitoring_app.num_meas_in_slid_wind:]
                    del aquamet_app.aq_enb_ue_dl_meas_mcs[ncell,ue][monitoring_app.num_meas_in_slid_wind:]
                    del aquamet_app.aq_enb_ue_dl_meas_thput[ncell,ue][monitoring_app.num_meas_in_slid_wind:]
                    del aquamet_app.aq_enb_ue_dl_pdcp_pkt_len_bytes[ncell,ue][monitoring_app.num_meas_in_slid_wind:]
                    del aquamet_app.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[ncell,ue][monitoring_app.num_meas_in_slid_wind:]
                    # WARNING ! make sure I have truncated all the sliding windows in use


    def estimate_inst_att_thput_sliding_window_for_assosn_set(self,sm,monitoring_app):
        # Get estimated instataneous attainable troughput
        # the first structure object in stats belongs to the ue whose attainable throughput is to be estimated
        # ues for which this enb satisfies the probabilistic condition 
        # because I only want to do this for the target eNB

        for enb in range(0,sm.get_num_enb()) :
            for wind_ind in range(0,aquamet_app.num_meas_in_slid_wind) :
                num_HR=0
                sum_LR_X=0 
                est_resource_alloc=0
                est_thput_rlc=0
                aq_enb_active_ues=[]
                # Number of active UEs. For this k count how many UEs had non zero arrival rates             
                for ue in aquamet_app.enb_assn_set[enb] :
                    if aquamet_app.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb,ue][wind_ind] > 0.0 :
                        aq_enb_active_ues.append(ue)

                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                    ' UE ' + str(ue) + ' Num. active UEs in window '+str(len(aq_enb_active_ues))) 
                for ue in aq_enb_active_ues :
                    # WARNING!! Make sure that the mcs index starts from 0 since that is what this table takes
                    # Number of PRB to be taken from a config file 
                    # tbs in bytes. The table gives it in bits
                    itbs=rrm_app_vars.mcs_to_itbs[aquamet_app.aq_enb_ue_dl_est_mcs[enb,ue][wind_ind]]
                    dl_cell_bw_in_prb = sm.get_cell_rb(enb=enb,cc=0, dir='dl') 
                    # WARNING!! MAke sure that this table returns TBS in bits as specified by the standard document
                    max_tbs=rrm_app_vars.tbs_table[itbs][dl_cell_bw_in_prb]/8.0 # should be 0 if set is empty
                    log.info(' max_TBS ' + str(max_tbs)) 
                    # Number of TTIs needed to send one pkt
                    N=math.ceil((aquamet_app.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb,ue][wind_ind])/float(max_tbs)) # will be 0 if set is empty
                    log.info(' N ' + str(N)) 
                    # Amount of resources requested by UE. units, TTIs/10ms or subframes/frame
                    X=(float(aquamet_app.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb,ue][wind_ind])/100.0) * N # will be 0 if either components are 0
                    #log.info('Wm=' + str(monitoring_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + ' UE ' + str(ue) + ' meas_thput_kbps '+str(monitoring_app.aq_enb_ue_dl_meas_thput[enb,ue][0])) 
                    log.info(' X ' + str(X)) 
                    # Number of flows that are high rate flows. i.e. number of flows that request resources > their share.
                    # Their share here is total resources / num. of active UEs. HEre shown as 10ms frame/ num. of active UEs
                    if X > 10.0/float(len(aq_enb_active_ues)) :
                        num_HR+=1
                    else :
                        # Sum of the resources requested by UEs that are requesting less than their share. 
                        sum_LR_X+=X
  
                (log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                    ' UE ' + str(ue) + ' Num_HR '+str(num_HR) + ' Sum_LR_X ' +str(sum_LR_X)))


                for ue in aquamet_app.enb_assn_set[enb] :
                    if ue in aq_enb_active_ues :
                        # Get stats from the first structure object which is the ue 
                        # whose attainable throughput is to be measured
                        itbs=rrm_app_vars.mcs_to_itbs[aquamet_app.aq_enb_ue_dl_est_mcs[enb,ue][wind_ind]]
                        dl_cell_bw_in_prb = sm.get_cell_rb(enb=enb,cc=0, dir='dl')
                        # WARNING!! MAke sure that this table returns TBS in bits as specified by the standard document
                        max_tbs=rrm_app_vars.tbs_table[itbs][dl_cell_bw_in_prb]/8.0 # should be 0 if set is empty
                        # Number of TTIs needed to send one pkt
                        N=math.ceil((aquamet_app.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb,ue][wind_ind])/float(max_tbs)) # will be 0 if set is empty
                        # Amount of resources requested by UE. units, TTIs/10ms or subframes/frame
                        X=(float(aquamet_app.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb,ue][wind_ind])/100.0) * N # will be 0 if either components are 0
                        # Resources actually allocated to this UE. unit, TTIs/10ms
                        est_resource_alloc=0
                        if X > 10.0/float(len(aq_enb_active_ues)) :
                            est_resource_alloc=min(X,(10.0 - sum_LR_X)/float(num_HR))
                        else :
                            est_resource_alloc=X
                            
                        aquamet_app.aq_enb_ue_dl_est_ratio_of_frame_alloc[enb,ue][wind_ind]=est_resource_alloc
                        aquamet_app.aq_enb_ue_dl_att_thput[enb,ue][wind_ind]=min((est_resource_alloc * max_tbs), 
                                                            ((aquamet_app.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb,ue][wind_ind]/100.0) 
                                                            * (aquamet_app.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb,ue][wind_ind]) * 8 / 10.0)) # Kbps 
                        
                        log.info('Wind_ind=' + str(wind_ind) + ' eNB ' + str(enb) + 
                            ' UE ' + str(ue) + ' Est. frac. of resource alloc. per frame ' + 
                            str(est_resource_alloc))
                        log.info('Wind_ind=' + str(wind_ind) + ' eNB ' + str(enb) + 
                            ' UE ' + str(ue) + ' Est. attainable throughput ' + 
                            str(aquamet_app.aq_enb_ue_dl_att_thput[enb,ue][wind_ind]))
                    else :
                        aquamet_app.aq_enb_ue_dl_est_ratio_of_frame_alloc[enb,ue][wind_ind]=0
                        aquamet_app.aq_enb_ue_dl_att_thput[enb,ue][wind_ind]=0



        # Print all the estimated info for the last window in one place. 
        # Each time this function is triggered the entire sliding window is evaluated
        # because that is how it would be done in a scenario where QoS degradation triggeres re-eval
        for enb in range(0,sm.get_num_enb()) :
            for ue in aquamet_app.enb_assn_set[enb] :   
                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                    ' UE ' + str(ue) + ' Est. frac. of resource alloc. per frame '+
                    str(aquamet_app.aq_enb_ue_dl_est_ratio_of_frame_alloc[enb,ue][0]))  
                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                    ' UE ' + str(ue) + ' Est. attainable throughput '+
                    str(aquamet_app.aq_enb_ue_dl_att_thput[enb,ue][0]))
                aquamet_app.aq_est_prob_good_thput[enb,ue]=(sum(i >= aquamet_app.thput_threshold for i in aquamet_app.aq_enb_ue_dl_att_thput[enb,ue])
                                /float(aquamet_appp.num_meas_in_slid_wind))
                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                    ' UE ' + str(ue) + ' Est_prob_good_thput '+
                    str(aquamet_app.aq_est_prob_good_thput[enb,ue])) 

        # WARNING!! This is only for test scenario where we are evaluating accuracy of estimation.
        for enb in range(0,sm.get_num_enb()) :
            for ue in aquamet_app.enb_assn_set[enb] :
                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                ' UE ' + str(ue) + ' Meas. throughput '+
                str(aquamet_app.aq_enb_ue_dl_meas_thput[enb,ue][0]))
                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                    ' UE ' + str(ue) + ' Est. attainable throughput '+
                    str(aquamet_app.aq_enb_ue_dl_att_thput[enb,ue][0]))
                log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                    ' UE ' + str(ue) + ' att_thput-meas_thpust (Kbps) '+
                    str(aquamet_app.aq_enb_ue_dl_att_thput[enb,ue][0]-aquamet_app.aq_enb_ue_dl_meas_thput[enb,ue][0])) 
                if aquamet_app.aq_enb_ue_dl_meas_thput[enb,ue][0] > 0.0 :
                    aq_enb_ue_dl_thput_ratio_error=((aquamet_app.aq_enb_ue_dl_att_thput[enb,ue][0] - 
                        aquamet_app.aq_enb_ue_dl_meas_thput[enb,ue][0]) / 
                        aquamet_app.aq_enb_ue_dl_meas_thput[enb,ue][0])
                    log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                        ' UE ' + str(ue) + ' Err_ratio (att-meas)/meas '+
                        str(aq_enb_ue_dl_thput_ratio_error)) 
                else:
                    log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                        ' UE ' + str(ue) + ' Err_ratio (att-meas)/meas '+
                        '-')


    #  This runs in a loop. At the end of this function it is initilized again with a timer.
    # So this measn that we get the monitroing info periodically with this period.
    def run(self, sm, rrc, monitoring_app):
        log.info('Wm timer fired')
        log.info('Reading the status of the underlying eNBs')
        sm.stats_manager('all')
        log.info('Gather measurements')
        monitoring_app.get_rsrp_rsrq(sm)
        monitoring_app.get_statistics(sm)

        # WARNING!! I don't know what this is 
        # It is borrowed from the monitoring_app code ???
        for enb in range(0, sm.get_num_enb()) :
            if monitoring_app.enb_ue_trigger_meas[enb] == 0 :
                log.info('Enable RRC trigger measurement event for eNB ' + str(enb))
                rrc.trigger_meas()
                monitoring_app.enb_ue_trigger_meas[enb] = 1
       
        # Obtain measurements from monitoring_app and add into sliding window.     
        aquamet_app.aggregate_and_add_metrics_to_sliding_window(sm,monitoring_app)
        
        # Monitor the probabilistic measured throughput on serving links
        eval_triggered_flag = False
        for enb in range(0, sm.get_num_enb()) :
            for ue in aquamet_app.current_assoc_set[enb] :
                if aquamet_app.aq_enb_ue_sample_counter[enb,ue] >= aquamet_app.num_meas_in_slid_wind :    
                    aquamet_app.aq_meas_prob_good_thput[enb,ue]=(sum(i >= aquamet_app.thput_threshold for i in aquamet_app.aq_enb_ue_dl_meas_thput[enb,ue])
                            /float(aquamet_app.num_meas_in_slid_wind))
                    log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + ' UE ' + str(ue) + ' Meas_prob_good_thput '+str(aquamet_app.aq_meas_prob_good_thput[enb,ue])) 
                    if aquamet_app.aq_meas_prob_good_thput[enb,ue] < aquamet_app.thput_tolerance :
                        # TRIGGER re-evaluation of association sets
                        eval_triggered_flag = True
                        log.info('k=' + str(aquamet_app.aq_enb_ue_sample_counter[enb,ue]) + ' eNB ' + str(enb) + 
                            ' UE ' + str(ue) + 
                            ' QoS not met, re-evaluation of association TRIGGERED because ' + 
                            str(aquamet_app.aq_meas_prob_good_thput[enb,ue]) + ' > ' + 
                            str(aquamet_app.thput_tolerance)) 


        # # As long as this is triggered for any one serving link we do a re-evaluation
        # if eval_triggered_flag :
        #     # Create association sets to evaluate and choose the 
        #     # configuration that best meets QoS of all users
        #     # TO DO: Modify this based on an algorithm to select assocition sets to evaluate. 
        #     enb=0
        #     aquamet_app.enb_assn_set[enb]=range(0, sm.get_num_ue(enb=enb))
        #     # Evaluate all links in the association set to see if the estimate of 
        #     # attainable throughput for each link meets the requirement 
        #     # But at the time being I want to evaluate the accuracy of the estimate. 
        #     # So this part will need to be changed if I want to trigger handovers with new association sets 
        #     aquamet_app.estimate_inst_att_thput_sliding_window_for_assosn_set(sm,monitoring_app)       


        # In a test scenario we want to evaluate attainable throughput continuously 
        # instead of evaluating this only when triggered by QoS degradation 

        for enb in range(0, sm.get_num_enb()) :   
            if aquamet_app.aq_enb_ue_sample_counter[enb,ue] >= aquamet_app.num_meas_in_slid_wind :
                aquamet_app.enb_assn_set[enb]=aquamet_app.current_assoc_set[enb]
                # This evaluates attainable throughput over the entire sliding window
                # So each time it is called the entire sliding window is re-evaluated, 
                # even through only the last window is new. This is because it is in test mode.
                aquamet_app.estimate_inst_att_thput_sliding_window_for_assosn_set(sm,monitoring_app)     
        
        # New line for each measurement window Wm
        aquamet_log_file.write('\n')
        t = Timer(aquamet_app.measurement_time_window_ms, 
            self.run,kwargs=dict(sm=sm,rrc=rrc,monitoring_app=monitoring_app))
        t.start()


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
    # Create aquamet_app object
    #aquamet_app = aquamet_app()
    aquamet_app = aquamet_app(measurement_time_window_ms=100, 
                               num_meas_in_slid_wind=5,
                               thput_tolerance=0.7)
    
    py3_flag = version_info[0] > 2 
    # This needs to be called after stats_manager has been instansiated 
    # since it uses information from the stats_manager
    aquamet_app.initialize_data_holders()
    # Start the periodic timer for Wm
    t = Timer(aquamet_app.measurement_time_window_ms, aquamet_app.run,kwargs=dict(sm=sm,
        rrc=rrc,monitoring_app=monitoring_app))
    t.start() 