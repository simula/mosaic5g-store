import datetime
import json

from connexion import NoContent
import yaml
import os
import argparse

#import urllib.request


 
def init():
    print ("CPSR service is running")
            
def UpdateCPSInstance(cpsInstanceId, body):
    """!@brief UpdateCPSInstance Update CPS Instance profile
        @param cpsInstanceId: Id of the CPS instance
        @param body: body of "PATCH" message 
    """


    #read JSON file
    with open('./inputs/cpsUpdateData.json', "r") as data_file:
        data = json.load(data_file)
        data_file.close()
           
      
    return data, 200
    #return NoContent, 404
        

def RegisterCPSInstance(cpsInstanceId, body):
    """!@brief RegisterCPSInstance Register a new CPS Instance
        @param cpsInstanceId: Id of the CPS instance
        @param body: body of "PUT" message 
    """
               
    #read JSON file
    with open('./inputs/cpsRegistrationData.json', "r") as data_file:
        data = json.load(data_file)
        data_file.close()
           
      
    return data, 201
    #return NoContent, 400
        
        

    