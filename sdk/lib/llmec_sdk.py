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
    File name: llmec_sdk.py
    Author: navid nikaein
    Description: Library to get and set accessible paramters and operation through the llmec
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
import yaml

from lib.logger import *


class llmec_rest_api(object):
    """!@brief LLMEC supported REST APIs endpoints

    """
 
    """!@brief flow status API endpoint"""
    fs_all='inputs/flow_stats.json'
    
    """!@brief Input data sets for all the status used for test"""
    bs_all='inputs/bearer_stats.json'
    

    """!@brief add/get/remove a ue bearer API endpoint"""
    # APIs : bearer is the smallest unit 
    bearer='/bearer'

    """!@brief get/remove ue bearer context by internal llmec id API endpoint"""
    ue_bearer_by_mecid='/bearer/id'
    """!@brief get/remove ue bearer context API endpoint"""
    ue_bearer='/bearer/imsi_bearer'
    
    """!@brief redirect ue bearer  by llmec internal id context API endpoint"""
    redirect_ue_bearer_by_mecid='/bearer/redirect'
    """!@brief redirect ue bearer context API endpoint"""
    redirect_ue_bearer='/bearer/redirect/imsi_bearer'
    
    
    flow_flush='/flow/flush'

    flow_stats='/stats'

class bearer_manager(object):
    def __init__(self, log, url='http://localhost', port='9999', op_mode='test'):
        super(bearer_manager, self).__init__()
        
        self.url = url+':'+port
        self.status = ''
        self.op_mode = op_mode
        self.log = log
        self.stats_data = ''
        self.bs_file = llmec_rest_api.bs_all

        
        self.ue_bearer_context=''
        self.bearer_context=''

        self.bearer_api=llmec_rest_api.bearer

        self.ue_bearer_by_mecid_api=llmec_rest_api.ue_bearer_by_mecid
        self.ue_bearer_api=llmec_rest_api.ue_bearer

        self.redirect_ue_bearer_by_mecid_api=llmec_rest_api.redirect_ue_bearer_by_mecid
        self.redirect_ue_bearer_api=llmec_rest_api.redirect_ue_bearer
     
       
       
    # data: {"eps_bearer_id":1, "imsi":"208950000000009", "s1_ul_teid":"0x3", "s1_dl_teid":"0x4", "slice_id":"0x1", "ue_ip":"172.16.0.2", "enb_ip":"192.168.0.3"}

    def add_ue_bearer_rule(self, imsi='208950000000001',eps_drb=0x1, slice_id=0x1, ul_teid='0x1', dl_teid='0x8d3ded37',ue_ip='172.16.0.2',enb_ip='192.168.12.79'):

        url = self.url+self.bearer_api 
        data= {'eps_bearer_id':eps_drb, 'slice_id':slice_id, 'imsi':imsi,  's1_ul_teid': ul_teid, 's1_dl_teid' : dl_teid, 'ue_ip': ue_ip, 'enb_ip' : enb_ip}
        status='disconnected'
        
        if self.op_mode == 'test' :
            self.log.info('POST ' + str(url))
            self.log.info('Data ' + str(data))
            status='connected'
        elif self.op_mode == 'sdk' : 
            try :
                self.log.debug('POST ' + str(url))
                self.log.debug('Data ' + str(data))
                req = requests.post(url,json.dumps(data),headers={'Content-Type': 'application/x-www-form-urlencoded'})
                if req.status_code == 200 :
                    self.log.debug('successfully added a UE specific rule' )
                    status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to add a UE specific rule' )

        else :
            self.log.warn('Unknown operation mode ' + op_mode )
            
            
        return status

    def get_ue_bearer_context_by_mecid(self, mec_id=1):

        url = self.url+self.ue_bearer_by_mecid_api+'/'+str(mec_id)
        status='disconnected'
      
        if self.op_mode == 'test' :
            self.log.info('GET ' + str(url))
            status='connected'
        elif self.op_mode == 'sdk' :
            try :
                self.log.debug('GET ' + str(url))
                req = requests.get(url)
                if req.status_code == 200 :
                    self.ue_bearer_context = req.json()
                    self.log.debug('successfully got the ue bearer context ' )
                    status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to get ue bearer context' )

        else :
            self.log.warn('Unknown operation mode ' + op_mode )
            
        if status == 'connected' :
            self.log.debug(json.dumps(self.ue_bearer_context, indent=2))

        return status 
            
    def get_ue_bearer_context(self, imsi='208950000000001',eps_drb='0x1'):

        url = self.url+self.ue_bearer_api+'/'+imsi+','+eps_drb
        status='disconnected'
      
        if self.op_mode == 'test' :
            self.log.info('GET ' + str(url))
            for index in range(0, len(self.bearer_context)):
                if (self.bearer_context[index]['imsi'] == imsi) and self.bearer_context[index]['eps_bearer_id'] == eps_drb:
                    return self.bearer_context[index]
            status='connected'
        elif self.op_mode == 'sdk' :
            try :
                self.log.debug('GET ' + str(url))
                req = requests.get(url)
                if req.status_code == 200 :
                    self.ue_bearer_context = req.json()
                    self.log.debug('successfully got the ue bearer context ' )
                    self.status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to get ue bearer context' )
                
        else :
            self.log.warn('Unknown operation mode ' + op_mode )

        if status == 'connected' :
            self.log.debug(json.dumps(self.ue_bearer_context, indent=2))

        return status
    
    def get_all_bearer_context(self):

        url = self.url+self.bearer_api
        status='disconnected'
      
        if self.op_mode == 'test' :
            self.log.info('GET ' + str(url))
            with open(self.bs_file, "r") as data_file:
                self.bearer_context = json.load(data_file)                
                data_file.close()                
            status='connected'
        elif self.op_mode == 'sdk' :
            try :
                self.log.debug('GET ' + str(url))
                req = requests.get(url)
                if req.status_code == 200 :
                    self.bearer_context = req.json()
                    self.log.debug('successfully got the all bearer context ' )
                    status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to all bearer context' )

        else :
            self.log.warn('Unknown operation mode ' + op_mode )

        if status == 'connected' :
            self.log.debug(json.dumps(self.bearer_context, indent=2))

        return status
    
    def get_num_ues(self):
        return len(self.bearer_context)
    
    def get_num_bearers(self):
        return len(self.bearer_context)*2
    
    def redirect_ue_bearer_rule_by_mec_id(self, mec_id, remote_ip='172.16.0.2',mec_ip='192.168.12.79'):
        """!@brief redirect ue bearer from a remote server to a local server 
     
      
        @param from_ip: the ip address of the remote server 
        @param to_ip: the ip address of the local MEC server
        @param id: id associated with (ue,eps bearer)
        """
        url = self.url+self.redirect_ue_bearer_by_mecid_api+'/'+str(mec_id) 
        data= {'from':remote_ip, 'to': mec_ip}
        status='disconnected'
        
        if self.op_mode == 'test' :
            self.log.info('POST ' + str(url))
            self.log.info('Data ' + str(data))
            status='connected'
        elif self.op_mode == 'sdk' : 
            try :
                self.log.debug('POST ' + str(url))
                self.log.debug('Data ' + str(data))
               
                req = requests.post(url,json.dumps(data),headers={'Content-Type': 'application/x-www-form-urlencoded'})
                if req.status_code == 200 :
                    self.log.error('successfully redirected the UE bearer' )
                    status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to redirect a UE bearer associated to id ' + str(id))

        else :
            self.log.warn('Unknown operation mode ' + op_mode )

        return status
    
    def redirect_ue_bearer_rule(self, imsi='208950000000001',eps_drb='0x1', remote_ip='172.16.0.2',mec_ip='192.168.12.79'):
        """!@brief redirect ue bearer from a remote server to a local server 
     
      
        @param from_ip: the ip address of the remote server 
        @param to_ip: the ip address of the local MEC server
        @param id: id associated with (ue,eps bearer)
        """
        url = self.url+self.redirect_ue_bearer_api+'/'+imsi+','+eps_drb
        data= {'from':remote_ip, 'to': mec_ip}
        status='disconnected'
        
        if self.op_mode == 'test' :
            self.log.info('POST ' + str(url))
            self.log.info('Data ' + str(data))
            status='connected'
        elif self.op_mode == 'sdk' : 
            try :
                self.log.debug('POST ' + str(url))
                self.log.debug('Data ' + str(data))
               
                req = requests.post(url,json.dumps(data),headers={'Content-Type': 'application/x-www-form-urlencoded'})
                if req.status_code == 200 :
                    self.log.debug('successfully redirected the UE bearer' )
                    status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to redirect a UE bearer associated to id ' + str(id))

        else :
            self.log.warn('Unknown operation mode ' + op_mode )
            
        return status
    
    def remove_ue_bearer_by_id(self, mec_id):

        if mec_id > 0 :
            url = self.url+self.ue_bearer_by_mecid_api+'/'+str(mec_id)
            msg = 'deleting ue bearer assocaited with mec id ' + str(mec_id)
        else:
            url = self.url+self.ue_bearer_api
            msg = 'deleting all ue bearers'
        status='disconnected'
        
        if self.op_mode == 'test' :
            self.log.info('DELETE ' + str(url))
            self.log.info(msg)
            status='connected'
            
        elif self.op_mode == 'sdk' : 
            try :
                self.log.debug('DELETE ' + str(url))
                req = requests.delete(url)
                if req.status_code == 200 :
                    self.log.debug('successfully deleted beare(s)' )
                    status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to delete bearer(s)' )

        else :
            self.log.warn('Unknown operation mode ' + op_mode )

        return status 

    def remove_all_bearers(self):
        self.remove_ue_bearer_by_id(self,0)

    def remove_ue_bearer(self, imsi='208950000000001',eps_drb='0x1') :

        url = self.url+self.ue_bearer_api+'/'+imsi+','+eps_drb
        status='disconnected'   
        if self.op_mode == 'test' :
            self.log.info('DELETE ' + str(url))
            status='connected'
        elif self.op_mode == 'sdk' : 
            try :
                self.log.debug('DELETE ' + str(url))
                req = requests.delete(url)
                if req.status_code == 200 :
                    self.log.debug('successfully deleted U Ebeare(s)' )
                    status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to delete U Ebearer(s)' )
                
        else :
            self.log.warn('Unknown operation mode ' + op_mode )
            
        return status 

    def remove_redirected_ue_bearer_by_mecid(self, mec_id=1):

        url = self.url+self.redirect_ue_bearer_by_mecid_api+'/'+str(mec_id)
        status='disconnected'          
        if self.op_mode == 'test' :
            self.log.info('DELETE ' + str(url))
            status='connected'
            
        elif self.op_mode == 'sdk' : 
            try :
                self.log.debug('DELETE ' + str(url))
                req = requests.delete(url)
                if req.status_code == 200 :
                    self.log.debug('successfully deleted UE redirect bearer(s)' )
                    status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to delete UE redirect bearer(s)' )

        else :
            self.log.warn('Unknown operation mode ' + op_mode )

        return status 

    def remove_redirected_ue_bearer(self, imsi='208950000000001',eps_drb='0x1'):

        url = self.url+self.redirect_ue_bearer_api+'/'+imsi+','+eps_drb
        status='disconnected'             
        if self.op_mode == 'test' :
            self.log.info('DELETE ' + str(url))
            status='connected'       
        elif self.op_mode == 'sdk' : 
            try :
                self.log.debug('DELETE ' + str(url))
                req = requests.delete(url)
                if req.status_code == 200 :
                    self.log.debug('successfully deleted UE redirect bearer(s)' )
                    status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to delete UE redirect bearer(s)' )

        else :
            self.log.warn('Unknown operation mode ' + op_mode )
            
        return status
     
    #begin TTN
    def redirect_all_ue_bearers_belong_to_sliceid(self, imsi='208950000000001',slice_id=0, from_ip='172.16.0.2',to_ip='192.168.12.79'):
        """!@brief redirect all  ue bearers beloging to a slice from a remote/local server to a local/remote server 
     
        @param from_ip: the ip address of the server from which all the flows will be redirected
        @param to_ip: the ip address of the server to which all the flows will be redirected
        @param imsi: imsi
        @param slice_id: slice id               
        """
        status='disconnected'
        for index in range(0, len(self.bearer_context)):
            if (self.bearer_context[index]['imsi'] == imsi) and (int(self.bearer_context[index]['slice_id']) == slice_id):
                eps_drb = self.bearer_context[index]['eps_bearer_id']      
                url = self.url+self.redirect_ue_bearer_api+'/'+imsi+','+str(eps_drb)
                data= {'from':from_ip, 'to': to_ip}                
        
                if self.op_mode == 'test' :
                    self.log.info('POST ' + str(url))
                    self.log.info('Data ' + str(data))
                    status='connected'
                elif self.op_mode == 'sdk' : 
                    try :
                        self.log.debug('POST ' + str(url))
                        self.log.debug('Data ' + str(data))
               
                        req = requests.post(url,json.dumps(data),headers={'Content-Type': 'application/x-www-form-urlencoded'})
                        if req.status_code == 200 :
                            self.log.debug('successfully redirected the UE bearer' )
                            status='connected'
                        else :
                            self.log.error('Request error code : ' + req.status_code)
                    except :
                        self.log.error('Failed to redirect a UE bearer associated to slice id ' + str(slice_id))
                else :
                    self.log.warn('Unknown operation mode ' + op_mode )
            
                #return status
        return status    
            
    def redirect_ue_bearer_belong_to_sliceid(self, imsi='208950000000001',eps_drb=1, slice_id=0, from_ip='172.16.0.2',to_ip='192.168.12.79'):
        """!@brief redirect ue bearer from a remote server to a local server 
     
        @param from_ip: the ip address of the server from which all the flows will be redirected
        @param to_ip: the ip address of the server to which all the flows will be redirected
        @param imsi: imsi
        @param slice_id: slice id
                       
        """
        status='disconnected'
        for index in range(0, len(self.bearer_context)):
            if (self.bearer_context[index]['imsi'] == imsi) and (int(self.bearer_context[index]['slice_id']) == slice_id) and (int(self.bearer_context[index]['eps_bearer_id']) == eps_drb):
                url = self.url+self.redirect_ue_bearer_api+'/'+imsi+','+str(eps_drb)
                data= {'from':from_ip, 'to': to_ip}
        
                if self.op_mode == 'test' :
                    self.log.info('POST ' + str(url))
                    self.log.info('Data ' + str(data))
                    status='connected'
                elif self.op_mode == 'sdk' : 
                    try :
                        self.log.debug('POST ' + str(url))
                        self.log.debug('Data ' + str(data))
               
                        req = requests.post(url,json.dumps(data),headers={'Content-Type': 'application/x-www-form-urlencoded'})
                        if req.status_code == 200 :
                            self.log.debug('successfully redirected the UE bearer' )
                            status='connected'
                        else :
                            self.log.error('Request error code : ' + req.status_code)
                    except :
                        self.log.error('Failed to redirect a UE bearer associated to slice id ' + str(slice_id))

                else :
                    self.log.warn('Unknown operation mode ' + op_mode )
            
                return status
        return status 
    #end TTN

class flow_manager(object):
    def __init__(self, log, url='http://localhost', port='9999', op_mode='test'):
        super(flow_manager, self).__init__()

        self.url = url+':'+port
        self.status = ''
        self.op_mode = op_mode
        self.log = log
        self.stats_data = ''

        self.flow_flush=llmec_rest_api.flow_flush
        self.flow_stats=llmec_rest_api.flow_stats
       
        self.fs_file = llmec_rest_api.fs_all
 
          
 
    def flow_status(self):
       
        url = self.url+self.flow_stats
        status='disconnected'     
        self.log.debug('GET ' + str(url))
        
        file = ''

        if self.op_mode == 'test' :
            
            file =  self.fs_file
            #file = '/home/voiture/store/sdk/inputs/flow_stats_1.json'

        
            try:
                with open(file, "r+") as data_file:
                    self.stats_data = json.load(data_file)
                    self.status='connected'
                    print self.stats_data
                    data_file.close()
            except :
                self.log.error('[THINH] cannot find the output file '  + file )       


        elif self.op_mode == 'sdk' : 
            try :
                req = requests.get(url)
                if req.status_code == 200 :
                    self.stats_data = req.json()
                    self.log.debug('successfully got the flow status ' )
                    status='connected'
                else :
                    self.log.error('Request error code : ' + req.status_code)
            except :
                self.log.error('Failed to get the flow status' )

        else :
            self.log.warn('Unknown operation mode ' + op_mode )                 

        if status == 'connected' :     
            self.log.debug('Flow Stats Manager requested data')
            self.log.debug(json.dumps(self.stats_data, indent=2))

            
    def get_num_rules(self):
        return len(self.stats_data)
        
    def get_num_ues(self):
        return self.get_num_rules()

    def get_num_bytes(self, ue_id=0, dir='ul'):
        index=0
        flow_dir='upstream'
        if dir == 'dl' or dir == 'DL' :
            flow_dir='downstream'

        self.log.info('UE id ' + str(ue_id) + ' : ' + flow_dir + ' byte count: ' + str(self.stats_data[index][dir]['byte_count']))    

        return self.stats_data[index][dir]['byte_count']

    def get_num_packets(self, ue_id=0, dir='ul'):
        index=0
        flow_dir='upstream'
        if dir == 'dl' or dir == 'DL' :
            flow_dir='downstream'
            
        self.log.info('UE id ' + str(ue_id) + ' : ' + flow_dir + ' packet count: ' + str(self.stats_data[index][dir]['packet_count']))    
        return self.stats_data[index][dir]['packet_count']

    def get_flow_life_time(self, ue_id=0, dir='ul'):
        index=0
        flow_dir='upstream'
        if dir == 'dl' or dir == 'DL' :
            flow_dir='downstream'
            
        self.log.info('UE id ' + str(ue_id) + ' : ' + flow_dir + ' flow lifetime: ' + str(self.stats_data[index][dir]['duration_sec']))    
        return self.stats_data[index][dir]['duration_sec']

    def get_flow_priority(self, ue_id=0, dir='ul'):
        index=0
        flow_dir='upstream'
        if dir == 'dl' or dir == 'DL' :
            flow_dir='downstream'

        self.log.info('UE id ' + str(ue_id) + ' : ' + flow_dir + ' flow priority: ' + str(self.stats_data[index][dir]['priority']))    
        return self.stats_data[index][dir]['priority']

    def get_flow_table_id(self, ue_id=0, dir='ul'):
        index=0
        flow_dir='upstream'
        if dir == 'dl' or dir == 'DL' :
            flow_dir='downstream'

        self.log.info('UE id ' + str(ue_id) + ' : ' + flow_dir + ' flow table id: ' + str(self.stats_data[index][dir]['flow_table_id']))    
        return self.stats_data[index][dir]['flow_table_id']


