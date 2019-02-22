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

class ranAdapter_client(object):
    url = "http://localhost:9090/slicenet/ctrlplane/ranadapter/v1/ranadapter-instance/" #/0/set_qos_on_ran"
    qos_parameters = {}
    slice_id = 0
    
    def __init__(self, url='http://localhost'):
        super(ranAdapter_client, self).__init__()
        self.qos_parameters = body 
          
    def set_qos_parameters (self, bandIncDir ='UL',bandIncVal='1',bandUnitScale='MB'):
        #jsondata = json.dumps(body)
        if (bandIncDir != ''):
            self.qos_parameters['bandIncDir'] =  bandIncDir
        if (bandIncVal != ''):
            self.qos_parameters['bandIncVal'] =  bandIncVal
        if (bandUnitScale != ''):
            self.qos_parameters['bandUnitScale'] =  bandUnitScale
                        
        
    def set_QoSOnRAN(self, method='POST', sid=0, body=body):
        """!@brief set_QoSOnRAN set QOS Constraints on RAN Adapter
        """
        status = 0                
        #self.set_qos_parameters(bandIncDir='ul', bandIncVal='10')        
        jsondata = json.dumps(self.qos_parameters)
        print("slice ID ", sid)
        print ('QoS parameters: ', str(jsondata))            
        #print(jsondata)        
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
    '''
    #reduce percentage of slice 0 to 50%
    reduce_slice_percentage='{"intrasliceShareActive":false,"intersliceShareActive":false,"dl":[{"id":0,"percentage":30}]}'
    cmd_reduce= 'curl -X POST http://localhost:9999/slice/enb/-1 --data ' + reduce_slice_percentage #192.168.12.45
    print(cmd_reduce)
    return_code = subprocess.call(cmd_reduce, shell=True)
    
    #create the second slice
    time.sleep(5)
    second_slice='{"intrasliceShareActive":false,"intersliceShareActive":false,"dl":[{"id":5,"percentage":10}]}'
    cmd_create = 'curl -X POST http://localhost:9999/slice/enb/-1 --data ' + second_slice
    print(cmd_create)
    return_code = subprocess.call(cmd_create, shell=True)   
    
        #reduce percentage of slice 0 to 50%
    reduce_slice_percentage='{"intrasliceShareActive":false,"intersliceShareActive":false,"ul":[{"id":0,"percentage":30}]}'
    cmd_reduce= 'curl -X POST http://localhost:9999/slice/enb/-1 --data ' + reduce_slice_percentage #192.168.12.45
    print(cmd_reduce)
    return_code = subprocess.call(cmd_reduce, shell=True)
    '''
    #create the second slice
    #time.sleep(5)
    second_slice='{"intrasliceShareActive":false,"intersliceShareActive":false,"ul":[{"id":1,"percentage":10}]}'
    cmd_create = 'curl -X POST http://localhost:9999/slice/enb/-1 --data ' + second_slice
    print(cmd_create)
    return_code = subprocess.call(cmd_create, shell=True) 
    
    
    '''
    #set QoS on RAN: decrease 5MB for DL (slice 0)
    time.sleep(5)    
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='-5')    
    ranAdapter_client.set_QoSOnRAN(sid=0, method='POST')
    #set QoS on RAN: decrease 10MB for DL (slice 0)
    time.sleep(5)    
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='-10')    
    ranAdapter_client.set_QoSOnRAN(sid=0, method='POST')
    #set QoS on RAN: decrease 10MB for DL (slice 0)
    time.sleep(5)    
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='-10')    
    ranAdapter_client.set_QoSOnRAN(sid=0, method='POST')
    #set QoS on RAN: decrease 10MB for DL (slice 1)
    time.sleep(5)
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='-10') 
    ranAdapter_client.set_QoSOnRAN(sid=1, method='POST')
    #set QoS on RAN: decrease 5MB for DL (slice 1)
    time.sleep(5)
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='-20') 
    ranAdapter_client.set_QoSOnRAN(sid=1, method='POST')
    #set QoS on RAN: increase 20MB for DL (slice 1)
    time.sleep(5)
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='20') 
    ranAdapter_client.set_QoSOnRAN(sid=1, method='POST')
    
    #set QoS on RAN: increase 20MB for DL (slice 1)
    time.sleep(5)
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='20') 
    ranAdapter_client.set_QoSOnRAN(sid=1, method='POST')
    #set QoS on RAN: increase 20MB for DL (slice 1)
    time.sleep(5)
    ranAdapter_client.set_qos_parameters(bandIncDir='dl', bandIncVal='20') 
    ranAdapter_client.set_QoSOnRAN(sid=1, method='POST')
    '''    
    #set QoS on RAN: decrease 5MB for UL (slice 0)
    time.sleep(5)
    #ranAdapter_client.set_qos_parameters(bandIncDir='ul', bandIncVal='-10')    
    ranAdapter_client.set_QoSOnRAN(sid=0, method='POST')
    