'''
an example for Adapter's client to set QoS on RAN
'''

#import urllib.request
import json      
from threading import Timer
import urllib2
import urllib
import subprocess
import time


body_req_ul_dl = [{
  "bandIncDir": "DL",
  "bandIncVal": "-10",
  "bandUnitScale": "MB"
},
{
  "bandIncDir": "UL",
  "bandIncVal": "-10",
  "bandUnitScale": "MB"
}
]
body_req = [{
  "bandIncDir": "DL",
  "bandIncVal": "-10",
  "bandUnitScale": "MB"
}
]


cmd_stats = """curl -sX GET http://localhost:9999/stats | jq '
{
  slices: {
    dl: [
      .eNB_config?[0].eNB.cellConfig[0]?.sliceConfig.dl[]? | {
        id: .id,
        percentage: .percentage
      }
    ],
    ul: [
      .eNB_config?[0].eNB.cellConfig[0]?.sliceConfig.ul[]? | {
        id: .id,
        percentage: .percentage,
        firstRb: .firstRb
      }
    ]
  }
}
'
"""

class ranAdapter_client(object):
    url = "http://localhost:9090/slicenet/ctrlplane/ranadapter/v1/ranadapter-instance/" #/0/set_qos_on_ran"
    qos_parameters = {}
    slice_id = 0
    
    def __init__(self, url='http://localhost'):
        super(ranAdapter_client, self).__init__()
        self.qos_parameters = body_req 
        self.qos_parameters_ul_dl = body_req_ul_dl 
    
    def print_slice_stats(self): 
        print ('Slice statistics')
        time.sleep(1)
        return_code = subprocess.call(cmd_stats, shell=True)   
          
    def set_qos_parameters (self, bandIncDir ='UL',bandIncVal='1',bandUnitScale='MB'):
        #jsondata = json.dumps(body)
        if (bandIncDir != ''):
            self.qos_parameters[0]['bandIncDir'] =  bandIncDir
        if (bandIncVal != ''):
            self.qos_parameters[0]['bandIncVal'] =  bandIncVal
        if (bandUnitScale != ''):
            self.qos_parameters[0]['bandUnitScale'] =  bandUnitScale
    
    def set_qos_parameters_ul_dl (self, bandIncVal_ul='1',bandUnitScale_ul='MB',bandIncVal_dl='1',bandUnitScale_dl='MB' ):
        for index in range (0, len(self.qos_parameters_ul_dl)):
            if self.qos_parameters_ul_dl[index]['bandIncDir'] == 'UL' or self.qos_parameters_ul_dl[index]['bandIncDir'] == 'ul':              
                if (bandIncVal_ul != ''):
                    self.qos_parameters_ul_dl[index]['bandIncVal'] =  bandIncVal_ul
                if (bandUnitScale_ul != ''):
                    self.qos_parameters_ul_dl[index]['bandUnitScale'] =  bandUnitScale_ul
                                    
            if self.qos_parameters_ul_dl[index]['bandIncDir'] == 'DL' or self.qos_parameters_ul_dl[index]['bandIncDir'] == 'dl':              
                if (bandIncVal_dl != ''):
                    self.qos_parameters_ul_dl[index]['bandIncVal'] =  bandIncVal_dl
                if (bandUnitScale_dl != ''):
                    self.qos_parameters_ul_dl[index]['bandUnitScale'] =  bandUnitScale_dl
                    
   
    def set_QoSOnRAN(self, method='POST', sid=0, body=body_req):
        """!@brief set_QoSOnRAN set QOS Constraints on RAN Adapter
        """
        time.sleep(1)  
        status = 0                
        #self.set_qos_parameters(bandIncDir='ul', bandIncVal='10')        
        jsondata = json.dumps(body)
        print('Set QoS on RAN: slice ID ', sid, ' QoS parameters: ', str(jsondata))         
        jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
        
        #method = 'POST'
        handler = urllib2.HTTPHandler()
        opener = urllib2.build_opener(handler)
        request = urllib2.Request(ranAdapter_client.url + str(sid)+'/set_qos_on_ran', data=jsondataasbytes)
        request.get_method = lambda: method
        request.add_header("content-Type", 'application/json')
        
        try:
            response = opener.open(request)
        except urllib2.HTTPError as e:
            print e 
            
        else:
            # process the response
            res_body = response.read().decode("utf-8")
            print("Status: ", response.code)
            status = int(response.code)
        
        if (status == 201):
            print(res_body)         
               
   
            
if __name__ == '__main__':
    ranAdapter_client = ranAdapter_client()
 
    #create new slices
    #reduce percentage of slice 0 to 50%
    reduce_slice_percentage='{"intrasliceShareActive":false,"intersliceShareActive":false,"dl":[{"id":0,"percentage":50}]}'
    cmd_reduce= 'curl -X POST http://localhost:9999/slice/enb/-1 --data ' + reduce_slice_percentage #192.168.12.45
    print(cmd_reduce)
    return_code = subprocess.call(cmd_reduce, shell=True)
    ranAdapter_client.print_slice_stats()
    
    #create the second slice
    second_slice='{"intrasliceShareActive":false,"intersliceShareActive":false,"dl":[{"id":1,"percentage":10}]}'
    cmd_create = 'curl -X POST http://localhost:9999/slice/enb/-1 --data ' + second_slice
    print(cmd_create)
    return_code = subprocess.call(cmd_create, shell=True)
    ranAdapter_client.print_slice_stats()   
    
    #reduce percentage of slice 0 to 50%
    reduce_slice_percentage='{"intrasliceShareActive":false,"intersliceShareActive":false,"ul":[{"id":0,"percentage":40}]}'
    cmd_reduce= 'curl -X POST http://localhost:9999/slice/enb/-1 --data ' + reduce_slice_percentage #192.168.12.45
    print(cmd_reduce)
    return_code = subprocess.call(cmd_reduce, shell=True)
    ranAdapter_client.print_slice_stats()    

    #set QoS on RAN: decrease 5MB for DL (slice 0) 
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='-5')    
    ranAdapter_client.set_QoSOnRAN(sid=0, method='POST', body=ranAdapter_client.qos_parameters)
    ranAdapter_client.print_slice_stats()
    
    #set QoS on RAN: decrease 5MB for DL (slice 0)
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='-10')    
    ranAdapter_client.set_QoSOnRAN(sid=0, method='POST', body=ranAdapter_client.qos_parameters)
    ranAdapter_client.print_slice_stats()
    
    
    #set QoS on RAN: increase 10MB for DL (slice 1)
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='10') 
    ranAdapter_client.set_QoSOnRAN(sid=1, method='POST')
    ranAdapter_client.print_slice_stats()

    #set QoS on RAN: increase 10MB for DL (slice 1)    
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='10') 
    ranAdapter_client.set_QoSOnRAN(sid=1, method='POST')
    ranAdapter_client.print_slice_stats()

    #set QoS on RAN: increase 10MB for DL (slice 1)
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='10') 
    ranAdapter_client.set_QoSOnRAN(sid=1, method='POST')
    ranAdapter_client.print_slice_stats()

    #set QoS on RAN: increase 10MB for DL (slice 2-> invalid)
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='10') 
    ranAdapter_client.set_QoSOnRAN(sid=2, method='POST')
    ranAdapter_client.print_slice_stats()
       
    #set QoS on RAN: decrease 10MB for DL and UL (slice 0)
    ranAdapter_client.set_qos_parameters(bandIncDir='ul', bandIncVal='10')     
    ranAdapter_client.set_QoSOnRAN(sid=0, method='POST', body=ranAdapter_client.qos_parameters)
    ranAdapter_client.print_slice_stats()

    #set QoS on RAN: decrease 10MB for DL and UL (slice 0)
    ranAdapter_client.set_qos_parameters(bandIncDir='ul', bandIncVal='10')     
    ranAdapter_client.set_QoSOnRAN(sid=0, method='POST', body=ranAdapter_client.qos_parameters)
    ranAdapter_client.print_slice_stats()
        
    #set QoS on RAN: decrease 10MB for DL and UL (slice 0)      
    ranAdapter_client.set_qos_parameters_ul_dl( bandIncVal_ul='-10',bandUnitScale_ul='MB',bandIncVal_dl='10',bandUnitScale_dl='MB')    
    ranAdapter_client.set_QoSOnRAN(sid=0, method='POST', body=ranAdapter_client.qos_parameters_ul_dl)
    ranAdapter_client.print_slice_stats()
    


    