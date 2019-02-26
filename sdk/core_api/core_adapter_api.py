import datetime
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

from connexion import NoContent
from array import *
from threading import Timer
from time import sleep

from lib import llmec_sdk 
from lib import logger

import urllib2
import urllib

CPSR_REGISTRATION_INTERVAL=10 

core_adapter_routes = {
  "userEqId": "208950000000009",
  "routes": [
      {"FromServer": "192.168.12.1", "ToServer": "192.168.12.2"} 
   ]
}


class adapter(object):
    #for FlexRAN
    url = ''
    port = ''
    op_mode = ''
    log_level = ''     
    cpsr_url = ''
    log = None

def update_instance_info(cpsStatus='', cpsInstanceId='', slicenetId='', serviceInstanceId='', load=0, capacity=0):
    """!@brief update_instance_info update instance info into a json file when necessary
    """
        
    #read JSON file
    with open('./inputs/core_adapter_cpsr.json', "+r") as data_file:
        data = json.load(data_file)
        data_file.close()
        
    #Update the data
    if (cpsStatus != ''):
        data["cpsStatus"] = cpsStatus  
    if (cpsInstanceId != ''):
        data["cpsInstanceId"] = cpsInstanceId
    if (slicenetId != ''):
        data["slicenetId"] = slicenetId
    if (serviceInstanceId != ''):
        data["serviceInstanceId"] = serviceInstanceId
    if (load != 0):
        data["load"] = load        
    if (capacity != 0):
        data["capacity"] = capacity                 
                      
    #write the update information to the file
    with open('./inputs/core_adapter_cpsr.json', "w") as data_file:
        #json.dump(data,data_file)
        data_file.write(json.dumps(data))
        data_file.close()
        
        
def cpsr_register():
    """!@brief Register the Adpater with a NRF (e.g., CPSR) 
       TODO: should be updated to deal with the situation in which registration procedure is failed at the first time
    """
    status = 0                
    # Read JSON file
    with open('./inputs/core_adapter_cpsr.json') as data_file:
        data = json.load(data_file)
        data_file.close()
    #print(data)
       
    jsondata = json.dumps(data)
    #jsondata = json.dumps(body)
    #print(jsondata)        
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
        
    method = "PUT"
    handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(handler)
    request = urllib2.Request(adapter.cpsr_url, data=jsondataasbytes)
    request.get_method = lambda: method
    request.add_header("content-Type", 'application/json')
        
    try:
        response = opener.open(request)
    except (urllib2.HTTPError, urllib2.URLError)  as e:
        adapter.log.info('[CPSR_Register]' + str(e)) 
            
    else:
        # process the response
        res_body = response.read().decode("utf-8")
        adapter.log.info("[CPSR_Register] Status: " + str(response.code))
        status = int(response.code)
        
    if (status == 201):
        #print(res_body)
        jsondata = json.loads(res_body)
        adapter.log.info("[CPSR_Register] HeartbeatTimer: " + str(jsondata["heartbeatTimer"]))
        adapter.heartbeat_timer = jsondata["heartbeatTimer"]
        t = Timer(adapter.heartbeat_timer, cpsr_update,()).start() 
    else:
        #for the moment,try registratin after 10s
        t = Timer(CPSR_REGISTRATION_INTERVAL, cpsr_register,()).start()        
           
def cpsr_update():
    """!@brief Update the Adpater with a NRF (e.g., CPSR) 
    """
    status = 0                
    # Read JSON file
    with open('./inputs/core_adapter_cpsr_update.json') as data_file:
        data = json.load(data_file)
        data_file.close()
    #print(data)
       
    jsondata = json.dumps(data)
    #jsondata = json.dumps(body)
    #print(jsondata)        
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
        
    method = "PATCH"
    handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(handler)
    request = urllib2.Request(adapter.cpsr_url, data=jsondataasbytes)
    request.get_method = lambda: method
    request.add_header("content-Type", 'application/json')
        
    try:
        response = opener.open(request)
    except urllib2.URLError as e:
        adapter.log.info('[CPSR_Update] ' + str(e.args))
        #TODO: should try to register after ... seconds
        
    except urllib2.HTTPError as e:
        adapter.log.info('[CPSR_Update] ERROR: ' + str(e))
        if (e.code == 404):
            adapter.log.info("[CPSR_Update] Send register ... ")
            cpsr_register()
            
    else:
        # process the response
        res_body = response.read().decode("utf-8")
        adapter.log.info("[CPSR_Update] Status: " + str(response.code))
        status = int(response.code)            
    
    #if ok, continue updating when the heartbeat_timer expires   
    if (status == 200):  
        #print(res_body)
        adapter.log.info("[CPSR_Update] Status: " + str(status))
        adapter.log.info("[CPSR_Update] Send update afer " + str(adapter.heartbeat_timer) + ' seconds')
        jsondata = json.loads(res_body)              
        #update the information if necessary
        #update_instance_info()    
        t = Timer(adapter.heartbeat_timer, cpsr_update,()).start()
    if (status == 400): #resend   
        #print(res_body)
        adapter.log.info("[CPSR_Update] Status: " + str(status))
        adapter.log.info("[CPSR_Update] Send update afer " + str(adapter.heartbeat_timer) + ' seconds')
        jsondata = json.loads(res_body)              
        #update the information if necessary
        #update_instance_info()    
        t = Timer(adapter.heartbeat_timer, cpsr_update,()).start()
        
    #if there's no information
    elif (status == 404): 
        cpsr_register()  
                
def init():
    """!@brief init Parse the command args and store in the appropriate variables
    """
    
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
    parser.add_argument('--cpsr-url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost', 
                        help='set the CPSR URL: loalhost (default)')
    
    #parse the arguments and store in the appropriate variables
    args = parser.parse_args()        
    adapter.url = args.url
    adapter.port = args.port
    adapter.op_mode = args.op_mode
    adapter.log_level = args.log    
    adapter.cpsr_url = args.cpsr_url 
    adapter.log = llmec_sdk.logger(log_level=adapter.log_level).init_logger()         
                   
                        
def put_QoSOnCore(sliceId, userEqId, body, epsBearerId=-1):
    """!@brief Set QoS contraints to the corresponding network slice in the core network
        @param sliceId: Id of the slice instance
        @param userEqId: IMSI
        @param epsBearerId: eps bearer id
        @param body: body of "PUT" message 
    """
    
    post_QoSOnCore(sliceId, userEqId, body, epsBearerId)
            
     
def post_QoSOnCore(sliceId, userEqId, body, epsBearerId=-1):
    """!@brief Add QoS contraints to the corresponding network slice in the core network
        @param sliceId: Id of the slice
        @param userEqId: IMSI
        @param epsBearerId: eps bearer id
        @param body: body of post message including the parameters bandIncDir, bandIncVal and bandUnitScale
    """

    """
    Step 0: get information from the request and verify the input
    """
    dir = {}    
    band_inc_val = 0.0
    band_unit_scale = ''

    #verify the input
    num_request = len(body)
    if (num_request > 2):
        print ('Bad request!')
        return NoContent, 400    

    for req in range (0, num_request):
        try:
            direction = body[req]['bandIncDir']
            band_inc_val = float(body[req]['bandIncVal'])    
            band_unit_scale = body[req]['bandUnitScale']  
        except (ValueError, KeyError):
            print ('Bad request!')
            return NoContent, 400          
        if  direction == 'dl' or direction == 'DL':
            dir[req] = 'dl'
        elif direction == 'ul' or direction == 'UL':
            dir[req] = 'ul'                            
 
    if num_request == 2:
        if dir[0] == dir[1]:
            print('Bad request!')
            return NoContent, 400
        
    """
    Step 1: get slice_config info from a configuration file
    """   
    
    #read slice_configuration file
    with open('./inputs/slice_config.json', "r") as data_file:
        slice_config = json.load(data_file)
        data_file.close()
        
    #get slice config information 
    #if slice_id doesn't exist -> get from the first slice
    remote_ip = slice_config[0]['remote_ip']
    local_ip = slice_config[0]['local_ip']
    for index in range(0, len(slice_config)):
        if (slice_config[index]['id'] == sliceId):
            remote_ip = slice_config[index]['remote_ip']
            local_ip = slice_config[index]['local_ip']            
    
    """
    Redirect Direction
    for the moment, based on the first request only
    if bandIncVal > 0 -> from remote to local
       else from local to remote       
    """ 
    redirect_dir_to = 'remote'
    if float(body[0]['bandIncVal']) > 0:
        redirect_dir_to = 'local'    
            
    print('Received request for imsi ' + str(userEqId) +', slice '  + str (sliceId) + ', eps bearer id '  + str (epsBearerId) + ', redirect direction to a ' + str(redirect_dir_to) + ' server')
        
    """
    Step 2: collect the necessary information by relying on LL-MEC
    """ 
    
    fm = llmec_sdk.flow_manager(log=adapter.log,
                                url=adapter.url,
                                port=adapter.port,
                                op_mode=adapter.op_mode)
    bm = llmec_sdk.bearer_manager(log=adapter.log,
                                  url=adapter.url,
                                  port=adapter.port,
                                  op_mode=adapter.op_mode)
    #fm.flow_status()
    bm.get_all_bearer_context()
    
    """
    Step 3: Redirect the bearer(s) to/from a local/remote server
    """
            
    status = 'disconnected'
    core_adapter_routes["userEqId"] = userEqId        
    if epsBearerId == -1: #redirect all bearers belong to a slice to local/remote server
        if redirect_dir_to == 'local': #to local server
            adapter.log.info('Send command to LL-MEC to redirect all bearers belonging to this slice from a remote server (' + str(remote_ip) + ') to a local server (' + str(local_ip) + ')')   
            status = bm.redirect_all_ue_bearers_belong_to_sliceid(imsi=userEqId, slice_id=sliceId, from_ip=remote_ip,to_ip=local_ip)
            core_adapter_routes["routes"][0]["FromServer"] = remote_ip
            core_adapter_routes["routes"][0]["ToServer"] = local_ip                        
        elif redirect_dir_to == 'remote': #to remote server
            adapter.log.info('Send command to LL-MEC to redirect all bearers belonging to this slice from a local server (' + str(local_ip) + ') to a remote server (' + str(remote_ip) + ')')
            status = bm.redirect_all_ue_bearers_belong_to_sliceid(imsi=userEqId, slice_id=sliceId, from_ip=local_ip, to_ip=remote_ip)
            core_adapter_routes["routes"][0]["FromServer"] = local_ip
            core_adapter_routes["routes"][0]["ToServer"] = remote_ip
    elif epsBearerId > -1: #redirect this bearers to local/remote server
        if redirect_dir_to == 'local': 
            adapter.log.info('Send command to LL-MEC to redirect this bearer from a remote server (' + str(remote_ip) + ') to a local server (' + str(local_ip) + ')')
            status = bm.redirect_ue_bearer_belong_to_sliceid(imsi=userEqId, eps_drb=epsBearerId, slice_id=sliceId, from_ip=remote_ip,to_ip=local_ip)
            core_adapter_routes["routes"][0]["FromServer"] = remote_ip
            core_adapter_routes["routes"][0]["ToServer"] = local_ip
        elif redirect_dir_to == 'remote': 
            adapter.log.info('Send command to LL-MEC to redirect this bearer from a local server (' + str(local_ip) + ') to a remote server (' + str(remote_ip) + ')')
            status = bm.redirect_ue_bearer_belong_to_sliceid(imsi=userEqId, eps_drb=epsBearerId,slice_id=sliceId, from_ip=local_ip, to_ip=remote_ip)   
            core_adapter_routes["routes"][0]["FromServer"] = local_ip
            core_adapter_routes["routes"][0]["ToServer"] = remote_ip
            
    if status == 'connected':
        return core_adapter_routes, 201 
    else:
        return NoContent, 500             

            
        
        

