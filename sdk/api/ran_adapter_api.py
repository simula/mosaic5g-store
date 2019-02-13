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


class adapter(object):
    #for FlexRAN
    url = ''
    port = ''
    op_mode = ''
    log_level = ''
    template = ''  
        
    template_data = ''

    maxmcs_dl= {}
    maxmcs_ul = {}
    
    # from rrm_app
    enb_sfn={}
    enb_ulrb={}
    enb_dlrb={}
    enb_ulmaxmcs={}
    enb_dlmaxmcs={}

    ue_dlwcqi={}
    ue_phr={}

    lc_ue_bsr={}
    lc_ue_report={}
    lc_ue_dlrb={}
    lc_ue_ulrb={}
    lc_ue_dltbs={}
    lc_ue_ultbs={}
    
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
    cpsr_url = '' #"http://localhost:9191/slicenet/ctrlplane/cpsr_cps/v1/cps-instances/1"
    heartbeat_timer = 0.0
    """
    cps_instance_id = None
    cps_type = None
    cps_status = None
    slicenet_id = None
    fqdn = None
    ipv4_addresses = None
    ipv6_addresses = None
    ipv6_prefixes = None
    capacity = None
    load = None
    priority = None
    cps_services = None
    
    serviceInstanceId = None
    serviceName = None
    version = "v1.0"
    schema = None
    slicenetId = None
    fqdn = None
    ipEndPoints = None 
    apiPrefix = None
    defaultNotificationSubscriptions = None
    allowedCPSTypes = None
    allowedSlices = None
    service_capacity = None
    service_load = None
    """
def update_instance_info():
    """!@brief update_instance_info update instance info into a json file
    """
        
    #read JSON file
    with open('./inputs/cpsr.json', "+r") as data_file:
        data = json.load(data_file)
        data_file.close()
        
    #Update the data, for example
    data["cpsStatus"] = "REGISTERED"         
          
    #write the update information to the file
    with open('./inputs/cpsr.json', "w") as data_file:
        #json.dump(data,data_file)
        data_file.write(json.dumps(data))
        data_file.close()
        
        
def register():
    """!@brief Register the Adpater with a NRF (e.g., CPSR) 
    """
    status = 0                
    # Read JSON file
    with open('./inputs/cpsr.json') as data_file:
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
        print e 
            
    else:
        # process the response
        res_body = response.read().decode("utf-8")
        print("Status: ", response.code)
        status = int(response.code)
        
    if (status == 201):
        print(res_body)
        jsondata = json.loads(res_body)
        print("HeartbeatTimer: ", jsondata["heartbeatTimer"])
        adapter.heartbeat_timer = jsondata["heartbeatTimer"]
        t = Timer(adapter.heartbeat_timer, update,()).start() 
            
           
def update():
    """!@brief Update the Adpater with a NRF (e.g., CPSR) 
    """
    status = 0                
    # Read JSON file
    with open('./inputs/cpsr_update.json') as data_file:
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
        print e.args
        #TODO: should try to register after ... seconds
        
    except urllib2.HTTPError as e:
        print "ERROR: ", e
        if (e.code == 404):
            print "Send register ... "
            register()
            
    else:
        # process the response
        res_body = response.read().decode("utf-8")
        print("Status: ", response.code)
        status = int(response.code)            
    
    #if ok, continue updating when the heartbeat_timer expires   
    if (status == 200):  
        print(res_body)
        jsondata = json.loads(res_body)              
        #update the information if necessary
        #update_instance_info()    
        t = Timer(adapter.heartbeat_timer, update,()).start()
    #if there's no information
    elif (status == 404): 
        register()       

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
    parser.add_argument('--app-port', metavar='[option]', action='store', type=int,
                        required=False, default=8080, 
                        help='set the App port to open data: 8080 (default)')
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

    parser.add_argument('--cpsr-url', metavar='[option]', action='store', type=str,
                        required=False, default='http://localhost', 
                        help='set the CPSR URL: loalhost (default)')
    
    #parse the arguments and store in the appropriate variables
    args = parser.parse_args()        
    adapter.url = args.url
    adapter.port = args.port
    adapter.op_mode = args.op_mode
    adapter.log_level = args.log
    adapter.template = args.template 
    adapter.cpsr_url = args.cpsr_url                     
       
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
            # skip the control channels, SRB1 and SRB2
            for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :
                # for each lcgid rater than lc
                adapter.lc_ue_bsr[enb,ue,lc] = sm.get_ue_bsr(enb,ue,lc=lc)
                adapter.lc_ue_report[enb, ue, lc] = sm.get_ue_lc_report(enb=enb, ue=ue, lc=lc)
                       
def get_policy_maxmcs(rrm,sm) :
    """!@brief get_policy_maxmcs Get the value maximum of MCS 
        @param sm: Statistic manager class (stats_manager, FlexRAN sdk) 
        @param rrm: Radio resource management policy (rrm_policy, FlexRAN sdk) 
    """
        
    for enb in range(0, sm.get_num_enb()) :
        adapter.maxmcs_dl[enb] = {}
        for sid in range(0, rrm.get_num_slices(enb) ):  # get_input_slice_nums and get_num_slices
            adapter.maxmcs_dl[enb][sid] = rrm.get_slice_maxmcs(sid=sid, dir='DL')
                
    for enb in range(0, sm.get_num_enb()) :
        adapter.maxmcs_ul[enb] = {}
        for sid in range(0, rrm.get_num_slices(enb) ):
            adapter.maxmcs_ul[enb][sid] = rrm.get_slice_maxmcs(sid=sid, dir='UL')
            
            
def get_policy_mcs(rrm, enb, ue, dir):
    """!@brief get_policy_mcs Get the value of MCS 
        @param rrm: Radio resource management policy (rrm_policy, FlexRAN sdk) 
        @param enb: index of eNB
        @param ue: index of UE
        @param dir: defines downlink or uplink direction         
    """
    sid = ue % rrm.get_num_slices()
    if dir == 'dl' or dir == "DL":
        return rrm_app_vars.cqi_to_mcs[adapter.ue_dlwcqi[enb,ue] ]
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
        elif (adapter.enb_dlrb[enb] == 100):
             adapter.min_dlrb[enb] = 4
              
        adapter.min_ulrb[enb] = 2
        if (adapter.enb_ulrb[enb] == 25):
            adapter.min_ulrb[enb] = 2
        elif (adapter.enb_ulrb[enb] == 50):
            adapter.min_ulrb[enb] = 3
        elif (adapter.enb_ulrb[enb] == 100):
             adapter.min_ulrb[enb] = 4         
        
        for ue in range(0, sm.get_num_ue(enb=enb)) :
            # Initialization of MCS (Dl = conversion DL wideband CQI -> MCS, UL : fixed value) and number of RBs
            adapter.ue_dlmcs[enb,ue] = get_policy_mcs(rrm, enb, ue, "DL")
            #adapter.ue_dlmcs[enb,ue] = rrm_app_vars.cqi_to_mcs[adapter.ue_dlwcqi[enb,ue]]
            adapter.ue_ulmcs[enb,ue] = get_policy_mcs(rrm, enb, ue, "UL")
            adapter.ue_ulrb[enb,ue]  = 0
            adapter.ue_dlrb[enb,ue]  = 0
            # skip the control channels, SRB1 and SRB2, start at index 2
            for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :
                # Initialization of number of RBs for LC
                adapter.lc_ue_ulrb[enb,ue,lc] = 0
                adapter.lc_ue_dlrb[enb,ue,lc] = 0          
      
                                   
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
    try:
        direction = body['bandIncDir']  
        band_inc_val = float(body['bandIncVal'])        
    except (ValueError, KeyError):
        return NoContent, 400    
        
    if direction == 'dl' or direction == "DL":
        dir = 'dl'
    elif direction == 'ul' or direction == "UL":
        dir = 'ul'
    else : #Unknown directions        
        return NoContent, 400    
    
    band_unit_scale = body['bandUnitScale']
    if (band_unit_scale == 'MB' or band_unit_scale == 'mb'):
        unit_scale = 1000
    if (band_unit_scale == 'KB' or band_unit_scale == 'kb'):
        unit_scale = 1      
    
    """
    Step 1: collect the necessary information by relying on FlexRAN
    """                
    log=flexran_sdk.logger(log_level=adapter.log_level).init_logger()
    rrm = flexran_sdk.rrm_policy(log=log,
                                 url=adapter.url,
                                 port=adapter.port,
                                 op_mode=adapter.op_mode)
    policy=rrm.read_policy()
    sm = flexran_sdk.stats_manager(log=log,
                                   url=adapter.url,
                                   port=adapter.port,
                                   op_mode=adapter.op_mode)               
    log.info('Reading the status of the underlying eNBs')
    sm.stats_manager('all')
    log.info('Gather statistics')
    get_statistics(sm)
    
    #initialize the variables based on the collected information
    initialize_variables(rrm=rrm,sm=sm)
               
    #at this moment, we can check if SliceID is valid
    slice_id = int(sliceId)
    if (slice_id < 0):
        print("SliceId is not valid")
        return NoContent, 400
    elif (slice_id > rrm.get_num_slices(dir='dl') and dir=='dl'):
        print("SliceId is not valid")
        return NoContent, 400
    elif (slice_id > rrm.get_num_slices(dir='ul') and dir=='ul'):
        print("SliceId is not valid")
        return NoContent, 400   
    
    """
    Step 2: Caculate current bitrate based on N_RB, SliceID
    """ 
    log.info('num dl slices: ' + str(rrm.get_num_slices(dir='dl')))
    log.info('rb percentage for slice (slice=' + str(slice_id) + ', dir=dl): ' +  str(rrm.get_slice_rb(slice_id, dir='dl')))      
    log.info('num ul slices: ' + str(rrm.get_num_slices(dir='ul')))
    log.info('rb percentage for slice (slice=' + str(slice_id) + ', dir=ul): '+  str(rrm.get_slice_rb(slice_id, dir='ul')))  
    for enb in range(0, sm.get_num_enb()) :
        log.info('num dl RB: ' + str(adapter.enb_dlrb[enb]))
        log.info('num ul RB: ' + str(adapter.enb_ulrb[enb])) 

    #Caculate current bitrate based on N_RB  
    for enb in range(0, sm.get_num_enb()) :
        # Loop on slices to calculate the current bit rate, for DL first
        for slice in range(0, rrm.get_num_slices(dir='dl')):
            sid = slice
            slice_dl_tbs = 0
            dl_itbs = rrm_app_vars.mcs_to_itbs[rrm.get_slice_maxmcs(sid=sid, dir='dl')]            
            adapter.max_rate_dl[enb] = rrm_app_vars.tbs_table[dl_itbs][adapter.enb_dlrb[enb]]
            #should verify the value of rrm.get_slice_rb(sid=sid, dir='dl') 
            adapter.current_rate_dl[enb][sid] = adapter.max_rate_dl[enb] * rrm.get_slice_rb(sid=sid, dir='dl')            
            adapter.current_slice_dlrb[enb][sid] =  int (adapter.enb_dlrb[enb] * rrm.get_slice_rb(sid=sid, dir='dl'))           
                    
            log.info('Max Rate DL (enb): (' + str(enb) + ') ' + str(adapter.max_rate_dl[enb]))
            log.info('Current Rate DL (enb,sid, percentage): (' + str(enb) + ', ' + str(sid) + ', '+ str(rrm.get_slice_rb(sid=sid, dir='dl'))+') ' + str(adapter.current_rate_dl[enb][sid]))
            log.info('Current slice RB DL  (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.current_slice_dlrb[enb][sid]))
        
        # Loop on slices to calculate the current bit rate, for UL                                 
        for slice in range(0, rrm.get_num_slices(dir='ul')):
            sid = slice
            slice_ul_tbs = 0
            ul_itbs = rrm_app_vars.mcs_to_itbs[rrm.get_slice_maxmcs(sid=sid, dir='ul')]            
            adapter.max_rate_ul[enb] = rrm_app_vars.tbs_table[ul_itbs][adapter.enb_ulrb[enb]]
            #should verify the value of rrm.get_slice_rb(sid=sid, dir='ul') 
            adapter.current_rate_ul[enb][sid] = adapter.max_rate_ul[enb] * rrm.get_slice_rb(sid=sid, dir='ul')            
            adapter.current_slice_ulrb[enb][sid] =  int (adapter.enb_ulrb[enb] * rrm.get_slice_rb(sid=sid, dir='ul'))           
                    
            log.info('Max Rate UL (enb): (' + str(enb) + ') ' + str(adapter.max_rate_ul[enb]))
            log.info('Current Rate UL (enb,sid, percentage): (' + str(enb) + ', ' + str(sid) + ', '+ str(rrm.get_slice_rb(sid=sid, dir='ul'))+') ' + str(adapter.current_rate_ul[enb][sid]))
            log.info('Current slice RB UL  (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.current_slice_ulrb[enb][sid]))
            
                       
    '''
    check with Navid/Robert
    based on connected UE
    '''
    '''        
    for enb in range(0, sm.get_num_enb()) :
        # Loop on slices 
        for slice in range(0, rrm.get_num_slices(dir='dl')):
            sid = slice #adapter.slices_priority_dl[slice][0]
            slice_dl_tbs = 0

            # Loop on UEs connected to the current eNodeB and in the current slice
            ue_in_slice = (ue for ue in range(0, sm.get_num_ue(enb=enb)) if ue % rrm.get_num_slices(dir='dl') == sid)
            for ue in ue_in_slice :
                # skip the control channels, SRB1 and SRB2, start at index 2
                for lc in range(2, sm.get_num_ue_lc(enb=enb,ue=ue)) :

                    # Make sure that slices with reserved rate get what they need, DL
                    #if rrm_kpi_app.reserved_rate_dl[enb][sid] > slice_dl_tbs / 1000 :
    '''              
                    #test new way to calculate
    '''
                    #calculate the required RB for DL
                    dl_itbs = rrm_app_vars.mcs_to_itbs[adapter.ue_dlmcs[enb,ue]]
                    adapter.ue_dlrb[enb,ue]=0
                    adapter.lc_ue_dlrb[enb,ue,lc]=2
                    dl_itbs=rrm_app_vars.mcs_to_itbs[adapter.ue_dlmcs[enb,ue]]
                    adapter.lc_ue_dltbs[enb,ue,lc]=rrm_app_vars.tbs_table[dl_itbs][adapter.lc_ue_dlrb[enb,ue,lc]]
                    while adapter.lc_ue_report[enb, ue, lc]['txQueueSize'] > adapter.lc_ue_dltbs[enb,ue,lc] : 
                        if adapter.lc_ue_dlrb[enb,ue,lc] > adapter.enb_available_dlrb[enb] :
                            log.info('no available dlrb')
                            break
                        adapter.lc_ue_dlrb[enb,ue,lc]+=2
                        adapter.lc_ue_dltbs[enb,ue,lc]=rrm_app_vars.tbs_table[dl_itbs][adapter.lc_ue_dlrb[enb,ue,lc]]

                    adapter.ue_dlrb[enb,ue]+=adapter.lc_ue_dlrb[enb,ue,lc]
                    adapter.enb_available_dlrb[enb]-=adapter.ue_dlrb[enb,ue]
                    print "THINH adapter.ue_dlrb[enb,ue]: ", adapter.ue_dlrb[enb,ue]
                    #end test
    '''
    '''                                    
                    dl_itbs                         = rrm_app_vars.mcs_to_itbs[adapter.ue_dlmcs[enb,ue]]
                    adapter.lc_ue_dltbs[enb,ue,lc]  = rrm_app_vars.tbs_table[dl_itbs][adapter.lc_ue_dlrb[enb,ue,lc]]
                    adapter.max_rate_dl = {}
                    adapter.max_rate_dl[enb] = rrm_app_vars.tbs_table[dl_itbs][adapter.enb_dlrb[enb]]
                    #should verify the value of rrm.get_slice_rb(sid=sid, dir='dl') 
                    adapter.current_rate_dl[enb][sid] = adapter.max_rate_dl[enb] * rrm.get_slice_rb(sid=sid, dir='dl') 
                    adapter.slice_availabe_dlrb[enb][sid] =  int (adapter.enb_available_dlrb[enb] * rrm.get_slice_rb(sid=sid, dir='dl'))
                    
                    log.info('Max Rate DL (enb): (' + str(enb) + ') ' + str(adapter.max_rate_dl[enb]))
                    log.info('Current Rate DL (enb,sid, percentage): (' + str(enb) + ', ' + str(sid) + ', '+ str(rrm.get_slice_rb(sid=sid, dir='dl'))+') ' + str(adapter.current_rate_dl[enb][sid]))
                    log.info('Slice Available DL RB  (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.slice_availabe_dlrb[enb][sid]))
                                        
                    print "Current Rate DL [enb][sid]: ", rrm_app_vars.tbs_table[dl_itbs][adapter.slice_availabe_dlrb[enb][sid]]
    '''
    
    #calculate the maximum RB available for this a particular slice (RB of this eNB - RB allocated for other slices)
    allocated_dlrb = {}
    allocated_ulrb = {}    
    for enb in range(0, sm.get_num_enb()) :
        allocated_dlrb[enb] = {}
        allocated_ulrb[enb] = {}
        #for DL
        for slice in range(0, rrm.get_num_slices(dir='dl')):
            allocated_dlrb[enb][slice] = 0
            for sid in range(0, rrm.get_num_slices(dir='dl')):
                if (sid != slice):
                    allocated_dlrb[enb][slice] += int (adapter.enb_dlrb[enb] * rrm.get_slice_rb(sid=sid, dir='dl'))
                
            adapter.slice_availabe_dlrb[enb][slice] =  adapter.enb_dlrb[enb] - allocated_dlrb[enb][slice]
            log.info('number of DL Slices: ' + str(rrm.get_num_slices(dir='dl')))
            log.info('Available DL RB for  (enb): (' + str(enb) + ') ' + str(adapter.enb_dlrb[enb]))
            log.info('Available DL RB for  (enb,sid): (' + str(enb) + ', ' + str(slice) + ') ' + str(adapter.slice_availabe_dlrb[enb][slice]))
        #for UL
        for slice in range(0, rrm.get_num_slices(dir='ul')):
            allocated_ulrb[enb][slice] = 0
            for sid in range(0, rrm.get_num_slices(dir='ul')):
                if (sid != slice):
                    allocated_ulrb[enb][slice] += int (adapter.enb_ulrb[enb] * rrm.get_slice_rb(sid=sid, dir='ul'))
                
            adapter.slice_availabe_ulrb[enb][slice] =  adapter.enb_ulrb[enb] - allocated_ulrb[enb][slice]
            log.info('number of UL Slices: ' + str(rrm.get_num_slices(dir='ul')))
            log.info('Available UL RB for  (enb): (' + str(enb) + ') ' + str(adapter.enb_ulrb[enb]))
            log.info('Available UL RB for  (enb,sid): (' + str(enb) + ', ' + str(slice) + ') ' + str(adapter.slice_availabe_ulrb[enb][slice]))                            
    
    '''
    Step 2: Caculate the new value
    '''
    
    for enb in range(0, sm.get_num_enb()) :
        # Loop on slices to caculate the new bitrate for DL
        for slice in range(0, rrm.get_num_slices(dir='dl')):
            slice_dl_tbs = 0.0
            sid = slice            
            adapter.new_rate_dl[enb][sid] = adapter.current_rate_dl[enb][sid] +  float(band_inc_val) * float(unit_scale)
            log.info('Expected Bitrate DL (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.new_rate_dl[enb][sid]))
            #calculate the required RB for DL
            dl_itbs = rrm_app_vars.mcs_to_itbs[rrm.get_slice_maxmcs(sid=sid, dir='DL')]
            expected_dlrb = 0
             
            while slice_dl_tbs  < adapter.new_rate_dl[enb][sid] :
                expected_dlrb +=1
                if expected_dlrb > adapter.slice_availabe_dlrb[enb][sid]: #adapter.enb_dlrb[enb] :
                    log.info('no available dlrb')
                    break                
                slice_dl_tbs = rrm_app_vars.tbs_table[dl_itbs][expected_dlrb]
            
            expected_dlrb -=1
            #make sure that the expected dlrb is always greater than the miminal value   
            if (expected_dlrb < adapter.min_dlrb[enb]):
                expected_dlrb = adapter.min_dlrb[enb]  
            
            log.info('New DL RB (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(expected_dlrb))
            log.info('New DL bitrate (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(slice_dl_tbs))
            adapter.percentage_dl[enb][sid] = float(expected_dlrb)/float(adapter.enb_dlrb[enb])
            log.info('Percentage to be set (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.percentage_dl[enb][sid]))           
        
        # Loop on slices to caculate the new bitrate for UL   
        for slice in range(0, rrm.get_num_slices(dir='ul')):
            slice_ul_tbs = 0.0
            sid = slice            
            adapter.new_rate_ul[enb][sid] = adapter.current_rate_ul[enb][sid] +  float(band_inc_val) * float(unit_scale)
            log.info('Expected Bitrate UL (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.new_rate_ul[enb][sid]))
            #calculate the required RB for UL
            ul_itbs = rrm_app_vars.mcs_to_itbs[rrm.get_slice_maxmcs(sid=sid, dir='UL')]
            expected_ulrb = 0
             
            while slice_ul_tbs  < adapter.new_rate_ul[enb][sid] :
                expected_ulrb +=1
                if expected_ulrb > adapter.slice_availabe_ulrb[enb][sid]: #adapter.enb_dlrb[enb] :
                    log.info('no available dlrb')
                    break
                slice_ul_tbs = rrm_app_vars.tbs_table[ul_itbs][expected_ulrb]
            
            expected_ulrb -=1
            #make sure that the expected ulrb is always greater than the miminal value   
            if (expected_ulrb < adapter.min_ulrb[enb]):
                expected_ulrb = adapter.min_ulrb[enb]  
            
            log.info('New UL RB (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(expected_ulrb))
            log.info('New UL bitrate (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(slice_ul_tbs))
            adapter.percentage_ul[enb][sid] = float(expected_ulrb)/float(adapter.enb_ulrb[enb])
            log.info('Percentage to be set (enb,sid): (' + str(enb) + ', ' + str(sid) + ') ' + str(adapter.percentage_ul[enb][sid]))  
    
    """
    Step 3: set new bitrate value to FlexRAN
    """           

    #rrm.dump_policy()
    for enb in range(0, sm.get_num_enb()) :
        for slice in range(0, rrm.get_num_slices(dir=dir)):
            if (slice == slice_id):                
                rrm.set_slice_rb(slice_id, adapter.percentage_dl[enb][slice_id], dir=dir)
    rrm.dump_policy()
    rrm.save_policy()
    status = rrm.rrm_apply_policy()
    log.info('rb percentage for slice (slice=' + str(slice_id) + ', dir=' + str(dir)+ '): ' +  str(rrm.get_slice_rb(slice_id, dir='dl')))        
    
    if (status == 'connected'):
        return NoContent, 201
    else:
        return NoContent, 500
             
        
        

    