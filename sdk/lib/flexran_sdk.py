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

""" FlexRAN software development kit (SDK)

    @file: flexran_sdk.py
    @author: navid nikaein
    @brief: Library to get and set accessible paramters and operation through the FlexRAN RTC
    @version: 1.0
    @date: 7 July 2017
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
import yaml

from logger import *

from enum import Enum


class rrc_triggers(Enum):
    """!@brief RRC Measurements trigger types
    
    """

    ONE_SHOT = 0
    PERIODIC = 1
    EVENT_DRIVEN= 2

class cd_actions(Enum):
    """!@brief control delegation actions

    """

    PULL = 0
    PUSH = 1
    
    #def describe(self):
        #return self.name, self.value

    #def __str__(self):
        #return '%s' % self._value_

class flexran_rest_api(object):
    """!@brief  FlexRAN supported REST APIs endpoints

    """
 
    """!@brief Output data sets for all the status used for test"""
    pf_all='outputs/all_2.json'
    """!@brief Output data sets for MAC  status used for test"""
    pf_mac='outputs/mac_stats_2.json'
    """!@brief Output data sets for eNB config status used for test"""
    pf_enb='outputs/enb_config_2.json'

    # relateive to flexran apps
    pf_name='enb_scheduling_policy.yaml'
    pf_yaml='../tests/delegation_control/'+pf_name
    pf_json='{"mac": [{"dl_scheduler": {"parameters": {"n_active_slices": 1,"slice_percentage": [1,0.4,0,0],"slice_maxmcs": [28,28,28,28 ]}}}]}'

    """!@brief RRC API endpoit """ 
    rrc_trigger='/rrc_trigger'
    """!@brief control delegation API endpoint for DL """ 
    cd_dl='/dl_sched'
    """!@brief control delegation API endpoint for DL """ 
    cd_ul='/ul_sched'

    """!@brief RRM API endpoint """ 
    rrm='/rrm'  
    """!@brief RRM API endpoint with config as a payload """    
    rrm_policy='/rrm_config'  


    """!@brief full status API endpoint for  """    
    sm_all='/stats_manager/json/all'
    """!@brief eNb config status API endpoint for  """    
    sm_enb='/stats_manager/json/enb_config'
    """!@brief MAC status API endpoint for  """    
    sm_mac='/stats_manager/json/mac_stats'
        
class rrc_trigger_meas(object):
    """!@brief RRC trigger measurement class

    This class is used to trigger measurement events in the UE for the reception of RSRP and RSRQ values of the neighboring cells.
    The REST API end point is /rrc_trigger
    @todo make the measurment trigger event reconfigurable
    """
    def __init__(self, log, url='http://localhost', port='9999', op_mode='test'):
        """!@brief Class constructor """
        super(rrc_trigger_meas, self).__init__()
        
        self.url = url+':'+port
        self.status = ''
        self.op_mode = op_mode
        self.log = log

        self.rrc_trigger_api=flexran_rest_api.rrc_trigger

        self.rrc_meas = {}
        self.rrc_meas[rrc_triggers.ONE_SHOT]      = 'ONE_SHOT'
        self.rrc_meas[rrc_triggers.PERIODIC]       = 'PERIODIC'
        self.rrc_meas[rrc_triggers.EVENT_DRIVEN]  = 'EVENT_DRIVEN'
        

    def trigger_meas(self, type='PERIODIC'):
        """!@brief Set the type of RRC trigger measurments
        
        @param type: ONE_SHOT, PERIODIC, and EVENT_DRIVEN
        """
        if type == self.rrc_meas[rrc_triggers.ONE_SHOT] :
            url = self.url+self.rrc_trigger_api+'/'+type.lower()
        elif type == self.rrc_meas[rrc_triggers.PERIODIC] :
            url = self.url+self.rrc_trigger_api+'/'+type.lower()
        elif type == self.rrc_meas[rrc_triggers.EVENT_DRIVEN] :
            url = self.url+self.rrc_trigger_api+'/'+type.lower()
        else:
            self.log.error('Type ' + type + 'not supported')
            return
        
        if self.op_mode == 'test' :
            self.log.info('POST ' + str(url))

        elif self.op_mode == 'sdk' : 
            try :
                req = requests.post(url)
                if req.status_code == 200 :
                    self.log.error('successfully delegated the dl scheduling to the agent' )
                    self.status='connected'
                else :
                    self.status='disconnected'
                self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to delegate the DL schedling to the agent' )

        else :
            self.log.warn('Unknown operation mode ' + op_mode )       

class control_delegate(object):
    """!@brief Control delegation class

       This class is used to delegate the control to the agent.
    """
      
    def __init__(self, log, url='http://localhost', port='9999', op_mode='test'):
        """!@brief Class constructor """
        super(control_delegate, self).__init__()

        self.url = url+':'+port
        self.status = ''
        self.op_mode = op_mode
        self.log = log
        # NB APIs endpoints
        self.cd_dl_api=flexran_rest_api.cd_dl
        self.cd_ul_api=flexran_rest_api.cd_ul
        #self.cd_actions[cd_actions.PULL]='PULL'
        #self.cd_actions[cd_actions.PUSH]='PUSH'
        self.actions = {}
        self.actions[cd_actions.PULL] = 'PULL'
        self.actions[cd_actions.PUSH] = 'PUSH'
        
    def delegate_agent(self, func='dl_sched', action='PUSH'):
        """!@brief Delegate a control function to the agent
        
        @param func: name of the function
        @param action: action to be performed by the controller
        """
    
        if func == 'dl_sched' : 
            url = self.url+self.cd_dl_api
        elif func == 'ul_sched' :
            url = self.url+self.cd_ul_api
        else :
            self.log.error('Func ' + fucn + 'not supported')
            return 

        if action == self.actions[cd_actions.PULL] :
            self.log.debug('Action: Pull ' + func + 'to the controller')
            url = url + '/0'
        elif action == self.actions[cd_actions.PUSH] :
            self.log.debug('Action: Push/delegate ' + func + 'to the agent' )
            url = url + '/1'

        if self.op_mode == 'test' :
            self.log.info('POST ' + str(url))

        elif self.op_mode == 'sdk' : 
            try :
                req = requests.post(url)
                if req.status_code == 200 :
                    self.log.error('successfully delegated the dl scheduling to the agent' )
                    self.status='connected'
                else :
                    self.status='disconnected'
                self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to delegate the DL schedling to the agent' )

        else :
            self.log.warn('Unknown operation mode ' + op_mode )                 
        
class rrm_policy (object):
    """!@brief Apply a radio resource management policy to the underlying RAN
        
        This class reads, creates, updates, and applies a policy 
        """
    def __init__(self, log, url='http://localhost', port='9999', op_mode='test'):
        """!@brief Class constructor """
        super(rrm_policy, self).__init__()
        
        self.url = url+':'+port
        self.status = 0
        self.op_mode = op_mode
        self.log = log
        # NB APIs endpoints
        self.rrm_api=flexran_rest_api.rrm
        self.rrm_policy_api=flexran_rest_api.rrm_policy
        # stats manager data requeted by the endpoint
        # could be extended to have data per API endpoint
        self.policy_data = ''

        # test files
        # location must be reletaive to app and not SDK
        # To do: create env vars 
        self.pf_yaml=flexran_rest_api.pf_yaml
        self.pf_json=flexran_rest_api.pf_json

    # read the policy file     
    def read_policy(self, pf=''):
        """!@brief Read the policy either from a user-defined policy file or the default one
        
        @param pf: the absolut path to the policy file
        """

        if os.path.isfile(pf) :
            pfile=pf
        elif os.path.isfile(self.pf_yaml) :
            pfile=self.pf_yaml
        else :
            self.log.error('cannot find the policy file '  + self.pf_yaml + ' or ' + pf)
            return

                
        try:
            with open(pfile) as data_file:
                self.policy_data = yaml.load(data_file)
                self.log.debug(yaml.dump(self.policy_data, default_flow_style=False))
        except yaml.YAMLError, exc:
            self.log.error('error in policy file'  + pfile + str(exc) )
	    return	

	self.print_policy() 
   
        return self.policy_data

    # apply policy with policy data 
    # TBD: apply policy from a file
    def apply_policy(self, policy_data='',as_payload=True):
        """!@brief Apply the default or user-defined policy 
        
        @param policy_data: content of the policy file
        @param as_payload: embed the applied policy as a payload
        """

        self.status=''

        if policy_data != '' :
            pdata=policy_data
        elif self.policy_data != '' :
            pdata=self.policy_data 
        else:
            self.log.error('cannot find the policy data '  + pdata)
            return
	
        if as_payload == True :
            url = self.url+self.rrm_policy_api
        else: 
            url = self.url+self.rrm_api+'/'+flexran_rest_api.pf_name
        
        if self.op_mode == 'test' :
            self.log.info('POST ' + str(url))
            self.log.debug(self.dump_policy(policy_data=pdata))
            self.status='connected'
            
        elif self.op_mode == 'sdk' :
            print self.dump_policy(pdata)
            try :
		# post data as binary
            	req = requests.post(url, data=self.dump_policy(pdata),headers={'Content-Type': 'application/octet-stream'})
		
            	if req.status_code == 200:
            	    self.log.info('successfully applied the policy')
            	    self.status='connected'
            	else :
            	    self.status='disconnected'
            	    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to apply the policy ' )
            
        else :
            self.log.warn('Unknown operation mode ' + op_mode )
	    self.status='unknown'
        return self.status 

    def dump_policy(self, policy_data=''):
        """!@brief return the content of the policy in ymal format
        
        @param policy_data: content of the policy file
        """
        
        if policy_data != '' :
            return yaml.dump(policy_data, default_flow_style=False, default_style='"')
        elif self.policy_data != '' :
            return yaml.dump(self.policy_data, default_flow_style=False, default_style='"')
        else:
            self.log.error('cannot find the policy data ' + policy_data)
            return

    def print_policy(self):
        """!@brief Dump the policy in the ymal format
        
        """

        print self.dump_policy()

    def save_policy(self, basedir='./', basefn='policy', time=0, format='yaml'):
        """!@brief Save the applied policy in a user-defined path and format
        
        @param basedir: base directory
        @param basefn: base file name
        @param time: timestamp when the policy is applied
        @param format: the file extension
        """

        fn = os.path.join(basedir,basefn + '_'+str(time) + "." + format)
        #stream = file('policy.yaml', 'w')
        stream = file(fn, 'w')

        if format == 'yaml' or format == 'YAML':
            yaml.dump(self.policy_data, stream)
        elif format == 'json' :
            json.dump(self.policy_data, stream)
        else :
            self.log.error('unsupported format')
            
        return self.policy_data
            
    def set_num_slices(self, n=1, dir='dl'):
        """!@brief Set the number of RAN slices to be created/updated in the policy file for a  direction
        
        @param n: number of slices
        @param dir: defines downlink or uplink direction
        """
        
        if dir == 'dl' or dir == "DL":
            index = 0
            key_sched = 'dl_scheduler'
            key_slice = 'n_active_slices'
            
        elif dir == 'ul' or dir == "UL":
            index = 1
            key_sched = 'ul_scheduler'
            key_slice = 'n_active_slices_uplink'
        else :
            self.log.error('Unknown direction ' + dir)
            return
        
            
        self.log.debug('Setting the number of ' + dir + ' slices from ' + str(self.policy_data['mac'][index][key_sched]['parameters'][key_slice]) + ' to ' + str(n) )
        self.policy_data['mac'][index][key_sched]['parameters'][key_slice]=n

    def get_num_slices(self, dir='dl'):
        """!@brief Get the current number of RAN slices for a  direction
        
        @param dir: defines downlink or uplink direction  
        """
      
        if dir == 'dl' or dir == "DL":
            index = 0
            key_sched = 'dl_scheduler'
            key_slice = 'n_active_slices'
        elif dir == 'ul' or dir == "UL":
            index = 1
            key_sched = 'ul_scheduler'
            key_slice = 'n_active_slices_uplink'
        else :
            self.log.error('Unknown direction ' + dir)
            return
        

        return  self.policy_data['mac'][index][key_sched]['parameters'][key_slice]
    
                

    def set_slice_rb(self, sid, rb, dir='dl'):
        """!@brief Set the resource block share for a slice in a direction. 
        
        @param sid: slice id
        @param rb: percentage of RB share, which is between [0,1]
        @param dir: defines downlink or uplink direction 

        @note: the sume of rb share acorss all the slices should be 1. The total number of slice is 4.
        
        """

        if sid < 0 or sid > 4 :
            self.log.error('Out of Range slice id')
            return
        # rb_percentage
        if rb < 0 or rb > 1 : 
            self.log.error('Out of Range RB percentage')
            return
        

        if dir == 'dl' or dir == "DL":
            index = 0
            key_sched = 'dl_scheduler'
            key_slice = 'slice_percentage'
        elif dir == 'ul' or dir == "UL":
            index = 1
            key_sched = 'ul_scheduler'
            key_slice = 'slice_percentage_uplink'
        else :
            self.log.error('Unknown direction ' + dir)
            return
            
        self.log.debug('Setting ' + dir + ' slice ' + str(sid) + ' RB from ' + str(self.policy_data['mac'][index][key_sched]['parameters'][key_slice][sid]) + ' to ' + str(rb) )
        self.policy_data['mac'][index][key_sched]['parameters'][key_slice][sid]=rb
        #print self.policy_data['mac'][index][key_sched]['parameters'][key_slice][sid]


        
    def get_slice_rb(self, sid, dir='dl'):
        """!@brief Get the current resource block share for a slice in a  direction 
        
        @param sid: slice id
        @param dir: defines downlink or uplink direction 
        """
        if sid < 0 or sid > 4 :
            self.log.error('Out of Range slice id')
            return
        
       
        if dir == 'dl' or dir == "DL":
            index = 0
            key_sched = 'dl_scheduler'
            key_slice = 'slice_percentage'
        elif dir == 'ul' or dir == "UL":
            index = 1
            key_sched = 'ul_scheduler'
            key_slice = 'slice_percentage_uplink'
        else :
            self.log.error('Unknown direction ' + dir)
            return

        return self.policy_data['mac'][index][key_sched]['parameters'][key_slice][sid]

    def set_slice_maxmcs(self, sid, maxmcs=28, dir='dl'):
        """!@brief Set the maximum modulation and coding scheme (MCS) for a slice in a given direction 
        
        @param sid: slice id
        @param maxmcs: maximum supported MCS
        @param dir: defines downlink or uplink direction
        @note: MAX MCS determines the maximum achievable throughput for a slice given its RB share.
        """

        if dir == 'dl' or dir == "DL":
            index = 0
            key_sched = 'dl_scheduler'
            key_mcs = 'slice_maxmcs'
            mcs=min(maxmcs,28)
        elif dir == 'ul' or dir == "UL":
            index = 1
            key_sched = 'ul_scheduler'
            key_mcs   = 'slice_maxmcs_uplink'
            # ToDO: use get_cell_maxmcs(enb) from sm
            mcs = min(maxmcs,16)
        else :
            self.log.error('Unknown direction ' + dir)
            return
            
 
        self.log.debug('Setting ' + dir + ' slice ' + str(sid) + ' MCS from ' + str(self.policy_data['mac'][index][key_sched]['parameters'][key_mcs][sid]) + ' to ' + str(mcs))
        self.policy_data['mac'][index][key_sched]['parameters'][key_mcs][sid]=mcs
        #print self.policy_data['mac'][index][key_sched]['parameters'][key_mcs][sid]

    def get_slice_maxmcs(self, sid, dir='dl'):
        """!@brief Get the current maximum MCS for a slice in a given direction 
        
        @param sid: slice id
        @param dir: defines downlink or uplink direction
        """

        if dir == 'dl' or dir == "DL":
            index = 0
            key_sched = 'dl_scheduler'
            key_mcs = 'slice_maxmcs'
        elif dir == 'ul' or dir == "UL":
            index = 1
            key_sched = 'ul_scheduler'
            key_mcs = 'slice_maxmcs_uplink'
        else :
            self.log.error('Unknown direction ' + dir)
            return
            
        if sid < 0 or sid > 4 :
            self.log.error('Out of Range slice id')
            return
 
        return self.policy_data['mac'][index][key_sched]['parameters'][key_mcs][sid]

    
class stats_manager(object):
    """!@brief Statistic manager class 
    
    This class provides high-level APIS to read and process realtime Radio information received from the underlying RAN
    """

    def __init__(self, log, url='http://localhost', port='9999', op_mode='test'):

        super(stats_manager, self).__init__()
        """!@brief URL of the controller """
        self.url = url+':'+port
        """!@brief status of API calls"""
        self.status = 0
        """!@brief operation mode of FlexRAN SDK: test or SDK"""
        self.op_mode = op_mode
        self.log = log
        """!@brief Local API endpoints"""
        self.sm_all_api=flexran_rest_api.sm_all
        self.sm_enb_api=flexran_rest_api.sm_enb
        self.sm_mac_api=flexran_rest_api.sm_mac

        # stats manager data requeted by the endpoint
        # could be extended to have data per API endpoint
        """!@brief content of status received by the controller """
        self.stats_data = ''
        
        """!@brief Test policy files"""
        self.pfile_all=flexran_rest_api.pf_all
        """!@brief Test policy file for MAC """
        self.pfile_mac=flexran_rest_api.pf_mac
        """!@brief Test policy files for eNB"""
        self.pfile_enb=flexran_rest_api.pf_enb
        

    def stats_manager(self, api):
        """!@brief Request the statistics from the controller and store it locally.

        @param api: defines the what type of stats shall be requested, available values: all, mac, eNB 
        """

        self.log.debug('set stats_manager API to :' + str(api))
        file = ''
        #url = '' 
        if self.op_mode == 'test' :
            
            if 'all' in api :
                file =  self.pfile_all
            elif 'mac' in api :
                file =  self.pfile_mac
            elif 'enb' in api :
                file =  self.pfile_enb
            
            try:
                with open(file) as data_file:
                    self.stats_data = json.load(data_file)
                    self.status='connected'
            except :
                self.status='disconnected'
                self.log.error('cannot find the output file'  + file )       

        elif self.op_mode == 'sdk' :

            if 'all' in api :
                url = self.url+self.sm_all_api
            elif 'mac' in api :
                url = self.url+self.sm_mac_api
            elif 'enb' in api :
                url = self.url+self.sm_enb_api
            
            
            self.log.info('the request url is: ' + url)
            try :
                req = requests.get(url)
                if req.status_code == 200:
                    self.stats_data = req.json()
                    self.status='connected'
                else :
                    self.status='disconnected'
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Request url ' + url + ' failed')
            
        else :
            self.log.warn('Unknown operation mode ' + op_mode )
            
        if self.status == 'connected' :     
            self.log.debug('Stats Manager requested data')
            self.log.debug(json.dumps(self.stats_data, indent=2))
                
    def get_enb_config(self,enb=0):
        """!@brief Get the entire eNB configuration
        
        @param enb: index of eNB
        """
        return self.stats_data['eNB_config'][enb]

    def get_num_enb(self):
        """!@brief Get the number of connected eNB to this controller 
        
        """

        return len(self.stats_data['eNB_config'])

    def get_ue_config(self,enb=0,ue=0):
        """!@brief Get the UE specific configuration
        
        @param enb: index of eNB
        @param ue: index of UE
        """
        return self.stats_data['eNB_config'][enb]['UE']['ueConfig'][ue]

    def get_cell_config(self,enb=0,cc=0):
        """!@brief Get the Cell-specific configuration
        
        @param enb: index of eNB
        @param cc: index of component carrier
        """
        return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]

    def get_cell_rb(self,enb=0,cc=0, dir='dl'):
        """!@brief Get the eNB total available resource blocks in a given direction
        
        @param enb: index of eNB
        @param cc: index of component carrier
        @param dir: defines downlink and uplink direction
        """
        if dir == 'dl' or dir == 'DL' :
            return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['dlBandwidth']
        elif dir == 'ul' or dir == 'UL' :
            return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['ulBandwidth']
        else :
            self.log.warning('unknown direction ' + dir + 'set to DL')
            return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['dlBandwidth']

    def get_cell_bw(self,enb=0,cc=0, dir='dl'):
        """!@brief Get the cell frequency bandwidth for a given direction
        
        @param enb: index of eNB
        @param cc: index of component carrier
        @param dir: defines downlink and uplink direction
        """
        rb=self.get_cell_rb(enb,cc,dir)
        if rb == 6 :
            return 1.4
        elif rb == 25 :
            return 5
        elif rb == 50 :
            return 10
        elif rb == 75 :
            return 15
        elif rb == 100 :
            return 20

    def get_cell_freq(self,enb=0,cc=0, dir='dl'):
        """!@brief Get the cell current operating frequency
        
        @param enb: index of eNB
        @param cc: index of component carrier
        @param dir: defines downlink and uplink direction
        """
        if dir == 'dl' or dir == 'DL' :
            return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['dlFreq']
        elif dir == 'ul' or dir == 'UL' :
            return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['ulFreq']
        else :
            self.log.warning('unknown direction ' + dir + 'set to DL')
            return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['dlFreq']

    def get_cell_power(self,enb=0,cc=0, dir='dl'):
        """!@brief Get the current cell operating power
        
        @param enb: index of eNB
        @param cc: index of component carrier
        @param dir: defines downlink and uplink direction
        """

        if dir == 'dl' or dir == 'DL' :
            return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['dlPdschPower']
        elif dir == 'ul' or dir == 'UL' :
            return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['ulPuschPower']
        else :
            self.log.warning('unknown direction ' + dir + 'set to DL')
            return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['dlPdschPower']

    def get_cell_band(self,enb=0,cc=0):
        """!@brief Get the current cell frequency band
        
        @param enb: index of eNB
        @param cc: index of component carrier
        """
        return self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['eutraBand']
               
    def get_cell_maxmcs(self,enb=0,cc=0, dir='dl'):
        """!@brief Get the maximum supported MCS by this eNB
        
        @param enb: index of eNB
        @param cc: index of component carrier
        @param dir: defines downlink and uplink direction
        """
        
        if dir == 'dl' or dir == 'DL' :
            return 28
        elif self.stats_data['eNB_config'][enb]['eNB']['cellConfig'][cc]['enable64QAM'] == 0 :
            return 16
        else :
            return 28
    
    def get_lc_config(self,enb=0,lc=0):
        """!@brief Get a logical channel (LC) config for a given eNB and LC id
        
        @param enb: index of eNB
        @param lc: logical channel id
        """
        return self.stats_data['eNB_config'][enb]['LC']['lcUeConfig'][lc]      

    # mac_stats needs to be changed to ue_status
    def get_ue_status(self,enb=0,ue=0):
        """!@brief Get the full UE status 
        
        @param enb: index of eNB
        @param ue: index of UE
        """

        return self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]

    def get_num_ue(self,enb=0):
        """!@brief Get the total number of attached UE to a given eNB
        
        @param enb: index of eNB
        """

        return len(self.stats_data['mac_stats'][enb]['ue_mac_stats'])

    def get_ue_mac_status(self,enb=0,ue=0):
        """!@brief Get the UE MAC layer status 
        
        @param enb: index of eNB
        @param ue: index of UE
        """
        return self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']

    def get_ue_phr(self,enb=0,ue=0):
        """!@brief Get the current UE power headroom
        
        @param enb: index of eNB
        @param ue: index of UE
        """
        return self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['phr']
    # return for all LCIDs
    def get_ue_rlc_report(self,enb=0,ue=0):
        """!@brief Get the current UE RLC layer buffer report 
        
        @param enb: index of eNB
        @param ue: index of UE
        """

        return self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['rlcReport']

    def get_num_ue_lc(self,enb=0,ue=0):
        """!@brief Get the number of configured/active UE logical channels for a given eNB
        
        @param enb: index of eNB
        @param ue: index of UE
        """

        return len(self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['rlcReport'])

    def get_ue_lc_report(self,enb=0,ue=0,lc=0):
        """!@brief Get the UE RLC report for a particular logical channel
        
        @param enb: index of eNB
        @param ue: index of UE
        @param lc: logical channel id
        """

        return self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['rlcReport'][lc]

    def get_ue_dlcqi_report(self,enb=0,ue=0):
        """!@brief Get the UE downlink channel quality indicator (CQI) report
        
        @param enb: index of eNB
        @param ue: index of UE
        """

        return self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['dlCqiReport']
   
    def get_ue_dlwbcqi(self,enb=0,ue=0,cc=0):
        """!@brief Get the UE downlink channel quality indicator for a patricular eNB and CC
        
        @param enb: index of eNB
        @param ue: index of UE
        @param cc: index of component carrier
        """

        return self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['dlCqiReport']['csiReport'][cc]['p10csi']['wbCqi']

    # lcgdi 0 for SRBs, lcgid 1 for default drb
    def get_ue_bsr(self,enb=0,ue=0, lc=0):
        """!@brief Get the UE buffer status report for a particular logical channel 
        
        @param enb: index of eNB
        @param ue: index of UE
        @param lc: logical channel id
        """

        if lc == 0 or lc == 1:
            return self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['bsr'][0]
        elif lc == 2 :
            aggregated_bsr= self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['bsr'][1]+self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['bsr'][2]+self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['bsr'][3]
            return aggregated_bsr
        else :
            return 0

    def get_ue_harq(self,enb=0,ue=0):
        """!@brief Get the UE HARQ status for different PID
        
        @param enb: index of eNB
        @param ue: index of UE
        """
        return self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['harq']

    # don't need UE
    def get_enb_sfn(self,enb=0,ue=0):
        """!@brief Get eNB system frame number (SFN)
        
        @param enb: index of eNB
        @param ue: index of UE
        """
        
	if self.get_num_ue(enb) > 0 :
            return self.stats_data['mac_stats'][enb]['ue_mac_stats'][ue]['mac_stats']['dlCqiReport']['sfnSn']
   	else:
            return 0 
   
class ss_policy (object):
    """!@brief Spectrum sharing class
        
        This class provides emulated spectrum sharing polices (general, operator, and LSA), rules, and sensing data. 
    @note: This class can implements interfaces to remote database and retrive and make available all the required information to the network control apps.
    """
    general_policy = []
    operator_policy = []
    lsa_policy = []
    rules = []
    sensing_data = []
    
    general_policy_file='inputs/general_policy.yaml'
    operator_policy_file='inputs/operator_policy.yaml'
    lsa_policy_file='inputs/lsa_policy.yaml'
    rules_file='inputs/rules.yaml'
    sensing_data_file='inputs/sensing_data.yaml'
    
    def __init__(self, log, url='http://localhost', port='9999', op_mode='test'):
        super(ss_policy, self).__init__()
        
        self.url = url+':'+port
        self.status = 0
        self.op_mode = op_mode
        self.log = log
        # NB APIs endpoints
        self.rrm_api=flexran_rest_api.rrm
        self.rrm_policy_api=flexran_rest_api.rrm_policy
        # stats manager data requeted by the endpoint
        # could be extended to have data per API endpoint
        self.policy_data = ''



    def load_policy(self):
        """!@brief load general and operator-specific policies"""
        file = open(self.general_policy_file,'r')
        self.general_policy = yaml.load(file)
        self.log.debug('Loaded: general policy file [yaml] :')
        self.log.debug(yaml.dump(self.general_policy))

        file = open(self.operator_policy_file,'r')
        self.operator_policy = yaml.load(file)
        self.log.debug('Loaded: operator policy file [yaml] :')
        self.log.debug(yaml.dump(self.operator_policy))

        file = open(self.lsa_policy_file,'r')
        self.lsa_policy = yaml.load(file)
        self.log.debug('Loaded: lsa policy file [yaml] :')
        self.log.debug(yaml.dump(self.lsa_policy))

    def load_rules(self):
        """!@brief load spectrun selection rules"""
        file = open(self.rules_file,'r')
        self.rules = yaml.load(file)
        self.log.debug('Loaded: rules file [yaml] :')
        self.log.debug(yaml.dump(self.rules))

    def load_sensing_data(self):
        """!@brief load sensing data"""
        file = open(self.sensing_data_file,'r')
        self.sensing_data = yaml.load(file)
        self.log.debug('Loaded: sensing data file [yaml] :')
        self.log.debug(yaml.dump(self.sensing_data))

    def load_config_files(self):
        """!@brief load all the information (knowledge base) """
        self.load_rules()
        self.load_sensing_data()
        self.load_policy()

    def get_sensing_data(self):
        """!@brief return the sensing data """
        return self.sensing_data
    def get_rules(self):
        """!@brief return the rule for spectrun selection """
        return self.rules
    def get_lsa_policy(self):
        """!@brief return the available LSA policy """
        return self.lsa_policy
    def get_operator_policy(self):
        """!@brief return the operator-specific policy """
        return self.operator_policy
    def get_general_policy(self):
        """!@brief return the general spectrum sharing policy """
        return self.general_policy

    # apply policy with policy data 
    # TBD: apply policy from a file
    def apply_policy(self, policy_data='',as_payload=True):
        """!@brief Apply the default or user-defined policy 
        
        @param policy_data: content of the policy file
        @param as_payload: embed the applied policy as a payload
        @note: this method is the same as in RRM class.
        """
        self.status=''

        if policy_data != '' :
            pdata=policy_data
        elif self.policy_data != '' :
            pdata=self.policy_data 
        else:
            self.log.error('cannot find the policy data '  + pdata)
            return
	
        if as_payload == True :
            url = self.url+self.rrm_policy_api
        else: 
            url = self.url+self.rrm_api+'/'+flexran_rest_api.pf_name
        
        if self.op_mode == 'test' :
            self.log.info('POST ' + str(url))
            self.log.debug(self.dump_policy(policy_data=pdata))
            self.status='connected'
            
        elif self.op_mode == 'sdk' :
            print self.dump_policy(pdata)
            try :
		# post data as binary
            	req = requests.post(url, data=self.dump_policy(pdata),headers={'Content-Type': 'application/octet-stream'})
            	if req.status_code == 200:
            	    self.log.info('successfully applied the policy')
            	    self.status='connected'
            	else :
            	    self.status='disconnected'
            	    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to apply the policy ' )
            
        else :
            self.log.warn('Unknown operation mode ' + op_mode )
	    self.status='unknown'
        return self.status 

    def dump_policy(self, policy_data=''):
        """!@brief return the content of the policy in ymal format
        
        @param policy_data: content of the policy file
        """
        if policy_data != '' :
            return yaml.dump(policy_data, default_flow_style=False, default_style='"')
        elif self.policy_data != '' :
            return yaml.dump(self.policy_data, default_flow_style=False, default_style='"')
        else:
            self.log.error('cannot find the policy data ' + policy_data)
            return
   
