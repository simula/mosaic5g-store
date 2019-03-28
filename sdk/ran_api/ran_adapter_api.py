import datetime
import json

from connexion import NoContent
import yaml
import os
import argparse
from lib import flexran_sdk
from lib.flexran_sdk import stats_manager 
import rrm_app_vars

from threading import Timer
import urllib2
import urllib

CPSR_REGISTRATION_INTERVAL=10 

class adapter(object):
    #for FlexRAN
    url = ''
    port = ''
    op_mode = ''
    log_level = ''     

    maxmcs_dl= {}
    maxmcs_ul = {}

    enb_ulrb={}
    enb_dlrb={}
    enb_ulmaxmcs={}
    enb_dlmaxmcs={}

    ue_dlwcqi={}
    ue_phr={}

    ue_dlmcs={}
    ue_ulmcs={}
    
    # performance variables
    enb_available_ulrb={}
    enb_available_dlrb={}
    
    ue_dlrb={}
    ue_ulrb={}
    reserved_rate_dl = {}
    
    current_rate_dl = {}
    current_rate_ul = {}
    slice_availabe_dlrb = {}
    slice_availabe_ulrb = {}
    current_slice_dlrb = {}
    current_slice_ulrb = {}
    max_rate_dl = {}
    max_rate_ul = {}
    
    new_rate_dl = {}
    new_rate_ul = {}
    percentage_dl = {}
    percentage_ul = {}
    min_ulrb = {}
    min_dlrb = {}    
    
    #for CPSR
    cpsr_url = '' 
    heartbeat_timer = 0.0
    log = None
def update_instance_info(cpsStatus='', cpsInstanceId='', slicenetId='', serviceInstanceId='', load=0, capacity=0):
    """!@brief update_instance_info update instance info into a json file when necessary
    """
        
    #read JSON file
    with open('./inputs/ran_adapter_cpsr.json', "+r") as data_file:
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
    with open('./inputs/ran_adapter_cpsr.json', "w") as data_file:
        #json.dump(data,data_file)
        data_file.write(json.dumps(data))
        data_file.close()
        
        
def cpsr_register():
    """!@brief Register the Adpater with a NRF (e.g., CPSR) 
       TODO: should be updated to deal with the situation in which registration procedure is failed at the first time
    """
    status = 0                
    # Read JSON file
    with open('./inputs/ran_adapter_cpsr.json') as data_file:
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
        adapter.log.info("[CPSR_Register] HeartbeatTimer: " + str(jsondata["heartBeatTimer"]))
        adapter.heartbeat_timer = jsondata["heartBeatTimer"]
        t = Timer(adapter.heartbeat_timer, cpsr_update,()).start() 
    else:
        #print(res_body)
        #for the moment,try registratin after 10s
        t = Timer(CPSR_REGISTRATION_INTERVAL, cpsr_register,()).start()        
           
def cpsr_update():
    """!@brief Update the Adpater with a NRF (e.g., CPSR) 
    """
    status = 0                
    # Read JSON file
    with open('./inputs/ran_adapter_cpsr_update.json') as data_file:
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
    request.add_header("content-Type", 'application/json-patch+json')
    #print ('CPSR_URL:', adapter.cpsr_url)    
    try:
        response = opener.open(request)
    except urllib2.URLError as e:
        adapter.log.info('[CPSR_Update] ERROR: ' + str(e.args))
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
                        help='set the FlexRAN RTC URL: loalhost (default)')
    parser.add_argument('--app-url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost', 
                        help='set the App address to open data: loalhost (default)')
    parser.add_argument('--port', metavar='[option]', action='store', type=str,
                        required=False, default='9999', 
                        help='set the FlexRAN RTC port: 9999 (default)')
    parser.add_argument('--op-mode', metavar='[option]', action='store', type=str,
                        required=False, default='sdk', 
                        help='Set the app operation mode either with FlexRAN or with the test json files: test, sdk(default)')
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
    adapter.log = flexran_sdk.logger(log_level=adapter.log_level).init_logger()                    
       
def get_statistics(sm):
    """!@brief get_statistics Get statistics (eNB, MAC) from FlexRAN
        @param sm: stats_manager (FlexRAN sdk) 
    """
    for enb in range(0, sm.get_num_enb()) :
        adapter.enb_dlrb[enb] = sm.get_cell_rb(enb,dir='DL')
        adapter.enb_ulrb[enb] = sm.get_cell_rb(enb,dir='UL')
        adapter.enb_ulmaxmcs[enb] = sm.get_cell_maxmcs(enb,dir='UL')
        adapter.enb_dlmaxmcs[enb] = sm.get_cell_maxmcs(enb,dir='DL')

        for ue in range(0, sm.get_num_ue(enb=enb)) :
            adapter.ue_dlwcqi[enb,ue]   = sm.get_ue_dlwbcqi(enb,ue)
            adapter.ue_phr[enb,ue]      = sm.get_ue_phr(enb,ue)

                       
def get_ue_mcs(enb, ue, dir='dl'):
    """!@brief get_ue_mcs Get the value of MCS 
        @param enb: index of eNB
        @param ue: index of UE
        @param dir: defines downlink or uplink direction         
    """
    if dir == 'dl' or dir == "DL":
        return rrm_app_vars.cqi_to_mcs[adapter.ue_dlwcqi[enb,ue]]
    elif dir == 'ul' or dir == "UL": 
        return 8 # f(ue_phr[enb,ue])
    #else :
    #    self.log.error('Unknown direction ' + dir)
    #    return
  
def initialize_variables(rrm,sm):
    """!@brief initialize_variables Initialize the parameters based on collected information from FlexRAN 
        @param rrm: Radio resource management policy (rrm_policy, FlexRAN sdk) 
        @param sm: Statistic manager class (stats_manager, FlexRAN sdk)        
    """
    for enb in range(0, sm.get_num_enb()) :      
        adapter.reserved_rate_dl[enb] = {}
        #adapter.reserved_rate_ul[enb] = {}
        adapter.current_rate_dl[enb] = {}
        adapter.current_rate_ul[enb] = {}
        adapter.slice_availabe_dlrb[enb] = {}
        adapter.slice_availabe_ulrb[enb] = {}  
        adapter.current_slice_dlrb[enb] = {}
        adapter.current_slice_ulrb[enb] = {}
        adapter.new_rate_dl[enb] = {}
        adapter.new_rate_ul[enb] = {}
        adapter.percentage_dl[enb] = {}
        adapter.percentage_ul[enb] = {}
        adapter.min_ulrb[enb] = 0
        adapter.min_dlrb[enb] = 0
        
        adapter.enb_available_ulrb[enb]= adapter.enb_ulrb[enb]
        adapter.enb_available_dlrb[enb]= adapter.enb_dlrb[enb]        
        
        #set minimal value for RB
        adapter.min_dlrb[enb] = 2
        if (adapter.enb_dlrb[enb] == 25):
            adapter.min_dlrb[enb] = 2
        elif (adapter.enb_dlrb[enb] == 50):
            adapter.min_dlrb[enb] = 3
        elif (adapter.enb_dlrb[enb] == 75):
            adapter.min_dlrb[enb] = 4
        elif (adapter.enb_dlrb[enb] == 100):
             adapter.min_dlrb[enb] = 4
              
        adapter.min_ulrb[enb] = 2
        if (adapter.enb_ulrb[enb] == 25):
            adapter.min_ulrb[enb] = 2
        elif (adapter.enb_ulrb[enb] == 50):
            adapter.min_ulrb[enb] = 3
        elif (adapter.enb_ulrb[enb] == 75):
            adapter.min_ulrb[enb] = 4
        elif (adapter.enb_ulrb[enb] == 100):
             adapter.min_ulrb[enb] = 4  
        
        for ue in range(0, sm.get_num_ue(enb=enb)) :
            # Initialization of MCS (Dl = conversion DL wideband CQI -> MCS, UL : fixed value) and number of RBs
            adapter.ue_dlmcs[enb,ue] = get_ue_mcs( enb, ue, "DL")
            #adapter.ue_dlmcs[enb,ue] = rrm_app_vars.cqi_to_mcs[adapter.ue_dlwcqi[enb,ue]]
            adapter.ue_ulmcs[enb,ue] = get_ue_mcs(enb, ue, "UL")
            adapter.ue_ulrb[enb,ue]  = 0
            adapter.ue_dlrb[enb,ue]  = 0     
      
                                   
def put_QoSOnRAN(sliceId, body):
    """!@brief put_QoSOnRAN set QOS Constraints on RAN Adapter
        @param sliceId: Id of the slice instance
        @param body: body of "PUT" message 
    """
    
    post_QoSOnRAN(sliceId, body)
    #TODO   
    #return NoContent, 400

def post_QoSOnRAN(sliceId, body):
    """!@brief Add QoS contraints to the corresponding network slice in the access network
        @param sliceId: Id of the slice
        @param body: body of post message including the parameters bandIncDir, bandIncVal and bandUnitScale
    """

    """
    Step 0: get information from the request and verify the input
    """
    num_request = len(body)
    if (num_request > 2):
        return NoContent, 400
    
    dir = {}
    unit_scale = {}
    band_inc_val = {}
    band_unit_scale = {}
    unit_scale_ul = 1
    unit_scale_dl = 1
    band_inc_val_dl = 0.0
    band_inc_val_ul = 0.0
    slice_id = -1   
    
    # check if the mapping between slicenetId and flexran sliceid exist! 
    with open('./inputs/mapping_slicenetid_sliceid.json') as data_file:
        slice_mapping = json.load(data_file)
        data_file.close()        

    for index in range (0, len(slice_mapping)):
        if slice_mapping[index]['slicenetid'] == sliceId:
            slice_id = int(slice_mapping[index]['sid'] )
    
    if slice_id == -1:
        print 'FlexRAN sliceId corresponding to the SlicenetId ' + sliceId+ ' does not exist!'
        return NoContent, 400    
      
    for req in range (0, num_request):
        try:
            direction = body[req]['bandIncDir']  
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

    for req in range (0, num_request):
        if  dir[req] == 'dl':
            try:
                band_inc_val_dl = float(body[req]['bandIncVal'])    
                band_unit_scale_dl = body[req]['bandUnitScale']
            except (ValueError, KeyError):
                return NoContent, 400
            
            if (band_unit_scale_dl == 'MB' or band_unit_scale_dl == 'mb'):
                unit_scale_dl = 1000
            if (band_unit_scale_dl == 'KB' or band_unit_scale_dl == 'kb'):
                unit_scale_dl = 1
            print('Received QoS parameters for SlicenetId '  + str (sliceId) + ', FlexRAN sid ' + str(slice_id) + ', direction dl, bandIncVal ' + str(band_inc_val_dl) + ', bandUnitScale ' + str(band_unit_scale_dl))
              
        elif dir[req] == 'ul':
            try:
                band_inc_val_ul = float(body[req]['bandIncVal'])  
                band_unit_scale_ul = body[req]['bandUnitScale']
            except (ValueError, KeyError):
                return NoContent, 400     
            if (band_unit_scale_ul == 'MB' or band_unit_scale_ul == 'mb'):
                unit_scale_ul = 1000
            if (band_unit_scale_ul == 'KB' or band_unit_scale_ul == 'kb'):
                unit_scale_ul = 1
            print('Received QoS parameters for SlicenetId '  + str (sliceId) +  ', FlexRAN sid ' + str(slice_id) + ', direction ul, bandIncVal ' + str(band_inc_val_ul) + ', bandUnitScale ' + str(band_unit_scale_ul))
 
    """
    Step 1: collect the necessary information by relying on FlexRAN
    """                
    rrm = flexran_sdk.rrm_policy(log=adapter.log,
                                 url=adapter.url,
                                 port=adapter.port,
                                 op_mode=adapter.op_mode)

    sm = flexran_sdk.stats_manager(log=adapter.log,
                                   url=adapter.url,
                                   port=adapter.port,
                                   op_mode=adapter.op_mode)
                   
    adapter.log.info('[post_QoSOnRAN] Reading the status of the underlying eNBs')
    sm.stats_manager('all')
    adapter.log.info('[post_QoSOnRAN] Gather statistics')
    get_statistics(sm)
    
    #initialize the variables based on the collected information
    initialize_variables(rrm=rrm,sm=sm)
               
     
    #at this moment, we can check if SliceID is valid
    #slice_id = int(sliceId)
    #if (slice_id < 0):
    #    adapter.log.info('SliceId is not valid')
    #    return NoContent, 400
    for req in range(0, num_request):
        if not sm.check_slice_id(sid=slice_id, dir=dir[req]):
            print ('slice '+ str(slice_id)+ ' is not exist! (dir=' + str(dir[req]) + ')' )
            return NoContent, 400       
   
    #print log
    adapter.log.info('Number DL slices: ' + str(sm.get_num_slices(dir='dl')))
    for slice in sm.get_slice_ids(dir='dl'):
        adapter.log.info('RB percentage for slice (slice=' + str(slice) + ', dir=dl): ' +  str(sm.get_slice_percentage(sid=slice, dir='dl')))      
    adapter.log.info('Number UL slices: ' + str(sm.get_num_slices(dir='ul')))
    for slice in sm.get_slice_ids(dir='ul'):
        adapter.log.info('RB percentage for slice (slice=' + str(slice) + ', dir=ul): '+  str(sm.get_slice_percentage(sid=slice, dir='ul')))  
    for enb in range(0, sm.get_num_enb()) :
        adapter.log.info('Number DL RB: ' + str(adapter.enb_dlrb[enb]))
        adapter.log.info('Number UL RB: ' + str(adapter.enb_ulrb[enb]))           
    
    
    """
    Step 2: Caculate current bitrate based on N_RB, SliceID
    """ 
        
    #Caculate current bitrate based on N_RB  
    for enb in range(0, sm.get_num_enb()) :
        # Loop on slices to calculate the current bit rate, for DL first
        for slice in sm.get_slice_ids(dir='dl'):
            sid = slice
            slice_dl_tbs = 0
            dl_itbs = rrm_app_vars.mcs_to_itbs[sm.get_slice_maxmcs(sid=sid, dir='dl')]            
            adapter.max_rate_dl[enb] = rrm_app_vars.tbs_table[dl_itbs][adapter.enb_dlrb[enb]]
            adapter.current_rate_dl[enb][sid] = adapter.max_rate_dl[enb] * sm.get_slice_percentage(sid=sid, dir='dl')/100.0            
            adapter.current_slice_dlrb[enb][sid] =  int (adapter.enb_dlrb[enb] * sm.get_slice_percentage(sid=sid, dir='dl')/100.0)         
                 
            adapter.log.debug('Max Rate DL (enb): (' + str(enb) + ') ' + str(adapter.max_rate_dl[enb]))
            adapter.log.debug('Current Rate DL (enb,sid, percentage): (' + str(enb) + ', ' + str(sid) + ', '+ str(sm.get_slice_percentage(sid=sid, dir='dl'))+') ' + str(adapter.current_rate_dl[enb][sid]))
            adapter.log.debug('Current slice RB DL (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.current_slice_dlrb[enb][sid]))
        
        # Loop on slices to calculate the current bit rate, for UL                                 
        for slice in sm.get_slice_ids(dir='ul'):
            sid = slice
            slice_ul_tbs = 0
            ul_itbs = rrm_app_vars.mcs_to_itbs[sm.get_slice_maxmcs(sid=sid, dir='ul')]            
            adapter.max_rate_ul[enb] = rrm_app_vars.tbs_table[ul_itbs][adapter.enb_ulrb[enb]]
            #should verify the value of rrm.get_slice_rb(sid=sid, dir='ul') 
            adapter.current_rate_ul[enb][sid] = adapter.max_rate_ul[enb] * sm.get_slice_percentage(sid=sid, dir='ul')/100.0            
            adapter.current_slice_ulrb[enb][sid] =  int (adapter.enb_ulrb[enb] * sm.get_slice_percentage(sid=sid, dir='ul')/100.0)           
                    
            adapter.log.debug('Max Rate UL (enb): (' + str(enb) + ') ' + str(adapter.max_rate_ul[enb]))
            adapter.log.debug('Current Rate UL (enb,sid, percentage): (' + str(enb) + ', ' + str(sid) + ', '+ str(sm.get_slice_percentage(sid=sid, dir='ul'))+') ' + str(adapter.current_rate_ul[enb][sid]))
            adapter.log.debug('Current slice RB UL (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.current_slice_ulrb[enb][sid]))
            
     
    #calculate the maximum RB available for this a particular slice (RB of this eNB - RB allocated for other slices)
    #TODO: should be updated according to intersliceShareActive 
    allocated_dlrb = {}
    allocated_ulrb = {}    
    for enb in range(0, sm.get_num_enb()) :
        allocated_dlrb[enb] = {}
        allocated_ulrb[enb] = {}
        #for DL
        for slice in sm.get_slice_ids(dir='dl'):
            allocated_dlrb[enb][slice] = 0
            for sid in sm.get_slice_ids(dir='dl'):
                if (sid != slice):
                    allocated_dlrb[enb][slice] += int (adapter.enb_dlrb[enb] * sm.get_slice_percentage(sid=sid, dir='dl')/100.0)
                
            adapter.slice_availabe_dlrb[enb][slice] =  adapter.enb_dlrb[enb] - allocated_dlrb[enb][slice]
            adapter.log.debug('Number of DL Slices: ' + str(sm.get_num_slices(dir='dl')))
            adapter.log.debug('Available DL RB for (enb): (' + str(enb) + ') ' + str(adapter.enb_dlrb[enb]))
            adapter.log.debug('Available DL RB for (enb,sid): (' + str(enb) + ', ' + str(slice) + ') ' + str(adapter.slice_availabe_dlrb[enb][slice]))
        #for UL
        for slice in sm.get_slice_ids(dir='ul'):
            allocated_ulrb[enb][slice] = 0
            for sid in sm.get_slice_ids(dir='ul'):
                if (sid != slice):
                    allocated_ulrb[enb][slice] += int (adapter.enb_ulrb[enb] * sm.get_slice_percentage(sid=sid, dir='ul')/100.0)
                
            adapter.slice_availabe_ulrb[enb][slice] =  adapter.enb_ulrb[enb] - allocated_ulrb[enb][slice]
            adapter.log.debug('number of UL Slices: ' + str(sm.get_num_slices(dir='ul')))
            adapter.log.debug('Available UL RB for (enb): (' + str(enb) + ') ' + str(adapter.enb_ulrb[enb]))
            adapter.log.debug('Available UL RB for (enb,sid): (' + str(enb) + ', ' + str(slice) + ') ' + str(adapter.slice_availabe_ulrb[enb][slice]))                            
    
    """
    Step 2: Caculate the new value
          New_bitrate = current_bitrate + band_inc_val * unit_scale
          Adjust/calibrate the new_bitrate to make sure that the corresponding number of RB is not less than a minimum RB 
          and not greater than RB available for this slice 
    """
    
    for enb in range(0, sm.get_num_enb()) :
        # Loop on slices to caculate the new bitrate for DL
        for slice in sm.get_slice_ids(dir='dl'):
            slice_dl_tbs = 0.0
            sid = slice            
            adapter.new_rate_dl[enb][sid] = adapter.current_rate_dl[enb][sid] +  float(band_inc_val_dl) * float(unit_scale_dl)
            adapter.log.debug('Expected Bitrate DL (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.new_rate_dl[enb][sid]))
            #calculate the required RB for DL
            dl_itbs = rrm_app_vars.mcs_to_itbs[sm.get_slice_maxmcs(sid=sid, dir='dl')]
            expected_dlrb = 0
             
            while slice_dl_tbs  < adapter.new_rate_dl[enb][sid] :
                expected_dlrb +=1
                if expected_dlrb > adapter.slice_availabe_dlrb[enb][sid]: 
                    adapter.log.debug('no available dlrb')
                    break                
                slice_dl_tbs = rrm_app_vars.tbs_table[dl_itbs][expected_dlrb]
            
            expected_dlrb -=1
            #make sure that the expected dlrb is not less than than the minimum RB   
            if (expected_dlrb < adapter.min_dlrb[enb]):
                adapter.log.debug('Expected DL RB ' + str(expected_dlrb) + " less than the minimum possible DL_RB " + str(adapter.min_dlrb[enb]))
                expected_dlrb = adapter.min_dlrb[enb]                
                adapter.log.debug('Set expected DL RB (enb,sid): (' + str(enb) + ', ' + str(sid) + ') to a minimum possible value: ' + str(expected_dlrb))  
            
            adapter.log.debug('New DL RB (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(expected_dlrb))
            adapter.log.debug('New DL bitrate (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(slice_dl_tbs))
            #Percentage should be a int value -> futher process, for now just get int from float 
            #it would be better if we get value of int (float +1)-> however should check if total percentage >100
            adapter.percentage_dl[enb][sid] = int (float(expected_dlrb)/float(adapter.enb_dlrb[enb])*100.0)            
            adapter.log.debug('DL Percentage to be set (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.percentage_dl[enb][sid]))           
        
        # Loop on slices to caculate the new bitrate for UL   
        for slice in sm.get_slice_ids(dir='ul'):
            slice_ul_tbs = 0.0
            sid = slice            
            adapter.new_rate_ul[enb][sid] = adapter.current_rate_ul[enb][sid] +  float(band_inc_val_ul) * float(unit_scale_ul)
            adapter.log.debug('Expected Bitrate UL (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.new_rate_ul[enb][sid]))
            #calculate the required RB for UL
            ul_itbs = rrm_app_vars.mcs_to_itbs[sm.get_slice_maxmcs(sid=sid, dir='ul')]
            expected_ulrb = 0
             
            while slice_ul_tbs  < adapter.new_rate_ul[enb][sid] :
                expected_ulrb +=1
                if expected_ulrb > adapter.slice_availabe_ulrb[enb][sid]: 
                    adapter.log.debug('no available dlrb')
                    break
                slice_ul_tbs = rrm_app_vars.tbs_table[ul_itbs][expected_ulrb]
            
            expected_ulrb -=1
            #make sure that the expected ulrb is always greater than or equal to the minimum value   
            if (expected_ulrb < adapter.min_ulrb[enb]):
                adapter.log.debug('Expected UL RB ' + str(expected_ulrb) + " less than the minimum possible UL_RB " + str(adapter.min_ulrb[enb]))
                expected_ulrb = adapter.min_ulrb[enb]
                adapter.log.debug('Set expected UL RB (enb,sid): (' + str(enb) + ', ' + str(sid) + ') to a minimum possible value: ' + str(expected_ulrb))  
            
            adapter.log.debug('New UL RB (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(expected_ulrb))
            adapter.log.debug('New UL bitrate (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(slice_ul_tbs))
            #Percentage should be a int value -> futher process, for now just get int from float 
            #it would be better if we get value of int (float +1)-> however should check if total percentage >100                      
            adapter.percentage_ul[enb][sid] = int (float(expected_ulrb)/float(adapter.enb_ulrb[enb]) *100.0)
            adapter.log.debug('UL Percentage to be set (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.percentage_ul[enb][sid]))  
    
    """
    Step 3: set new bitrate value to FlexRAN
    """         
    
    slice_config_dl={"intrasliceShareActive":"false","intersliceShareActive":"false","dl":[{"id":0,"percentage":100, "maxmcs":28}]}
    slice_config_ul={"intrasliceShareActive":"false","intersliceShareActive":"false","ul":[{"id":0,"percentage":100, "maxmcs":20}]}
    slice_config={"intrasliceShareActive":"false","intersliceShareActive":"false","ul":[{"id":0,"percentage":100, "maxmcs":20}], "dl":[{"id":0,"percentage":100, "maxmcs":28}] }
    
    for enb in range(0, sm.get_num_enb()) :
        if (num_request == 1):        
            adapter.log.info('Send command to FlexRAN to set slice configuration')                            
            if (dir[0] == 'dl'):
                data_dl  = sm.get_slice_config(sid=slice_id, dir='dl')
                slice_config_dl['dl'][0]['percentage'] = adapter.percentage_dl[enb][slice_id]
                slice_config_dl['dl'][0]['id'] = slice_id
                slice_config_dl['dl'][0]['maxmcs'] = data_dl["maxmcs"]
                #slice_config["dl"][slice_id]["percentage"] = adapter.percentage_dl[enb][slice_id]
                adapter.log.info("Slice Configuration for DL: " + str(adapter.percentage_dl[enb][slice_id]))
                adapter.log.info("Slice Configuration will be pushed to FlexRAN: \n" + str(slice_config_dl))
                status = rrm.rrm_apply_policy(slice=slice_id, policy=slice_config_dl)
                     
            if (dir[0] == 'ul'):
                data_ul  = sm.get_slice_config(sid=slice_id, dir='ul')
                slice_config_ul["ul"][0]["percentage"] = adapter.percentage_ul[enb][slice_id]
                slice_config_ul["ul"][0]["id"] = slice_id
                slice_config_ul["ul"][0]["maxmcs"] = data_ul["maxmcs"]
                #slice_config["ul"][slice_id]["percentage"] = adapter.percentage_ul[enb][slice_id]
                adapter.log.info("Slice Configuration for UL: " + str(adapter.percentage_ul[enb][slice_id]))
                adapter.log.info("Slice Configuration will be pushed to FlexRAN: \n" + str(slice_config_ul)) 
                status = rrm.rrm_apply_policy(slice=slice_id, policy=slice_config_ul)
                    
            #apply to FlexRAN
            if (status != 'connected'):                
                return NoContent, 500
            
        elif (num_request == 2):
            adapter.log.info('Send command to FlexRAN to set slice configuration')                            
            data_dl  = sm.get_slice_config(sid=slice_id, dir='dl')
            slice_config['dl'][0]['percentage'] = adapter.percentage_dl[enb][slice_id]
            slice_config['dl'][0]['id'] = slice_id
            slice_config['dl'][0]['maxmcs'] = data_dl["maxmcs"]
            adapter.log.info("Slice Configuration for DL: " + str(adapter.percentage_dl[enb][slice_id]))

            data_ul  = sm.get_slice_config(sid=slice_id, dir='ul')
            slice_config["ul"][0]["percentage"] = adapter.percentage_ul[enb][slice_id]
            slice_config["ul"][0]["id"] = slice_id
            slice_config["ul"][0]["maxmcs"] = data_ul["maxmcs"]
            adapter.log.info("Slice Configuration for UL: " + str(adapter.percentage_ul[enb][slice_id]))                 
           
            adapter.log.info("Slice Configuration will be pushed to FlexRAN: \n" + str(slice_config)) 
            status = rrm.rrm_apply_policy(slice=slice_id, policy=slice_config)

            #apply to FlexRAN
            if (status != 'connected'):                
                return NoContent, 500            
            
    if (status == 'connected'):
        return NoContent, 201
    else:
        return NoContent, 500      
        
        

    
