"""
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
"""

"""
  File name: rrm_app.py
  Author: navid nikaein
  Description: This app dynamically updates the RRM policy based on the statistics received through FLEXRAN SDK
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

import rrm_app_vars

from lib import flexran_sdk
from lib import logger

import signal

def sigint_handler(signum,frame):
  print 'Exiting, wait for the timer to expire... Bye'
  sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

class rrm_app(object):
  """RRM network app to enforce poliy to the underlying RAN
  """
  #
  pf=''
  pf_current=''
  # stats vars
  maxmcs_dl= {}
  maxmcs_ul={}
  # stats vars
  reserved_vrbg_ul= {}
  reserved_vrbg_dl={}
  reserved_rate_dl= {}
  reserved_rate_ul={}
  reserved_latency_dl= {}
  reserved_latency_ul={}
  reserved_priority_dl= {}
  reserved_priority_ul={}
  reserved_isolation_dl= {}
  reserved_isolation_ul={}

  # consider only one cc
  enb_sfn={}
  enb_ulrb={}
  enb_dlrb={}
  enb_ulmaxmcs={}
  enb_dlmaxmcs={}

  ue_dlwcqi={}
  ue_phr={}

  lc_ue_bsr={}
  lc_ue_report={}


  # performance variables
  enb_available_ulrb={}
  enb_available_dlrb={}

  ue_dlmcs={}
  ue_ulmcs={}

  lc_ue_dlrb={}
  lc_ue_ulrb={}
  lc_ue_dltbs={}
  lc_ue_ultbs={}
  ue_dlrb={}
  ue_ulrb={}
  ue_dltbs={}
  ue_ultbs={}

  # Slice policy vars
  slice_ulrb = {}
  slice_dlrb = {}
  slice_ulrb_share = {}
  slice_dlrb_share = {}
  enb_ulrb_share = {}
  enb_dlrb_share = {}
  
  slice_ulrb_share_r1= {}
  slice_dlrb_share_r1 = {}
  enb_ulrb_share_r1 = {}
  enb_dlrb_share_r1 = {}




  def __init__(self, log, template=rrm_app_vars.template_1, url='http://localhost',port='9999',log_level='info', op_mode='test'):
    super(rrm_app, self).__init__()

    self.templates  = template
    self.url        = url+port
    self.log_level  = log_level
    self.status     = 0
    self.op_mode    = op_mode

    # RRM App local data
    self.policy_data = {}

    # TBD: init for max enb and ue
    rrm_app.enb_sfn[0,0]={0}

  def get_statistics(self, sm):

    for enb in range(0, sm.get_num_enb()) :
      rrm_app.enb_dlrb[enb] = sm.get_cell_rb(enb,dir='DL')
      rrm_app.enb_ulrb[enb] = sm.get_cell_rb(enb,dir='UL')
      rrm_app.enb_ulmaxmcs[enb] = sm.get_cell_maxmcs(enb,dir='UL')
      rrm_app.enb_dlmaxmcs[enb] = sm.get_cell_maxmcs(enb,dir='DL')

      for ue in range(0, sm.get_num_ue(enb=enb)) :
        rrm_app.enb_sfn[enb,ue]     = sm.get_enb_sfn(enb,ue)
        rrm_app.ue_dlwcqi[enb,ue]   = sm.get_ue_dlwbcqi(enb,ue)
        rrm_app.ue_phr[enb,ue]      = sm.get_ue_phr(enb,ue)

        # skip the control channels, SRB1 and SRB2
        for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :
          # for each lcgid rater than lc
          rrm_app.lc_ue_bsr[enb,ue,lc] = sm.get_ue_bsr(enb,ue,lc=lc)
          rrm_app.lc_ue_report[enb, ue, lc] = sm.get_ue_lc_report(enb=enb, ue=ue, lc=lc)


  # 
  def get_policy_maxmcs(self,rrm,sm) :

    for enb in range(0, sm.get_num_enb()) :
      rrm_app.maxmcs_dl[enb] = {}
      for sid in range(0, rrm.get_input_slice_nums(enb) ):  # get_input_slice_nums and get_num_slices
        rrm_app.maxmcs_dl[enb][sid] = rrm.get_slice_maxmcs(sid=sid, dir='DL')

    for enb in range(0, sm.get_num_enb()) :
      rrm_app.maxmcs_ul[enb] = {}
      for sid in range(0, rrm.get_input_slice_nums(enb) ):
        rrm_app.maxmcs_ul[enb][sid] = rrm.get_slice_maxmcs(sid=sid, dir='UL')


  def get_policy_mcs(self, rrm, enb, ue, dir):

        sid = ue % rrm.get_input_slice_nums(enb)

        if dir == 'dl' or dir == "DL":
          robustness = rrm.get_input_slice_reliability(enb, sid, "DL")

          if robustness == 'high':
              return rrm_app_vars.cqi_to_mcs_robust[rrm_app.ue_dlwcqi[enb,ue] ]
          elif robustness == 'low':
              return rrm_app_vars.cqi_to_mcs_high_rate[rrm_app.ue_dlwcqi[enb,ue] ]
          else :
              return rrm_app_vars.cqi_to_mcs[rrm_app.ue_dlwcqi[enb,ue] ]

        elif dir == 'ul' or dir == "UL":
            return 8 # f(ue_phr[enb,ue])
        else :
            self.log.error('Unknown direction ' + dir)
            return


  def get_policy_reserved_rate(self,rrm,sm) :

    #for sid in range(0, rrm.get_num_slices()):
    for enb in range(0, sm.get_num_enb()) :
      rrm_app.reserved_vrbg_dl[enb] = {}
      rrm_app.reserved_rate_dl[enb] = {}
      rrm_app.reserved_latency_dl[enb] = {}
      rrm_app.reserved_priority_dl[enb] = {}
      rrm_app.reserved_isolation_dl[enb] = {}
      for sid in range(0, rrm.get_input_slice_nums(enb) ):
        rrm_app.reserved_vrbg_dl[enb][sid] = rrm.get_input_slice_vrbg(enb, sid=sid, dir='DL')
        rrm_app.reserved_rate_dl[enb][sid] = rrm.get_input_slice_rate(enb, sid=sid, dir='DL')
        rrm_app.reserved_latency_dl[enb][sid] = rrm.get_input_slice_latency(enb, sid=sid, dir='DL')
        rrm_app.reserved_priority_dl[enb][sid] = rrm.get_input_slice_priority(enb, sid=sid, dir='DL')
        rrm_app.reserved_isolation_dl[enb][sid] = rrm.get_input_slice_isolation(enb, sid=sid, dir='DL')

      #for sid in range(0, rrm.get_num_slices(dir='UL')):
      rrm_app.reserved_vrbg_ul[enb] = {}
      rrm_app.reserved_rate_ul[enb] = {}
      rrm_app.reserved_latency_ul[enb] = {}
      rrm_app.reserved_priority_ul[enb] = {}
      rrm_app.reserved_isolation_ul[enb] = {}
      for sid in range(0, rrm.get_input_slice_nums(enb) ):
        rrm_app.reserved_vrbg_ul[enb][sid] = rrm.get_input_slice_vrbg(enb, sid=sid, dir='UL')
        rrm_app.reserved_rate_ul[enb][sid] = rrm.get_input_slice_rate(enb, sid=sid, dir='UL')
        rrm_app.reserved_latency_ul[enb][sid] = rrm.get_input_slice_latency(enb, sid=sid, dir='UL')
        rrm_app.reserved_priority_ul[enb][sid] = rrm.get_input_slice_priority(enb, sid=sid, dir='UL')
        rrm_app.reserved_isolation_ul[enb][sid] = rrm.get_input_slice_isolation(enb, sid=sid, dir='UL')


  def calculate_exp_perf (self, sm) :

    # Loop on eNodeBs
    for enb in range(0, sm.get_num_enb()) :
      rrm_app.enb_available_ulrb[enb]= rrm_app.enb_ulrb[enb]
      rrm_app.enb_available_dlrb[enb]= rrm_app.enb_dlrb[enb]

      # Loop on UEs connected to the current eNodeB
      for ue in range(0, sm.get_num_ue(enb=enb)) :
        # calculate the MCS : Dl = conversion DL wideband CQI -> MCS, UL : fixed value
        rrm_app.ue_dlmcs[enb,ue] = rrm_app_vars.cqi_to_mcs[rrm_app.ue_dlwcqi[enb,ue]]
        rrm_app.ue_ulmcs[enb,ue] = 8 # f(ue_phr[enb,ue])

        # calculate the spectral efficieny

        # skip the control channels, SRB1 and SRB2, start at index 2
        for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :

          #calculate the required RB for UL
          rrm_app.ue_ulrb[enb,ue] = 0 # Error : if this var is 0-initialized here, the increment of this value a few lines after is equivalent to an assignement. This 0-initialisation should probably be put outside of this loop
          rrm_app.lc_ue_ulrb[enb,ue,lc] = 2 # f(bandwidth)
          ul_itbs = rrm_app_vars.mcs_to_itbs[rrm_app.ue_ulmcs[enb,ue]]
          rrm_app.lc_ue_ultbs[enb,ue,lc] = rrm_app_vars.tbs_table[ul_itbs][rrm_app.lc_ue_ulrb[enb,ue,lc]]
          while rrm_app_vars.bsr_table[rrm_app.lc_ue_bsr[enb,ue,lc]] > rrm_app.lc_ue_ultbs[enb,ue,lc] :
            if rrm_app.lc_ue_ulrb[enb,ue,lc] > rrm_app.enb_available_ulrb[enb] :
              log.info('no available ulrb')
              break
            rrm_app.lc_ue_ulrb[enb,ue,lc]+=2 # f(bandwidth)
            rrm_app.lc_ue_ultbs[enb,ue,lc]=rrm_app_vars.tbs_table[ul_itbs][rrm_app.lc_ue_ulrb[enb,ue,lc]]

          rrm_app.ue_ulrb[enb,ue] += rrm_app.lc_ue_ulrb[enb,ue,lc]
          rrm_app.enb_available_ulrb[enb] -= rrm_app.ue_ulrb[enb,ue]

          #calculate the required RB for DL
          rrm_app.ue_dlrb[enb,ue] = 0 # Error : if this var is 0-initialized here, the increment of this value a few lines after is equivalent to an assignement. This 0-initialisation should probably be put outside of this loop
          rrm_app.lc_ue_dlrb[enb,ue,lc] = 2 # f(bandwidth)
          dl_itbs = rrm_app_vars.mcs_to_itbs[rrm_app.ue_dlmcs[enb,ue]]
          rrm_app.lc_ue_dltbs[enb,ue,lc] = rrm_app_vars.tbs_table[dl_itbs][rrm_app.lc_ue_dlrb[enb,ue,lc]]
          while rrm_app.lc_ue_report[enb, ue, lc]['txQueueSize'] > rrm_app.lc_ue_dltbs[enb,ue,lc] :
            if rrm_app.lc_ue_dlrb[enb,ue,lc] > rrm_app.enb_available_dlrb[enb] :
              log.info('no available dlrb')
              break
            rrm_app.lc_ue_dlrb[enb,ue,lc] += 2 # f(bandwidth)
            rrm_app.lc_ue_dltbs[enb,ue,lc] = rrm_app_vars.tbs_table[dl_itbs][rrm_app.lc_ue_dlrb[enb,ue,lc]]

          rrm_app.ue_dlrb[enb,ue] += rrm_app.lc_ue_dlrb[enb,ue,lc]
          rrm_app.enb_available_dlrb[enb] -= rrm_app.ue_dlrb[enb,ue]

          # calculate the total RB for DL and UL

        rrm_app.ue_ultbs[enb,ue] = rrm_app_vars.tbs_table[ul_itbs][rrm_app.ue_ulrb[enb,ue]]
        rrm_app.ue_dltbs[enb,ue] = rrm_app_vars.tbs_table[dl_itbs][rrm_app.ue_dlrb[enb,ue]]

        log.info( 'eNB ' + str(enb) + ' UE ' + str(ue) + ' SFN ' + str(rrm_app.enb_sfn[enb,ue]) +
              ' DL TBS ' + str(rrm_app.ue_dltbs[enb,ue]) +
              ' ue_dlrb ' + str(rrm_app.ue_dlrb[enb,ue]) +
              ' ue_dlmcs ' + str(rrm_app.ue_dlmcs[enb,ue]) +
              ' --> expected DL throughput ' +  str(float(rrm_app.ue_dltbs[enb,ue]/1000.0)) + ' Mbps')

        log.info( 'eNB ' + str(enb) + ' UE ' + str(ue) + ' SFN ' + str(rrm_app.enb_sfn[enb,ue]) +
              ' UL TBS ' + str(rrm_app.ue_ultbs[enb,ue])   +
              ' ue_ulrb ' + str(rrm_app.ue_ulrb[enb,ue])   +
              ' ue_ulmcs ' + str(rrm_app.ue_ulmcs[enb,ue]) +
              ' --> expected UL throughput ' +  str(float(rrm_app.ue_ultbs[enb,ue]/1000.0)) + ' Mbps')


  def initialize_allocation(self, sm, rrm):
    # Loop on eNodeBs
    for enb in range(0, sm.get_num_enb()) :
      rrm_app.enb_available_ulrb[enb]= rrm_app.enb_ulrb[enb]
      rrm_app.enb_available_dlrb[enb]= rrm_app.enb_dlrb[enb]

      log.info('Available RB : UL ' + str(rrm_app.enb_available_ulrb[enb]) + ', DL ' + str(rrm_app.enb_available_dlrb[enb]) )

      for ue in range(0, sm.get_num_ue(enb=enb)) :

        # Initialization of MCS (Dl = conversion DL wideband CQI -> MCS, UL : fixed value) and number of RBs
        rrm_app.ue_dlmcs[enb,ue] = self.get_policy_mcs(rrm, enb, ue, "DL")
        rrm_app.ue_ulmcs[enb,ue] = self.get_policy_mcs(rrm, enb, ue, "UL")
        rrm_app.ue_ulrb[enb,ue]  = 0
        rrm_app.ue_dlrb[enb,ue]  = 0

        # skip the control channels, SRB1 and SRB2, start at index 2
        for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :

          # Initialization of number of RBs for LC
          rrm_app.lc_ue_ulrb[enb,ue,lc] = 0
          rrm_app.lc_ue_dlrb[enb,ue,lc] = 0

      # Initialize slices priority
      rrm_app.slices_priority_ul = []
      rrm_app.slices_priority_dl = []

      for sid in range(0, rrm.get_input_slice_nums(enb)):
        rrm_app.slices_priority_ul.append( (sid, rrm.get_input_slice_priority(enb, sid, "UL")) )
        rrm_app.slices_priority_dl.append( (sid, rrm.get_input_slice_priority(enb, sid, "DL")) )

      # Sort slices according to priority
      rrm_app.slices_priority_ul = sorted(rrm_app.slices_priority_ul, key=lambda slice: -slice[1])
      rrm_app.slices_priority_dl = sorted(rrm_app.slices_priority_dl, key=lambda slice: -slice[1])


  def allocate_rb_reserved_rate (self, sm):

    # Loop on eNodeBs
    for enb in range(0, sm.get_num_enb()) :

      # Loop on slices to allocate reserved rate, according to priority, for UL
      for slice in range(0, rrm.get_input_slice_nums(enb)):

        sid = rrm_app.slices_priority_ul[slice][0]
        slice_ul_tbs = 0

        # Loop on UEs connected to the current eNodeB and in the current slice
        ue_in_slice = (ue for ue in range(0, sm.get_num_ue(enb=enb)) if ue % rrm.get_input_slice_nums(enb) == sid)
        for ue in ue_in_slice :

          # skip the control channels, SRB1 and SRB2, start at index 2
          for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :

            # Make sure that slices with reserved rate get what they need, UL
            if rrm_app.reserved_rate_ul[enb][sid] > slice_ul_tbs / 1000 :

              # Initialization of number of RBs for LC, and of TBS for LC and slice
              ul_itbs                         = rrm_app_vars.mcs_to_itbs[rrm_app.ue_ulmcs[enb,ue]]
              ul_addtionnal_rb                = 0
              rrm_app.lc_ue_ultbs[enb,ue,lc]  = rrm_app_vars.tbs_table[ul_itbs][rrm_app.lc_ue_ulrb[enb,ue,lc]]
              slice_ul_tbs                    += rrm_app.lc_ue_ultbs[enb,ue,lc]

              # Add RBs for LC as long as : enough data is present AND slice reserved rate is not reached
              while rrm_app_vars.bsr_table[rrm_app.lc_ue_bsr[enb,ue,lc]] > rrm_app.lc_ue_ultbs[enb,ue,lc] and slice_ul_tbs / 1000 < rrm_app.reserved_rate_ul[enb][sid] :

                if ul_addtionnal_rb + 2 > rrm_app.enb_available_ulrb[enb] or rrm_app.enb_available_ulrb[enb] == 0 :
                  log.info('no available ulrb')
                  break

                # Update slice TBS (first remove old value for this LC), increment nb of RBs, update TBS (LC and slice)
                slice_ul_tbs                    -= rrm_app_vars.tbs_table[ul_itbs][rrm_app.lc_ue_ulrb[enb,ue,lc] + ul_addtionnal_rb]
                ul_addtionnal_rb                += 2 # f(bandwidth)
                rrm_app.lc_ue_ultbs[enb,ue,lc]  = rrm_app_vars.tbs_table[ul_itbs][rrm_app.lc_ue_ulrb[enb,ue,lc] + ul_addtionnal_rb]
                slice_ul_tbs                    += rrm_app_vars.tbs_table[ul_itbs][rrm_app.lc_ue_ulrb[enb,ue,lc] + ul_addtionnal_rb]

              rrm_app.lc_ue_ulrb[enb,ue,lc]   += ul_addtionnal_rb
              rrm_app.ue_ulrb[enb,ue]         += ul_addtionnal_rb
              rrm_app.enb_available_ulrb[enb] -= ul_addtionnal_rb


      # Loop on slices to allocate reserved rate, according to priority, for DL
      for slice in range(0, rrm.get_input_slice_nums(enb)):

        sid = rrm_app.slices_priority_dl[slice][0]
        slice_dl_tbs = 0

        # Loop on UEs connected to the current eNodeB and in the current slice
        ue_in_slice = (ue for ue in range(0, sm.get_num_ue(enb=enb)) if ue % rrm.get_input_slice_nums(enb) == sid)
        for ue in ue_in_slice :

          # skip the control channels, SRB1 and SRB2, start at index 2
          for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :

            # Make sure that slices with reserved rate get what they need, DL
            if rrm_app.reserved_rate_dl[enb][sid] > slice_dl_tbs / 1000 :

              # Initialization of number of RBs for LC, and of TBS for LC and slice
              dl_itbs                         = rrm_app_vars.mcs_to_itbs[rrm_app.ue_dlmcs[enb,ue]]
              dl_additionnal_rb               = 0
              rrm_app.lc_ue_dltbs[enb,ue,lc]  = rrm_app_vars.tbs_table[dl_itbs][rrm_app.lc_ue_dlrb[enb,ue,lc]]
              slice_dl_tbs                    += rrm_app.lc_ue_dltbs[enb,ue,lc]

              # Add RBs for LC as long as : enough data is present AND slice reserved rate is not reached
              while rrm_app.lc_ue_report[enb, ue, lc]['txQueueSize'] > rrm_app.lc_ue_dltbs[enb,ue,lc] and slice_dl_tbs / 1000 < rrm_app.reserved_rate_dl[enb][sid] :

                if dl_additionnal_rb + 2 > rrm_app.enb_available_dlrb[enb] or rrm_app.enb_available_dlrb[enb] == 0 :
                  log.info('no available dlrb')
                  break

                # Update slice TBS (first remove old value for this LC), increment nb of RBs, update TBS (LC and slice)
                slice_dl_tbs -= rrm_app_vars.tbs_table[dl_itbs][rrm_app.lc_ue_dlrb[enb,ue,lc] + dl_additionnal_rb]
                dl_additionnal_rb += 1 # f(bandwidth)
                rrm_app.lc_ue_dltbs[enb,ue,lc] = rrm_app_vars.tbs_table[dl_itbs][rrm_app.lc_ue_dlrb[enb,ue,lc] + dl_additionnal_rb]
                slice_dl_tbs += rrm_app_vars.tbs_table[dl_itbs][rrm_app.lc_ue_dlrb[enb,ue,lc] + dl_additionnal_rb]

              rrm_app.lc_ue_dlrb[enb,ue,lc]   += dl_additionnal_rb
              rrm_app.enb_available_dlrb[enb] -= dl_additionnal_rb
              rrm_app.ue_dlrb[enb,ue]         += dl_additionnal_rb


        log.info( 'slice ' + str(sid) + ' --> expected DL/UL throughput ' +  str(float(slice_dl_tbs/1000.0)) + 'Mbps/' + str(float(slice_ul_tbs/1000.0)) + 'Mbps')


  def allocate_rb_priority (self, sm):

    # Loop on eNodeBs
    for enb in range(0, sm.get_num_enb()) :

      # Loop on slices to allocate reserved rate, according to priority, for UL
      for slice in range(0, rrm.get_input_slice_nums(enb)):

        sid = rrm_app.slices_priority_ul[slice][0]

        # Loop on UEs connected to the current eNodeB and in the current slice
        ue_in_slice = (ue for ue in range(0, sm.get_num_ue(enb=enb)) if ue % rrm.get_input_slice_nums(enb) == sid)
        for ue in ue_in_slice :

          # skip the control channels, SRB1 and SRB2, start at index 2
          for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :

            # Initialization of number of RBs for LC, and of TBS for LC
            ul_itbs                         = rrm_app_vars.mcs_to_itbs[rrm_app.ue_ulmcs[enb,ue]]
            ul_addtionnal_rb                = 0
            rrm_app.lc_ue_ultbs[enb,ue,lc]  = rrm_app_vars.tbs_table[ul_itbs][rrm_app.lc_ue_ulrb[enb,ue,lc]]

            # Add RBs for LC as long as : enough data is present
            while rrm_app_vars.bsr_table[rrm_app.lc_ue_bsr[enb,ue,lc]] > rrm_app.lc_ue_ultbs[enb,ue,lc] :

              if ul_addtionnal_rb + 2 > rrm_app.enb_available_ulrb[enb] or rrm_app.enb_available_ulrb[enb] == 0 :
                log.info('no available ulrb')
                break

              # Increment nb of RBs, update TBS for LC
              ul_addtionnal_rb                += 2 # f(bandwidth)
              rrm_app.lc_ue_ultbs[enb,ue,lc]  = rrm_app_vars.tbs_table[ul_itbs][rrm_app.lc_ue_ulrb[enb,ue,lc] + ul_addtionnal_rb]

            rrm_app.lc_ue_ulrb[enb,ue,lc]   += ul_addtionnal_rb
            rrm_app.ue_ulrb[enb,ue]         += ul_addtionnal_rb
            rrm_app.enb_available_ulrb[enb] -= ul_addtionnal_rb


      # Loop on slices to allocate reserved rate, according to priority, for DL
      for slice in range(0, rrm.get_input_slice_nums(enb)):

        sid = rrm_app.slices_priority_dl[slice][0]
        slice_dl_tbs = 0

        # Loop on UEs connected to the current eNodeB and in the current slice
        ue_in_slice = (ue for ue in range(0, sm.get_num_ue(enb=enb)) if ue % rrm.get_input_slice_nums(enb) == sid)
        for ue in ue_in_slice :

          # skip the control channels, SRB1 and SRB2, start at index 2
          for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :

            # Initialization of number of RBs for LC, and of TBS for LC
            dl_itbs                         = rrm_app_vars.mcs_to_itbs[rrm_app.ue_dlmcs[enb,ue]]
            dl_additionnal_rb               = 0
            rrm_app.lc_ue_dltbs[enb,ue,lc]  = rrm_app_vars.tbs_table[dl_itbs][rrm_app.lc_ue_dlrb[enb,ue,lc]]

            # Add RBs for LC as long as : enough data is present
            while rrm_app.lc_ue_report[enb, ue, lc]['txQueueSize'] > rrm_app.lc_ue_dltbs[enb,ue,lc] :

              if dl_additionnal_rb + 2 > rrm_app.enb_available_dlrb[enb] or rrm_app.enb_available_dlrb[enb] == 0 :
                log.info('no available dlrb')
                break

              # Increment nb of RBs, update TBS for LC
              dl_additionnal_rb += 2 # f(bandwidth)
              rrm_app.lc_ue_dltbs[enb,ue,lc] = rrm_app_vars.tbs_table[dl_itbs][rrm_app.lc_ue_dlrb[enb,ue,lc] + dl_additionnal_rb]

            rrm_app.lc_ue_dlrb[enb,ue,lc]   += dl_additionnal_rb
            rrm_app.enb_available_dlrb[enb] -= dl_additionnal_rb
            rrm_app.ue_dlrb[enb,ue]         += dl_additionnal_rb


  def allocate_rb (self, sm):

    # Loop on eNodeBs
    for enb in range(0, sm.get_num_enb()) :
      # Loop on UEs attached to the current eNodeB
      for ue in range(0, sm.get_num_ue(enb=enb)) :
        # skip the control channels, SRB1 and SRB2, start at index 2
        for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :

          # Initialization of number of RBs for LC, and of TBS for LC
          ul_itbs                         = rrm_app_vars.mcs_to_itbs[rrm_app.ue_ulmcs[enb,ue]]
          ul_addtionnal_rb                = 0
          rrm_app.lc_ue_ultbs[enb,ue,lc]  = rrm_app_vars.tbs_table[ul_itbs][rrm_app.lc_ue_ulrb[enb,ue,lc]]

          # Add RBs for LC as long as enough data is present
          while rrm_app_vars.bsr_table[rrm_app.lc_ue_bsr[enb,ue,lc]] > rrm_app.lc_ue_ultbs[enb,ue,lc] :

            if ul_addtionnal_rb + 2 > rrm_app.enb_available_ulrb[enb] or rrm_app.enb_available_ulrb[enb] == 0 :
              log.info('no available ulrb')
              break

            # Increment nb of RBs, update TBS
            ul_addtionnal_rb += 2 # f(bandwidth)
            rrm_app.lc_ue_ultbs[enb,ue,lc]=rrm_app_vars.tbs_table[ul_itbs][rrm_app.lc_ue_ulrb[enb,ue,lc] + ul_addtionnal_rb]

          rrm_app.lc_ue_ulrb[enb,ue,lc]   += ul_addtionnal_rb
          rrm_app.enb_available_ulrb[enb] -= ul_addtionnal_rb
          rrm_app.ue_ulrb[enb,ue]         += ul_addtionnal_rb


          # Initialization of number of RBs for LC, and of TBS for LC
          dl_itbs                         = rrm_app_vars.mcs_to_itbs[rrm_app.ue_dlmcs[enb,ue]]
          dl_additionnal_rb               = 0
          rrm_app.lc_ue_dltbs[enb,ue,lc]  = rrm_app_vars.tbs_table[dl_itbs][rrm_app.lc_ue_dlrb[enb,ue,lc]]

          # Add RBs for LC as long as : enough data is present AND slice reserved rate is not reached
          while rrm_app.lc_ue_report[enb, ue, lc]['txQueueSize'] > rrm_app.lc_ue_dltbs[enb,ue,lc] :

            if dl_additionnal_rb + 2 > rrm_app.enb_available_dlrb[enb] or rrm_app.enb_available_dlrb[enb] == 0 :
              log.info('no available dlrb')
              break

            # Increment nb of RBs, update TBS
            dl_additionnal_rb               += 2 # f(bandwidth)
            rrm_app.lc_ue_dltbs[enb,ue,lc]  = rrm_app_vars.tbs_table[dl_itbs][rrm_app.lc_ue_dlrb[enb,ue,lc] + dl_additionnal_rb]

          rrm_app.lc_ue_dlrb[enb,ue,lc]   += dl_additionnal_rb
          rrm_app.enb_available_dlrb[enb] -= dl_additionnal_rb
          rrm_app.ue_dlrb[enb,ue]         += dl_additionnal_rb


        # calculate the total RB for DL and UL
        rrm_app.ue_ultbs[enb,ue] = rrm_app_vars.tbs_table[ul_itbs][rrm_app.ue_ulrb[enb,ue]]
        rrm_app.ue_dltbs[enb,ue] = rrm_app_vars.tbs_table[dl_itbs][rrm_app.ue_dlrb[enb,ue]]

        log.info( 'eNB ' + str(enb) + ' UE ' + str(ue) + ' SFN ' + str(rrm_app.enb_sfn[enb,ue]) +
              ' DL TBS ' + str(rrm_app.ue_dltbs[enb,ue]) +
              ' ue_dlrb ' + str(rrm_app.ue_dlrb[enb,ue]) +
              ' ue_dlmcs ' + str(rrm_app.ue_dlmcs[enb,ue]) +
              ' --> expected DL throughput ' +  str(float(rrm_app.ue_dltbs[enb,ue]/1000.0)) + ' Mbps')

        log.info( 'eNB ' + str(enb) + ' UE ' + str(ue) + ' SFN ' + str(rrm_app.enb_sfn[enb,ue]) +
              ' UL TBS ' + str(rrm_app.ue_ultbs[enb,ue])   +
              ' ue_ulrb ' + str(rrm_app.ue_ulrb[enb,ue])   +
              ' ue_ulmcs ' + str(rrm_app.ue_ulmcs[enb,ue]) +
              ' --> expected UL throughput ' +  str(float(rrm_app.ue_ultbs[enb,ue]/1000.0)) + ' Mbps')


  def calculate_exp_kpi_perf (self, sm, rrm) :
    self.initialize_allocation(sm, rrm)
    self.allocate_rb_reserved_rate(sm)
    self.allocate_rb_priority(sm)
    self.allocate_rb(sm)


  def determine_rb_share(self,sm,rrm):

    # Loop on eNodeBs
    for enb in range(0, sm.get_num_enb()) :

      rrm_app.enb_ulrb_share_r1[enb]=0.0
      rrm_app.enb_dlrb_share_r1[enb]=0.0
      rrm_app.enb_ulrb_share[enb]=0.0
      rrm_app.enb_dlrb_share[enb]=0.0

      # Loop on slices
      for sid in range(0, rrm.get_input_slice_nums(enb)):
        rrm_app.slice_ulrb[enb,sid]=0.0
        rrm_app.slice_dlrb[enb,sid]=0.0
        rrm_app.slice_ulrb_share_r1[enb,sid]=0.0
        rrm_app.slice_dlrb_share_r1[enb,sid]=0.0
        rrm_app.slice_ulrb_share[enb,sid]=0.0
        rrm_app.slice_dlrb_share[enb,sid]=0.0

        # Loop on UEs
        for ue in range(0, sm.get_num_ue(enb=enb)) :
          # simple ue to slice mapping
          if ue % rrm.get_input_slice_nums(enb) == sid :
            rrm_app.slice_ulrb[enb,sid] += rrm_app.ue_ulrb[enb,ue]
            rrm_app.slice_dlrb[enb,sid] += rrm_app.ue_dlrb[enb,ue]

        # Compute the share for each slice (ressource blocs for slice/number of ressource blocs for the eNB) for UL and DL and set a minimum of 0.1 share
        rrm_app.slice_ulrb_share[enb,sid] = float(rrm_app.slice_ulrb[enb,sid]/rrm_app.enb_ulrb[enb])
        rrm_app.slice_dlrb_share[enb,sid] = float(rrm_app.slice_dlrb[enb,sid]/rrm_app.enb_dlrb[enb])
        if rrm_app.slice_ulrb_share[enb,sid] < 0.1 and rrm_app.slice_ulrb_share[enb,sid] > 0.0:
          rrm_app.slice_ulrb_share[enb,sid]= 0.1
        if rrm_app.slice_dlrb_share[enb,sid] < 0.1 and rrm_app.slice_dlrb_share[enb,sid] > 0.0:
          rrm_app.slice_dlrb_share[enb,sid]= 0.1
	
	if rrm_app.slice_ulrb_share[enb,sid] > 1.0:
          rrm_app.slice_ulrb_share[enb,sid]= 1.0
        if rrm_app.slice_dlrb_share[enb,sid] > 1.0:
          rrm_app.slice_dlrb_share[enb,sid]= 1.0


        log.info( 'S1: eNB ' + str(enb) + ' Slice ' + str(sid) + ' SFN ' + str(rrm_app.enb_sfn[enb,0]) +
              ' slice_ulrb_share: ' + str(rrm_app.slice_ulrb_share[enb,sid]) +
              ' slice_dlrb_share: ' + str(rrm_app.slice_dlrb_share[enb,sid]) )

        # save the allocated rb per slice based on the enforced policy for stage 2 allocation 
        rrm_app.slice_ulrb_share_r1[enb,sid]= rrm_app.slice_ulrb_share[enb,sid]
        rrm_app.slice_dlrb_share_r1[enb,sid]= rrm_app.slice_dlrb_share[enb,sid]


        # Accumulate the total share occupied by slices at the eNB, for UL and DL
        rrm_app.enb_ulrb_share[enb]+=rrm_app.slice_ulrb_share[enb,sid]
        rrm_app.enb_dlrb_share[enb]+=rrm_app.slice_dlrb_share[enb,sid]


        # save the allocated rb per enb based on the enforced policy for stage 2 allocation 
      rrm_app.enb_ulrb_share_r1[enb]=rrm_app.enb_ulrb_share[enb]
      rrm_app.enb_dlrb_share_r1[enb]=rrm_app.enb_dlrb_share[enb]

      nb_slice_to_share=0
      for sid in range(0, rrm.get_input_slice_nums(enb)):  
        if rrm_app.reserved_isolation_ul[enb][sid] == 0 :
          nb_slice_to_share+=1 # multiplex
      
      # Disribute the remaining RB at the second stage : divide the remaining RBs by the number of slices
      # TODO: allocate based on SLA
      extra_ul=((1.0 - rrm_app.enb_ulrb_share[enb])/rrm.get_input_slice_nums(enb))
      extra_dl=((1.0 - rrm_app.enb_dlrb_share[enb])/rrm.get_input_slice_nums(enb))
      for sid in range(0, rrm.get_input_slice_nums(enb)):

        if  extra_ul > 0 and rrm_app.reserved_isolation_ul[enb][sid] == 0:
          rrm_app.slice_ulrb_share[enb,sid]+=extra_ul
          rrm_app.enb_ulrb_share[enb]+=extra_ul

        if  extra_dl > 0 and rrm_app.reserved_isolation_dl[enb][sid] == 0:
          rrm_app.slice_dlrb_share[enb,sid]+=extra_dl
          rrm_app.enb_dlrb_share[enb]+=extra_dl


        log.debug( 'S2: eNB ' + str(enb) + ' Slice ' + str(sid) + ' SFN ' + str(rrm_app.enb_sfn[enb,0]) +
              ' slice_ulrb_share: ' + str(rrm_app.slice_ulrb_share_r1[enb,sid]) + '->' + str(rrm_app.slice_ulrb_share[enb,sid]) +
              ' slice_dlrb_share: ' + str(rrm_app.slice_dlrb_share_r1[enb,sid]) + '->' +    str(rrm_app.slice_dlrb_share[enb,sid]) )

        log.info( 'eNB ' + str(enb) + ' Slice ' + str(sid) + ' SFN ' + str(rrm_app.enb_sfn[enb,0]) +
            ' ulrb_share: ' + str(rrm_app.enb_ulrb_share_r1[enb]) + '->' + str(rrm_app.enb_ulrb_share[enb]) +
            ' dlrb_share: ' + str(rrm_app.enb_dlrb_share_r1[enb]) + '->' + str(rrm_app.enb_dlrb_share[enb])      )


  def enforce_policy(self,sm,rrm):

    for enb in range(0, sm.get_num_enb()) :
      for sid in range(0, rrm.get_input_slice_nums(enb)):

        # set the policy files
        rrm.set_slice_rb(sid=sid,rb=rrm_app.slice_ulrb_share[enb,sid], dir='UL')
        rrm.set_slice_rb(sid=sid,rb=rrm_app.slice_dlrb_share[enb,sid], dir='DL')
        rrm.set_slice_maxmcs(sid=sid,maxmcs=min(rrm_app.maxmcs_ul[enb][sid],rrm_app.enb_ulmaxmcs[enb]), dir='UL')
        rrm.set_slice_maxmcs(sid=sid,maxmcs=min(rrm_app.maxmcs_dl[enb][sid],rrm_app.enb_dlmaxmcs[enb]), dir='DL')

        # ToDO: check if we should push sth
      if sm.get_num_ue(enb) > 0 :
        if rrm.apply_policy() == 'connected' :
          rrm_app.pf=rrm.save_policy(time=rrm_app.enb_sfn[enb,0])
          log.info('_____________eNB' + str(enb)+' enforced policy______________')
          print rrm.dump_policy()
      else:
        log.info('No UE is attached yet')


  def run(self, sm, rrm):
    log.info('2. Reading the status of the underlying eNBs')
    sm.stats_manager('all')

    log.info('3. Gather statistics')
    rrm.read_template()
    rrm_app.get_statistics(sm)
    rrm_app.get_policy_maxmcs(rrm,sm)
    rrm_app.get_policy_reserved_rate(rrm,sm)
    
    rrm.set_num_slices(n=int(rrm.get_input_slice_nums(0)), dir='DL')
    rrm.set_num_slices(n=int(rrm.get_input_slice_nums(0)), dir='UL')

    log.info('4. Calculate the expected performance')
    rrm_app.calculate_exp_kpi_perf(sm, rrm)

    log.info('5. Determine RB share per slice')
    rrm_app.determine_rb_share(sm,rrm)

    log.info('6. Check for new RRM Slice policy')
    rrm_app.enforce_policy(sm,rrm)

    t = Timer(5, self.run,kwargs=dict(sm=sm,rrm=rrm))
    t.start()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Process some integers.')

  parser.add_argument('--url', metavar='[option]', action='store', type=str,
            required=False, default='http://localhost',
            help='set the FlexRAN RTC URL: loalhost (default)')
  parser.add_argument('--port', metavar='[option]', action='store', type=str,
            required=False, default='9999',
            help='set the FlexRAN RTC port: 9999 (default)')
  parser.add_argument('--template', metavar='[option]', action='store', type=str,
            required=False, default='template_1',
            help='set the slice template to indicate the type of each slice: template_1(default), .... template_4')
  parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
            required=False, default='sdk',
            help='Set the app operation mode either with FlexRAN or with the test json files: test, sdk(default)')
  parser.add_argument('--log',  metavar='[level]', action='store', type=str,
            required=False, default='info',
            help='set the log level: debug, info (default), warning, error, critical')
  parser.add_argument('--version', action='version', version='%(prog)s 1.0')

  args = parser.parse_args()

  log=flexran_sdk.logger(log_level=args.log).init_logger()

  rrm_app = rrm_app(log=log,
            template=args.template,
            url=args.url,
            port=args.port,
            log_level=args.log,
            op_mode=args.op_mode)

  rrm = flexran_sdk.rrm_policy(log=log,
                 url=args.url,
                 port=args.port,
                 op_mode=args.op_mode)
  policy=rrm.read_policy()

  sm = flexran_sdk.stats_manager(log=log,
                   url=args.url,
                   port=args.port,
                   op_mode=args.op_mode)

  py3_flag = version_info[0] > 2

  t = Timer(3, rrm_app.run,kwargs=dict(sm=sm,rrm=rrm))
  t.start()

