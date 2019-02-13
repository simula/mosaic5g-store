'''
an example for Adapter's client to set QoS on RAN
'''

#import urllib.request
import json      
from threading import Timer
import urllib2
import urllib


body = {
  "bandIncDir": "dl",
  "bandIncVal": "10",
  "bandUnitScale": "MB"
}

class ranAdapter_client(object):
    url = "http://localhost:9090/slicenet/ctrlplane/ranadapter/v1/ranadapter-instance/0/set_qos_on_ran"
          
    
    def __init__(self, url='http://localhost'):
        super(ranAdapter_client, self).__init__()
        
        
    def set_QoSOnRAN(self, method='POST'):
        """!@brief set_QoSOnRAN set QOS Constraints on RAN Adapter
        """
        status = 0                

        jsondata = json.dumps(body)
        #print(jsondata)        
        jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
        
        #method = 'POST'
        handler = urllib2.HTTPHandler()
        opener = urllib2.build_opener(handler)
        request = urllib2.Request(ranAdapter_client.url, data=jsondataasbytes)
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
    ranAdapter_client.set_QoSOnRAN(method='POST')
    