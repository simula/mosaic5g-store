import argparse
import copy
# import sys
from sys import *
from threading import Timer
import rrm_app_vars
from lib import flexran_sdk 
# from lib import logger
import math
import monitoring_app

class AquametApp(object):
    # Data holders for aquamet

    """Input arrival rate downlink data for each ue in IP pkts/second 
    as measured at the enb PDCP""" 
    aq_enb_ue_dl_pdcp_sdu_arr_rate_pps = {}  # [enb, ue][wind_ind]
    """ Average pkt length in bytes of the input IP pkts at the enb PDCP layer """
    aq_enb_ue_dl_pdcp_pkt_len_bytes = {}  # [enb, ue][wind_ind]
    # Noise at ue
    aq_ue_dl_noise = {}  # [ue]
    # RSRP in dBm
    aq_enb_ue_dl_rsrp = {}  # [enb, ue]
    # RSRQ in dB
    aq_enb_ue_dl_rsrq = {}  # [enb, ue]
    # Estimated downlink SNR from RSRP and noise
    aq_enb_ue_dl_est_snr = {}  # [enb, ue] in dB
    # The range of CQI is 0-15
    aq_enb_ue_dl_est_cqi = {}  # [enb, ue]
    # The range of CQI is 0-15
    aq_enb_ue_dl_meas_cqi = {}  # [enb, ue]
    # Estimated MCS from SNR. The range of MCS is 0-27
    aq_enb_ue_dl_est_mcs = {}  # [enb, ue][wind_ind]
    # Estimate of downlink resources allocated to a ue, in terms of fraction 
    # of total available resources in PRBs.
    aq_enb_ue_dl_est_ratio_of_frame_alloc = {}  # [enb, ue][wind_ind]
    aq_enb_ue_dl_meas_ratio_of_frame_alloc = {}  # [enb, ue][wind_ind]
    # Downlink Attainable throughput estimated for which association set  ???
    # in Kbps
    aq_enb_ue_dl_att_thput = {}  # [enb, ue][wind_ind]
    # The ratio of (number of windows where measured throughput
    # is larger than ?? large than or equal to the throughput threshold) 
    #  to the total numner windows in sliding window
    # in Lbps
    aq_meas_prob_good_thput = {}  # [enb, ue]
    # The ratio of (number of windows where attainable throughput
    # is larger than ?? large than or equal to the throughput threshold) 
    #  to the total numner windows in sliding window  
    # ??? for which association set   
    aq_est_prob_good_thput = {}  # [enb, ue]
    # The range of MCS is 0-27
    aq_enb_ue_dl_meas_mcs = {}  # [enb, ue][wind_ind]
    # Downlink throughput in Kbps as measured at the ???? 
    aq_enb_ue_dl_meas_thput = {}  # [enb, ue][wind_ind]

    wm_enb_ue_dl_rsrp = {}  # [enb, ue]
    wm_enb_ue_dl_rsrq = {}  # [enb, ue]
    wm_enb_ue_dl_mac_wcqi = {}  # [enb, ue]
    wm_enb_ue_dl_mcs = {}  # [enb, ue]
    wm_enb_ue_dl_phy_acked_bytes = {}  # [enb, ue]
    wm_enb_ue_dl_mac_rb = {}  # [enb, ue]
    wm_enb_ue_dl_tbs = {}  # [enb, ue]
    wm_enb_ue_dl_pdcp = {}  # [enb, ue]
    prev_enb_ue_dl_pdcp = {}  # [enb, ue]
    wm_enb_ue_dl_pdcp_bytes = {}  # [enb, ue]
    prev_enb_ue_dl_pdcp_bytes = {}  # [enb, ue]
    prev_sfn = {}  # [enb]

    # Current associations of enb to ues
    current_assoc_set = {}  # [enb][set of ues]
    aq_enb_ue_dl_thput_ratio_error = {}  # [enb, ue]
    aq_enb_ue_sample_counter = {}  # [enb, ue]
    # Aquamet monitoring parameters. 
    num_meas_in_slid_wind = 20
    thput_tolerance = 0.7
    thput_threshold = 12000  # Kbps
    measurement_time_window_ms = 500.0  # ms
    tti_time_ms = 1.0  # ms
    aquamet_log_file = None
    tagged_ue_log_file = None
    handover_trigger_log_file = None
    tti_sample_count = 0
    max_rb_per_tti = 25 
    ttis_per_wm = measurement_time_window_ms/tti_time_ms
    tagged_ue_id = 0
    tagged_ue_enb = 0
    tagged_ue_wm_counter = 0

    # Class constructor, which is run when a class object is created. 
    # This can accept arguments that are passed when the object is created
    def __init__(self, log, url='http://localhost', port='9999', url_app='http://localhost', port_app='9090',
                 log_level='info', op_mode='test',
                 measurement_time_window_ms=500.0, num_meas_in_slid_wind=20,thput_tolerance=0.7):
        super(AquametApp, self).__init__()
        
        self.url = url+':'+port
        self.log = log
        self.log_level = log_level
        self.status = 'none'
        self.op_mode = op_mode

        self.num_meas_in_slid_wind = num_meas_in_slid_wind
        self.thput_tolerance = thput_tolerance
        self.measurement_time_window_ms = measurement_time_window_ms

    def initialize_data_holders(self):
        for enb in range(0, sm.get_num_enb()):
            self.current_assoc_set[enb] = []
            self.prev_sfn[enb] = 0
            for ue in range(0, sm.get_num_ue(enb=enb)):
                self.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb, ue] = []  # [enb, ue][wind_ind]
                self.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb, ue] = []  # [enb, ue][wind_ind]
                self.aq_enb_ue_dl_est_mcs[enb, ue] = []  # [enb, ue][wind_ind]
                self.aq_enb_ue_dl_meas_mcs[enb, ue] = []  # [enb, ue][wind_ind]
                self.aq_enb_ue_dl_meas_thput[enb, ue] = []  # [enb, ue][wind_ind]
                self.aq_enb_ue_dl_est_ratio_of_frame_alloc[enb, ue] = \
                    [0]*self.num_meas_in_slid_wind  # [enb, ue][wind_ind]
                self.aq_enb_ue_dl_meas_ratio_of_frame_alloc[enb, ue] = \
                    [0]*self.num_meas_in_slid_wind  # [enb, ue][wind_ind]
                self.aq_enb_ue_dl_att_thput[enb, ue] = [0]*self.num_meas_in_slid_wind  # [enb, ue][wind_ind]
                self.aq_est_prob_good_thput[enb, ue] = 0  # [enb, ue]
                self.aq_meas_prob_good_thput[enb, ue] = 0  # [enb, ue]
                self.aq_enb_ue_dl_est_snr[enb, ue] = 0  # [enb, ue]
                self.aq_ue_dl_noise[ue] = 0  # [ue]
                # aquamet in between variable
                self.aq_enb_ue_dl_rsrp[enb, ue] = 0  # [enb, ue]
                self.aq_enb_ue_dl_rsrq[enb, ue] = 0  # [enb, ue]
                self.aq_enb_ue_dl_est_cqi[enb, ue] = 0  # [enb, ue]
                self.aq_enb_ue_sample_counter[enb, ue] = 0  # [enb, ue]
                self.aq_enb_ue_dl_thput_ratio_error[enb, ue] = 0  # [enb, ue]
                self.current_assoc_set[enb].append(ue)

                self.wm_enb_ue_dl_rsrp[enb, ue] = 0
                self.wm_enb_ue_dl_rsrq[enb, ue] = 0
                self.wm_enb_ue_dl_mac_wcqi[enb, ue] = 0
                self.wm_enb_ue_dl_mcs[enb, ue] = 0
                self.wm_enb_ue_dl_phy_acked_bytes[enb, ue] = 0
                self.wm_enb_ue_dl_mac_rb[enb, ue] = 0
                self.wm_enb_ue_dl_tbs[enb, ue] = 0
                self.wm_enb_ue_dl_pdcp[enb, ue] = 0
                self.prev_enb_ue_dl_pdcp[enb, ue] = 0
                self.wm_enb_ue_dl_pdcp_bytes[enb, ue] = 0
                self.prev_enb_ue_dl_pdcp_bytes[enb, ue] = 0

                self.aquamet_log_file = open("aquamet_log.txt", "w")
                self.tagged_ue_log_file = open("tagged_ue_log.txt", "w")
                self.handover_trigger_log_file = open("handover_trigger_log.txt", "w")
                self.aquamet_log_file.write('running_sample_counter ' + 'enb_id ' + 'ue_id ' +
                                            'rsrp ' + 'rsrq ' + 'noise ' + 'est_snr ' + 'est_cqi ' + 'est_mcs ' +
                                            'pdcp_pkt_len_bytes ' + 'pdcp_sdu_arr_rate_pps ' + 'meas_cqi ' +
                                            'meas_mcs ' + 'meas_ratio_of_frame_alloc ' + 'meas_thput' + '\n')
                self.tagged_ue_log_file.write('tagged_ue_sample_count ' + 'enb_id ' + 'ue_id ' +
                                            'rsrp ' + 'rsrq ' + 'noise ' + 'est_snr ' + 'est_cqi ' + 'est_mcs ' +
                                            'pdcp_pkt_len_bytes ' + 'pdcp_sdu_arr_rate_pps ' + 'meas_cqi ' +
                                            'meas_mcs ' + 'meas_ratio_of_frame_alloc ' + 'meas_thput ' +
                                            'meas_prob_good_thput' + '\n')
                self.handover_trigger_log_file.write('Handover Trigger information \n')

    def aggregate_and_add_metrics_to_sliding_window(self, sm, monitoring_app):
        for enb in range(0, sm.get_num_enb()):
            # WARNING !! Does this imply that the ues of each enb always ave ids starting from 1 ? 
            # How can we uniquely identify ues across enbs ???
            for ue in range(0, sm.get_num_ue(enb=enb)):
                self.aq_enb_ue_sample_counter[enb, ue] += 1

                if enb == 0 and ue == self.tagged_ue_id:
                    self.tagged_ue_wm_counter += 1

                # RSRP and noise are assumed to be in dBm. SNR is in dB
                self.aq_enb_ue_dl_est_snr[enb, ue] = self.wm_enb_ue_dl_rsrp[enb, ue]-monitoring_app.ue_dl_noise[ue]
                self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                              ' eNB ' + str(enb) + ' UE ' + str(ue) +
                              ' RSRP ' + str(self.wm_enb_ue_dl_rsrp[enb, ue]))

                self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                              ' eNB ' + str(enb) + ' UE ' + str(ue) +
                              ' RSRQ ' + str(self.wm_enb_ue_dl_rsrq[enb, ue]))

                self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                              ' eNB ' + str(enb) + ' UE ' + str(ue) +
                              ' Receiver_noise ' + str(monitoring_app.ue_dl_noise[ue]))

                self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                              ' eNB ' + str(enb) + ' UE ' + str(ue) +
                              ' Est_SNR ' + str(self.aq_enb_ue_dl_est_snr[enb, ue]))

                self.aquamet_log_file.write(str(self.aq_enb_ue_sample_counter[enb, ue]) + ' ' +
                                            str(enb) + ' ' + str(ue) + ' ')
                self.aquamet_log_file.write(str(monitoring_app.enb_ue_dl_rsrp[enb, ue]) + ' ')
                self.aquamet_log_file.write(str(monitoring_app.enb_ue_dl_rsrq[enb, ue]) + ' ')
                self.aquamet_log_file.write(str(monitoring_app.ue_dl_noise[ue]) + ' ')
                self.aquamet_log_file.write(str(self.aq_enb_ue_dl_est_snr[enb, ue]) + ' ')
                if enb == 0 and ue == self.tagged_ue_id:
                    self.tagged_ue_log_file.write(str(self.tagged_ue_wm_counter) + ' ' +
                                                str(enb) + ' ' + str(ue) + ' ')
                    self.tagged_ue_log_file.write(str(monitoring_app.enb_ue_dl_rsrp[enb, ue]) + ' ')
                    self.tagged_ue_log_file.write(str(monitoring_app.enb_ue_dl_rsrq[enb, ue]) + ' ')
                    self.tagged_ue_log_file.write(str(monitoring_app.ue_dl_noise[ue]) + ' ')
                    self.tagged_ue_log_file.write(str(self.aq_enb_ue_dl_est_snr[enb, ue]) + ' ')

                # SNR to CQI table imported from rrm_app_vars.py 
                # Warning !! SNR cannot be negative here. It will cause an error
                if self.aq_enb_ue_dl_est_snr[enb, ue] < 0:
                    self.log.info('ERROR!!! SNR is negative')

                self.aq_enb_ue_dl_est_cqi[enb, ue] = \
                    rrm_app_vars.snrdb_to_cqi.index([i for i in rrm_app_vars.snrdb_to_cqi
                                                     if i <= self.aq_enb_ue_dl_est_snr[enb, ue]][-1])
                self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                              ' eNB ' + str(enb) + ' UE ' + str(ue) +
                              ' Est_wCQI '+str(self.aq_enb_ue_dl_est_cqi[enb, ue]))

                self.aquamet_log_file.write(str(self.aq_enb_ue_dl_est_cqi[enb, ue]) + ' ')
                # CQI to MCS
                (self.aq_enb_ue_dl_est_mcs[enb, ue]).insert(0,rrm_app_vars.cqi_to_mcs[self.aq_enb_ue_dl_est_cqi[enb, ue]])
                self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                              ' eNB ' + str(enb) + ' UE ' + str(ue) +
                              ' est_mcs '+str(rrm_app_vars.cqi_to_mcs[self.aq_enb_ue_dl_est_cqi[enb, ue]]))

                self.aquamet_log_file.write(str(rrm_app_vars.cqi_to_mcs[self.aq_enb_ue_dl_est_cqi[enb, ue]]) + ' ')
                
                # Pkt length in bytes. If pkt len is 0 because no pkts were received
                if self.wm_enb_ue_dl_pdcp[enb, ue] == 0:
                    ((self.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb, ue]).insert(0, 0.0))
                else:
                    ((self.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb, ue]).insert(
                        0, self.wm_enb_ue_dl_pdcp_bytes[enb, ue] / float(self.wm_enb_ue_dl_pdcp[enb, ue])))
                self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                              ' eNB ' + str(enb) + ' UE ' + str(ue) +
                              ' PDCP_avg_pkt_len_bytes '+str(self.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb, ue][0]))

                self.aquamet_log_file.write(str(self.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb, ue][0]) + ' ')
                
                # Pkt arrival rate in pkts/second.
                ((self.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb, ue]).insert(
                    0, self.wm_enb_ue_dl_pdcp[enb, ue]*1000 / float(self.measurement_time_window_ms)))
                self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                              ' eNB ' + str(enb) + ' UE ' + str(ue) +
                              ' PDCP_sdu_arr_rate_pps '+str(self.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb, ue][0]))

                self.aquamet_log_file.write(str(self.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb, ue][0]) + ' ')

                if enb == 0 and ue == self.tagged_ue_id:
                    self.tagged_ue_log_file.write(str(self.aq_enb_ue_dl_est_cqi[enb, ue]) + ' ')
                    self.tagged_ue_log_file.write(str(rrm_app_vars.cqi_to_mcs[self.aq_enb_ue_dl_est_cqi[enb, ue]]) + ' ')
                    self.tagged_ue_log_file.write(str(self.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb, ue][0]) + ' ')
                    self.tagged_ue_log_file.write(str(self.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb, ue][0]) + ' ')



                # Do this only if ue is being served by enb 
                if ue in self.current_assoc_set[enb]: 
                    self.aq_enb_ue_dl_meas_cqi[enb, ue] = self.wm_enb_ue_dl_mac_wcqi[enb, ue]
                    (self.aq_enb_ue_dl_meas_mcs[enb, ue]).insert(
                        0, rrm_app_vars.cqi_to_mcs[self.aq_enb_ue_dl_meas_cqi[enb, ue]])
                    self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                                  ' eNB ' + str(enb) + ' UE ' + str(ue) +
                                  ' Meas_wCQI '+str(self.aq_enb_ue_dl_meas_cqi[enb, ue]))

                    self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                                  ' eNB ' + str(enb) + ' UE ' + str(ue) +
                                  ' Meas_MCS '+str(rrm_app_vars.cqi_to_mcs[self.aq_enb_ue_dl_meas_cqi[enb, ue]]))

                    self.aquamet_log_file.write(str(self.aq_enb_ue_dl_meas_cqi[enb, ue]) + ' ')
                    self.aquamet_log_file.write(str(rrm_app_vars.cqi_to_mcs[self.aq_enb_ue_dl_meas_cqi[enb, ue]]) + ' ')

                    # WARNING !! I am not if I have used the right units. Is this ratio really number per 10 ms frame ?
                    (self.aq_enb_ue_dl_meas_ratio_of_frame_alloc[enb, ue]).insert(
                        0, self.wm_enb_ue_dl_mac_rb[enb, ue]/(self.max_rb_per_tti*self.ttis_per_wm))
                    
                    self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                                  ' eNB ' + str(enb) + ' UE ' + str(ue) +
                                  ' Meas_X ' + str(self.aq_enb_ue_dl_meas_ratio_of_frame_alloc[enb, ue][0]))

                    self.aquamet_log_file.write(str(self.aq_enb_ue_dl_meas_ratio_of_frame_alloc[enb, ue][0]) + ' ')

                    ((self.aq_enb_ue_dl_meas_thput[enb, ue]).insert(
                        0, self.wm_enb_ue_dl_phy_acked_bytes[enb, ue]*8 / float(self.measurement_time_window_ms)))
                    
                    self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                                  ' eNB ' + str(enb) + ' UE ' + str(ue) +
                                  ' Meas_thput_kbps '+str(self.aq_enb_ue_dl_meas_thput[enb, ue][0]))

                    self.aquamet_log_file.write(str(self.aq_enb_ue_dl_meas_thput[enb, ue][0]) + ' ')

                    if enb == 0 and ue == self.tagged_ue_id:
                        self.tagged_ue_log_file.write(str(self.aq_enb_ue_dl_meas_cqi[enb, ue]) + ' ')
                        self.tagged_ue_log_file.write(
                            str(rrm_app_vars.cqi_to_mcs[self.aq_enb_ue_dl_meas_cqi[enb, ue]]) + ' ')
                        self.tagged_ue_log_file.write(str(self.aq_enb_ue_dl_meas_ratio_of_frame_alloc[enb, ue][0]) + ' ')
                        self.tagged_ue_log_file.write(str(self.aq_enb_ue_dl_meas_thput[enb, ue][0]) + ' ')

                else:
                    self.aquamet_log_file.write(str(0) + ' ')
                    self.aquamet_log_file.write(str(0) + ' ')
                    self.aquamet_log_file.write(str(0) + ' ')
                    self.aquamet_log_file.write(str(0) + ' ')



                # WARNING!!! make sure that the overflow of this is handled. currrently it is not.
                self.aquamet_log_file.write('\n')
                # Check if the number of aggregated measurements in the sliding window is > window_size
                if self.aq_enb_ue_sample_counter[enb, ue] > self.num_meas_in_slid_wind:
                    del self.aq_enb_ue_dl_est_mcs[enb, ue][self.num_meas_in_slid_wind:]
                    del self.aq_enb_ue_dl_meas_mcs[enb, ue][self.num_meas_in_slid_wind:]
                    del self.aq_enb_ue_dl_meas_thput[enb, ue][self.num_meas_in_slid_wind:]
                    del self.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb, ue][self.num_meas_in_slid_wind:]
                    del self.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb, ue][self.num_meas_in_slid_wind:]
                    # WARNING ! make sure I have truncated all the sliding windows in use

    def estimate_inst_att_thput_sliding_window_for_assosn_set(self, sm, monitoring_app, enb_assn_set):
        # Get estimated instataneous attainable troughput
        # the first structure object in stats belongs to the ue whose attainable throughput is to be estimated
        # ues for which this enb satisfies the probabilistic condition 
        # because I only want to do this for the target eNB

        for enb in enb_assn_set:
            for wind_ind in range(0, self.num_meas_in_slid_wind):
                num_HR = 0
                sum_LR_X = 0
                est_resource_alloc = 0
                est_thput_rlc = 0
                aq_enb_active_ues = []

                # Number of active UEs. For this k count how many UEs had non zero arrival rates             
                for ue in enb_assn_set[enb]:
                    if self.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb, ue][wind_ind] > 0.0:
                        aq_enb_active_ues.append(ue)

                # self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) +
                #               ' UE ' + str(ue) + ' Num. active UEs in window '+str(len(aq_enb_active_ues)))
                for ue in aq_enb_active_ues:
                    # WARNING!! Make sure that the mcs index starts from 0 since that is what this table takes
                    # Number of PRB to be taken from a config file 
                    # tbs in bytes. The table gives it in bits
                    itbs = rrm_app_vars.mcs_to_itbs[self.aq_enb_ue_dl_est_mcs[enb, ue][wind_ind]]
                    # self.log.info(' itbs ' + str(itbs))
                    # dl_cell_bw_in_prb = sm.get_cell_rb(enb=enb, cc=0, dir='dl')
                    dl_cell_bw_in_prb = 25
                    # self.log.info(' dl_cell_bw_in_prb ' + str(dl_cell_bw_in_prb))
                    # WARNING!! MAke sure that this table returns TBS in bits as specified by the standard document
                    max_tbs = rrm_app_vars.tbs_table[itbs][dl_cell_bw_in_prb-1] / 8.0  # should be 0 if set is empty
                    # self.log.info(' max_TBS ' + str(max_tbs))
                    # Number of TTIs needed to send one pkt
                    # will be 0 if set is empty
                    N = math.ceil((self.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb, ue][wind_ind])/float(max_tbs))
                    # self.log.info(' N ' + str(N))
                    # Amount of resources requested by UE. units, TTIs/10ms or subframes/frame
                    # will be 0 if either components are 0
                    X = (float(self.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb, ue][wind_ind])/100.0) * N
                    # self.log.info('Wm=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) + ' UE ' +
                    #  str(ue) + ' meas_thput_kbps '+str(monitoring_app.aq_enb_ue_dl_meas_thput[enb, ue][0]))
                    # self.log.info(' X ' + str(X))
                    # Number of flows that are high rate flows. i.e.
                    # number of flows that request resources > their share.
                    # Their share here is total resources / num. of active UEs.
                    # HEre shown as 10ms frame/ num. of active UEs
                    if X > 10.0/float(len(aq_enb_active_ues)):
                        num_HR += 1
                    else:
                        # Sum of the resources requested by UEs that are requesting less than their share. 
                        sum_LR_X += X
  
                # (self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) +
                #                ' UE ' + str(ue) + ' Num_HR '+str(num_HR) + ' Sum_LR_X ' + str(sum_LR_X)))

                for ue in enb_assn_set[enb]:
                    if ue in aq_enb_active_ues:
                        # Get stats from the first structure object which is the ue 
                        # whose attainable throughput is to be measured
                        itbs = rrm_app_vars.mcs_to_itbs[self.aq_enb_ue_dl_est_mcs[enb, ue][wind_ind]]
                        # dl_cell_bw_in_prb = sm.get_cell_rb(enb=enb, cc=0, dir='dl')
                        dl_cell_bw_in_prb = 25
                        # WARNING!! MAke sure that this table returns TBS in bits as specified by the standard document
                        max_tbs = rrm_app_vars.tbs_table[itbs][dl_cell_bw_in_prb-1]/8.0  # should be 0 if set is empty
                        # Number of TTIs needed to send one pkt
                        # will be 0 if set is empty
                        N = math.ceil((self.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb, ue][wind_ind])/float(max_tbs))
                        # Amount of resources requested by UE. units, TTIs/10ms or subframes/frame
                        # will be 0 if either components are 0
                        X = (float(self.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb, ue][wind_ind])/100.0) * N
                        # Resources actually allocated to this UE. unit, TTIs/10ms
                        est_resource_alloc = 0
                        if X > 10.0/float(len(aq_enb_active_ues)):
                            est_resource_alloc = min(X, (10.0 - sum_LR_X)/float(num_HR))
                        else:
                            est_resource_alloc = X
                            
                        self.aq_enb_ue_dl_est_ratio_of_frame_alloc[enb, ue][wind_ind] = est_resource_alloc
                        self.aq_enb_ue_dl_att_thput[enb, ue][wind_ind] = \
                            min((est_resource_alloc * max_tbs * 8 / 10.0),
                                ((self.aq_enb_ue_dl_pdcp_sdu_arr_rate_pps[enb, ue][wind_ind]/100.0) *
                                 (self.aq_enb_ue_dl_pdcp_pkt_len_bytes[enb, ue][wind_ind]) * 8 / 10.0))  # Kbps
                        
                        # self.log.info('Wind_ind=' + str(wind_ind) + ' eNB ' + str(enb) +
                        #               ' UE ' + str(ue) + ' Est. frac. of resource alloc. per frame ' +
                        #               str(est_resource_alloc))
                        # self.log.info('Wind_ind=' + str(wind_ind) + ' eNB ' + str(enb) +
                        #               ' UE ' + str(ue) + ' Est. attainable throughput ' +
                        #               str(self.aq_enb_ue_dl_att_thput[enb, ue][wind_ind]))
                    else:
                        self.aq_enb_ue_dl_est_ratio_of_frame_alloc[enb, ue][wind_ind] = 0
                        self.aq_enb_ue_dl_att_thput[enb, ue][wind_ind] = 0

        # # Print all the estimated info for the last window in one place. 
        # # Each time this function is triggered the entire sliding window is evaluated
        # # because that is how it would be done in a scenario where QoS degradation triggeres re-eval
        # for enb in range(0,sm.get_num_enb()):
        #     for ue in enb_assn_set[enb]:   
        #         self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) + 
        #             ' UE ' + str(ue) + ' Est. frac. of resource alloc. per frame '+
        #             str(self.aq_enb_ue_dl_est_ratio_of_frame_alloc[enb, ue][0]))  
        #         self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) + 
        #             ' UE ' + str(ue) + ' Est. attainable throughput '+
        #             str(self.aq_enb_ue_dl_att_thput[enb, ue][0]))
        #         self.aq_est_prob_good_thput[enb, ue]= \
        #           (sum(i >= self.thput_threshold for i in self.aq_enb_ue_dl_att_thput[enb, ue])
        #                         /float(AquametAppp.num_meas_in_slid_wind))
        #         self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) + 
        #             ' UE ' + str(ue) + ' Est_prob_good_thput '+
        #             str(self.aq_est_prob_good_thput[enb, ue])) 

        # # WARNING!! This is only for test scenario where we are evaluating accuracy of estimation.
        # for enb in range(0,sm.get_num_enb()):
        #     for ue in enb_assn_set[enb]:
        #         self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) + 
        #         ' UE ' + str(ue) + ' Meas. throughput '+
        #         str(self.aq_enb_ue_dl_meas_thput[enb, ue][0]))
        #         self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) + 
        #             ' UE ' + str(ue) + ' Est. attainable throughput '+
        #             str(self.aq_enb_ue_dl_att_thput[enb, ue][0]))
        #         self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) + 
        #             ' UE ' + str(ue) + ' att_thput-meas_thpust (Kbps) '+
        #             str(self.aq_enb_ue_dl_att_thput[enb, ue][0]-self.aq_enb_ue_dl_meas_thput[enb, ue][0])) 
        #         if self.aq_enb_ue_dl_meas_thput[enb, ue][0] > 0.0:
        #             aq_enb_ue_dl_thput_ratio_error=((self.aq_enb_ue_dl_att_thput[enb, ue][0] - 
        #                 self.aq_enb_ue_dl_meas_thput[enb, ue][0]) / 
        #                 self.aq_enb_ue_dl_meas_thput[enb, ue][0])
        #             self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) + 
        #                 ' UE ' + str(ue) + ' Err_ratio (att-meas)/meas '+
        #                 str(aq_enb_ue_dl_thput_ratio_error)) 
        #         else:
        #             self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) + 
        #                 ' UE ' + str(ue) + ' Err_ratio (att-meas)/meas '+
        #                 '-')

    #  This runs in a loop. At the end of this function it is initilized again with a timer.
    # So this means that we get the monitroing info periodically with this period.
    def tti_timer_fire(self, sm, rrc, monitoring_app):
        self.tti_sample_count += 1
        # self.log.info('tti timer fired: tti count is ' + str(self.tti_sample_count))
        # self.log.info('tti timer fired: sfn is ' + str(monitoring_app.enb_dl_mac_sfn[0]))
        # self.log.info('TTI timer fired')
        # self.log.info('Reading the status of the underlying eNBs')
        # self.log.info('Gather measurements')
        # update the all stats 
        sm.stats_manager('all')
        # self.log.info('2.1 Gather PDCP statistics')
        monitoring_app.get_pdcp_statistics(sm)
        # self.log.info('2.2 Gather RLC statistics')
        monitoring_app.get_rlc_statistics(sm)
        # self.log.info('2.3 Gather MAC statistics')
        monitoring_app.get_mac_statistics(sm)
        # self.log.info('2.4 Gather PHY statistics')
        monitoring_app.get_phy_statistics(sm)
        # self.log.info('2.5 Gather RRC statistics')
        monitoring_app.get_rrc_statistics(sm) 
        # WARNING!! I don't know what this is 
        # It is borrowed from the monitoring_app code ???
        # for enb in range(0, sm.get_num_enb()):
        #    if monitoring_app.enb_ue_trigger_meas[enb] == 0:
        #        self.log.info('Enable RRC trigger measurement event for eNB ' + str(enb))
        #        rrc.trigger_meas()
        #        monitoring_app.enb_ue_trigger_meas[enb] = 1
       
        # Aggregate these metrics into Wm
        # Should I use number of samples or a timer ? a timer is more realistic .
        
        # running average 
        for enb in range(0, sm.get_num_enb()):
            for ue in range(0, sm.get_num_ue(enb=enb)):
                self.wm_enb_ue_dl_rsrp[enb, ue] = (self.wm_enb_ue_dl_rsrp[enb, ue] * self.tti_sample_count +
                                                   monitoring_app.enb_ue_dl_rsrp[enb, ue]) / \
                                                  (self.tti_sample_count + 1)
                self.wm_enb_ue_dl_rsrq[enb, ue] = (self.wm_enb_ue_dl_rsrq[enb, ue] *
                                                   self.tti_sample_count + monitoring_app.enb_ue_dl_rsrq[enb, ue]) / \
                                                  (self.tti_sample_count + 1)
                self.wm_enb_ue_dl_mac_wcqi[enb, ue] = (self.wm_enb_ue_dl_mac_wcqi[enb, ue] * self.tti_sample_count +
                                                       monitoring_app.enb_ue_dl_mac_wcqi[enb, ue]) / \
                                                      (self.tti_sample_count + 1)
                self.wm_enb_ue_dl_mcs[enb, ue] = (self.wm_enb_ue_dl_mcs[enb, ue] * self.tti_sample_count +
                                                  monitoring_app.enb_ue_dl_mac_mcs[enb, ue]) / (self.tti_sample_count + 1)
                self.wm_enb_ue_dl_phy_acked_bytes[enb, ue] += monitoring_app.enb_ue_dl_phy_acked_bytes[enb, ue]
                self.wm_enb_ue_dl_mac_rb[enb, ue] += monitoring_app.enb_ue_dl_mac_rb[enb, ue]
                self.wm_enb_ue_dl_tbs[enb, ue] += monitoring_app.enb_ue_dl_mac_tbs[enb, ue]
        
        if self.tti_sample_count >= self.ttis_per_wm:
            self.measurement_window_timer_fire(sm=sm, rrc=rrc, monitoring_app=monitoring_app)
        # else:
        #     self.tti_timer_fire(sm=sm, rrc=rrc, monitoring_app=monitoring_app)
        # t = Timer(self.tti_time_ms/1000,
        #           self.tti_timer_fire, kwargs=dict(sm=sm, rrc=rrc, monitoring_app=monitoring_app))
        # t.start()
        return

    def measurement_window_timer_fire(self, sm, rrc, monitoring_app):
        self.log.info('Wm timer fired: tti count is ' + str(self.tti_sample_count))
        self.tti_sample_count = 0
        # Handle the upcounter that have been counting up for the last Wm time
        for enb in range(0, sm.get_num_enb()):
            for ue in range(0, sm.get_num_ue(enb=enb)):
                self.wm_enb_ue_dl_pdcp[enb, ue] = monitoring_app.enb_ue_dl_pdcp[enb, ue] - \
                                                  self.prev_enb_ue_dl_pdcp[enb, ue]
                self.prev_enb_ue_dl_pdcp[enb, ue] = monitoring_app.enb_ue_dl_pdcp[enb, ue]
                self.wm_enb_ue_dl_pdcp_bytes[enb, ue] = \
                    monitoring_app.enb_ue_dl_pdcp_bytes[enb, ue] - self.prev_enb_ue_dl_pdcp_bytes[enb, ue]
                self.prev_enb_ue_dl_pdcp_bytes[enb, ue] = monitoring_app.enb_ue_dl_pdcp_bytes[enb, ue]


        # Use this aggregated over Wm samples and add into sliding window.
        self.log.info('----------- Bytes sent by pdcp in this window are ' + str(self.wm_enb_ue_dl_pdcp_bytes[0, 0]))
        self.log.info('----------- Before and after sfn are ' +
                      str(monitoring_app.enb_dl_mac_sfn[0] - self.prev_sfn[0]))
        self.prev_sfn[0] = monitoring_app.enb_dl_mac_sfn[0]

        self.aggregate_and_add_metrics_to_sliding_window(sm, monitoring_app)
        # Reset the values that were being accumulated
        for enb in range(0, sm.get_num_enb()):
            for ue in range(0, sm.get_num_ue(enb=enb)):
                self.wm_enb_ue_dl_phy_acked_bytes[enb, ue] = 0
                self.wm_enb_ue_dl_mac_rb[enb, ue] = 0
                self.wm_enb_ue_dl_tbs[enb, ue] = 0

        # --------------------------------------------------------------------------------
        # Monitor the probabilistic measured throughput on serving links if the sliding window is full
        eval_triggered_flag = False
        association_changed_flag = False

        # WARNING. I do not need this. Remove
        if self.tagged_ue_wm_counter >= self.num_meas_in_slid_wind:
                # self.aq_enb_ue_sample_counter[1, 0] >= self.num_meas_in_slid_wind:
            # I do not know what this is ??????
            # ue = tagged_ue_id
            #  enb = 0
            for enb in range(0, sm.get_num_enb()):
                for ue in self.current_assoc_set[enb]:
                    if self.aq_enb_ue_sample_counter[enb, ue] >= self.num_meas_in_slid_wind:
                        self.aq_meas_prob_good_thput[enb, ue] = (sum(i >= self.thput_threshold
                                                                     for i in self.aq_enb_ue_dl_meas_thput[enb, ue])
                                                                 / float(self.num_meas_in_slid_wind))
                        self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                                      ' eNB ' + str(enb) + ' UE ' + str(ue) +
                                      ' Meas_prob_good_thput '+str(self.aq_meas_prob_good_thput[enb, ue]))
                        if enb == 0 and ue == self.tagged_ue_id:
                            self.tagged_ue_log_file.write(str(self.aq_meas_prob_good_thput[enb, ue]) + '\n')

                        # if (self.aq_meas_prob_good_thput[enb, ue] < self.thput_tolerance) and \
                        #         (enb == self.tagged_ue_enb) \
                        #         and (ue == self.tagged_ue_id):
                        if (enb == self.tagged_ue_enb) \
                                    and (ue == self.tagged_ue_id):
                            # TRIGGER re-evaluation of association sets only for tagged UE
                            eval_triggered_flag = True
                            self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) + ' eNB ' + str(enb) +
                                          ' UE ' + str(ue) +
                                          ' QoS not met, re-evaluation of association TRIGGERED because ' +
                                          str(self.aq_meas_prob_good_thput[enb, ue]) + ' > ' +
                                          str(self.thput_tolerance))

        else:
            self.tagged_ue_log_file.write('\n')


        if eval_triggered_flag:  # only for tagged UE
            self.log.info('--------------------')
            max_prob_satisfying_qos = self.aq_meas_prob_good_thput[self.tagged_ue_enb, self.tagged_ue_id]
            enb_assn_set = {}
            for enb in range(0, sm.get_num_enb()):
                self.log.info('-------------------- enb is ' + str(enb) + ' tagged_enb is ' + str(self.tagged_ue_enb))
                # if enb != self.tagged_ue_enb:
                if True:
                    self.log.info('--------------------')
                    """ Take the current serving set of this candidate eNB and add the tagged UE to it to 
                    see how this affects the throughput of the tagged UE and the others in the serving set """
                    # enb_assn_set[enb] = copy.copy(self.current_assoc_set[enb])
                    enb_assn_set[enb] = []
                    enb_assn_set[enb].append(self.tagged_ue_id)

                    self.estimate_inst_att_thput_sliding_window_for_assosn_set(sm, monitoring_app, enb_assn_set)

                    prob_satisfying_qos = \
                        (sum(i >= self.thput_threshold
                             for i in self.aq_enb_ue_dl_att_thput[enb, self.tagged_ue_id])
                         / float(self.num_meas_in_slid_wind))
                    self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                                  ' eNB ' + str(enb) + ' UE ' + str(ue) +
                                  ' Est_prob_good_thput '+str(prob_satisfying_qos))

                    self.handover_trigger_log_file.write(str(self.tagged_ue_wm_counter) + ' ' +
                                                         'enb_ue_dl_est_ratio_of_frame_alloc ' +
                                                         str(self.aq_enb_ue_dl_est_ratio_of_frame_alloc
                                                             [enb, self.tagged_ue_id]) + '\n')
                    self.handover_trigger_log_file.write(str(self.tagged_ue_wm_counter) + ' ' +
                                                         'enb_ue_dl_att_thput ' + str(self.aq_enb_ue_dl_att_thput
                                                             [enb, self.tagged_ue_id]) + '\n')
                    self.handover_trigger_log_file.write(str(self.tagged_ue_wm_counter) + ' ' +
                                                         'enb_ue_dl_meas_thput ' + str(self.aq_enb_ue_dl_meas_thput
                                                             [self.tagged_ue_enb, self.tagged_ue_id]) + '\n')
                    self.handover_trigger_log_file.write(str(self.tagged_ue_wm_counter) + ' ' +
                                                         'Est_prob_good_thput ' + str(prob_satisfying_qos) + '\n')

                    if prob_satisfying_qos > max_prob_satisfying_qos:
                        # After this evaluation I need to see if this association set is a fit for the tagged sta.
                        max_prob_satisfying_qos = prob_satisfying_qos
                        best_target_enb = enb
                        association_changed_flag = True
                        self.log.info('k=' + str(self.aq_enb_ue_sample_counter[enb, ue]) +
                                      "eNB: " + str(enb) + " is better than current eNB: " +
                                      str(self.tagged_ue_enb))

        if association_changed_flag:
            self.tagged_ue_enb = best_target_enb
            self.tagged_ue_wm_counter = 0
            # To Do: Update current association sets. Not doing this because handover is not implemented.
            # To Do: Implement handover

        # New line for each measurement window Wm
        # self.aquamet_log_file.write('\n')
        # self.tti_timer_fire(sm=sm, rrc=rrc, monitoring_app=monitoring_app)

        # t_Wm = Timer(self.measurement_time_window_ms/1000.0, self.measurement_window_timer_fire,
        #              kwargs=dict(sm=sm, rrc=rrc, monitoring_app=monitoring_app))
        # t_Wm.start()
        return


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
                        help='set the application server port: 9090 (default)')
    # need to may be rename parameters - do not know
    parser.add_argument('--app-url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost', 
                        help='set the App address to open data: loalhost (default)')
    parser.add_argument('--app-port', metavar='[option]', action='store', type=int,
                        required=False, default=8080, 
                        help='set the App port to open data: 8080 (default)')
    parser.add_argument('--app-period',  metavar='[option]', action='store', type=float,
                        required=False, default=0.001, 
                        help='set the period of the app: 0.001 s (default)')
    parser.add_argument('--graph', metavar='[option]', action='store', type=bool,
                        required=False, default=False, 
                        help='set true to visualize (default false)')
    parser.add_argument('--graph-period',  metavar='[option]', action='store', type=int,
                        required=False, default=5, 
                        help='set the period of the app visualisation: 5s (default)')
    parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
                        required=False, default='test', 
                        help='Set the app operation mode either with FlexRAN or with the test json files: '
                             'test(default), sdk')
    parser.add_argument('--log',  metavar='[level]', action='store', type=str,
                        required=False, default='info', 
                        help='set the log level: debug, info (default), warning, error, critical')
   
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args() 

    log = flexran_sdk.logger(log_level=args.log).init_logger()

    # Create stats_manager object
    sm = flexran_sdk.stats_manager(log=log,
                                   url=args.url,
                                   port=args.port,
                                   op_mode=args.op_mode)
    # Create rrc_trigger_meas object
    rrc = flexran_sdk.rrc_trigger_meas(log=log,
                                       url=args.url,
                                       port=args.port,
                                       op_mode=args.op_mode)

    # sm.log.info('1. Reading the status of the underlying eNBs')
    sm.stats_manager('all')

    # Create monitoring_app object
    monitoring_app = monitoring_app.monitoring_app(log=log,
                                url=args.url,
                                port=args.port,
                                log_level=args.log,
                                op_mode=args.op_mode)
    # monitoring_app = monitoring_app.monitoring_app(log=log,
    #                                                url=args.url,
    #                                                port=args.port,
    #                                                url_app=args.url_app,
    #                                                port_app=args.port_app,
    #                                                log_level=0,
    #                                                # log_level=args.log,
    #                                                op_mode=args.op_mode)
    monitoring_app.init_data_holders(sm)

    # Create AquametApp object
    AquametApp = AquametApp(log=log,
                            url=args.url,
                            port=args.port,
                            url_app=args.url_app,
                            port_app=args.port_app,
                            log_level=args.log,
                            op_mode=args.op_mode,
                            measurement_time_window_ms=500,
                            num_meas_in_slid_wind=20,
                            thput_tolerance=0.7)

    py3_flag = version_info[0] > 2 
    # This needs to be called after stats_manager has been instansiated 
    # since it uses information from the stats_manager
    AquametApp.initialize_data_holders()
    """ Start the TTI timer that fires every ms so that I can collect data from 
    the monitoring app. This is only because the logs are giving me a value every ms. 
    In reality this should be removed and a Wm timer should be used """
    # The unit for the fire time is in seconds
    run_time_ms = 210*1000
    for i in range(0, run_time_ms):
        AquametApp.tti_timer_fire(sm=sm, rrc=rrc, monitoring_app=monitoring_app)
        # print("Again !!! ")

    # t = Timer(AquametApp.tti_time_ms/1000, AquametApp.tti_timer_fire,
    #           kwargs=dict(sm=sm, rrc=rrc, monitoring_app=monitoring_app))
    # t.start()
    # t_Wm = Timer(AquametApp.measurement_time_window_ms/1000.0, AquametApp.measurement_window_timer_fire,
    #              kwargs=dict(sm=sm, rrc=rrc, monitoring_app=monitoring_app))
    # t_Wm.start()
