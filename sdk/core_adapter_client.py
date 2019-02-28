'''
an example for Adapter's client to set QoS on Core
'''

#import urllib.request
import json      
from threading import Timer
import urllib2
import urllib
import subprocess
import time


body = [{
  "bandIncDir": "DL",
  "bandIncVal": "10",
  "bandUnitScale": "MB"
   },
   {
  "bandIncDir": "UL",
  "bandIncVal": "10",
  "bandUnitScale": "MB"
  }  
]

class core_adapter_client(object):
    url = "http://localhost:9090/slicenet/ctrlplane/coreadapter/v1/coreadapter-instance/"
    qos_parameters = {}
    slice_id = 0
    
    def __init__(self, url='http://localhost'):
        super(core_adapter_client, self).__init__()
        self.qos_parameters = body 
          
    def set_qos_parameters (self, bandIncDir ='UL',bandIncVal='1',bandUnitScale='MB'):
        #jsondata = json.dumps(body)
        if (bandIncDir != ''):
            self.qos_parameters['bandIncDir'] =  bandIncDir
        if (bandIncVal != ''):
            self.qos_parameters['bandIncVal'] =  bandIncVal
        if (bandUnitScale != ''):
            self.qos_parameters['bandUnitScale'] =  bandUnitScale
                        
        
    def set_qoS_on_core(self, method='POST', sid=0, userEqId ='208950000000009', epsBearerId=1, body=body):
        """!@brief set_qoS_on_core set QOS Constraints on Core Adapter
        """
        time.sleep(1)  
        status = 0                
        #self.set_qos_parameters(bandIncDir='ul', bandIncVal='10')        
        jsondata = json.dumps(self.qos_parameters)
        print("slice ID "+ str(sid) + ", userEqId " + userEqId + ", epsBearerId " + str(epsBearerId))  
        print ('QoS parameters: ', str(jsondata))            
        #print(jsondata)        
        jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
        
        #method = 'POST'
        handler = urllib2.HTTPHandler()
        opener = urllib2.build_opener(handler)
        request = urllib2.Request(core_adapter_client.url + str(sid)+'/set_qos_on_core?userEqId='+userEqId+'&epsBearerId='+str(epsBearerId), data=jsondataasbytes)
        print("Request URL: " + core_adapter_client.url + str(sid)+'/set_qos_on_core?userEqId='+userEqId+'&epsBearerId='+str(epsBearerId))
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
        
        if (status == 201) or (status == 200):
            print(res_body)         
               
   
            
if __name__ == '__main__':
    core_adapter_client = core_adapter_client()
    core_adapter_client.set_qoS_on_core(sid=0, userEqId='208950000000009', epsBearerId=5, method='POST')    
    core_adapter_client.set_qoS_on_core(sid=0, userEqId='208950000000009', epsBearerId=-1, method='POST')
    core_adapter_client.set_qoS_on_core(sid=1, userEqId='208950000000009', epsBearerId=-1, method='PUT')
    core_adapter_client.set_qoS_on_core(sid=0, userEqId='208950000000001', epsBearerId=5, method='PUT')
    #test invalid request
    core_adapter_client.set_qoS_on_core(sid=2, userEqId='208950000000009', epsBearerId=-1, method='POST')
    core_adapter_client.set_qoS_on_core(sid=1, userEqId='208950000000008', epsBearerId=-1, method='POST')
    core_adapter_client.set_qoS_on_core(sid=0, userEqId='208950000000009', epsBearerId=6, method='POST')
    