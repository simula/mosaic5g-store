#!/usr/bin/python3

# Copyright (c) 2020 Eurecom
################################################################################
# Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The OpenAirInterface Software Alliance licenses this file to You under
# the Apache License, Version 2.0  (the "License"); you may not use this file
# except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#-------------------------------------------------------------------------------
# For more information about the OpenAirInterface (OAI) Software Alliance:
#      contact@openairinterface.org
################################################################################
# author Osama Arouk (arouk@eurecom.fr) & Navid Nikaein (navid.nikaein@eurecom.fr)

from flask import Flask, render_template, request, jsonify, json, url_for, make_response
from flask_restplus import Api, Resource, fields, inputs
from werkzeug.utils import secure_filename
import subprocess
import os, logging   
import argparse
from werkzeug.utils import cached_property
from werkzeug.datastructures import FileStorage

from apivars import *

flask_app = Flask(__name__.split('.')[0])                                                        
flask_api = Api(flask_app, 
		  version = "1.0", 
		  title = "Manager the OpenAPI of oai-upf", 
		  description = "Manage the manager of the OpenAPI of oai-upf",
          ordered = True,
          terms_url= "https://www.openairinterface.org/?page_id=698",
          contact = "arouk@eurecom.fr, navid.nikaein@eurecom.fr")

upf_space = flask_api.namespace('upf', description='Management of oai-upf')
api_space = flask_api.namespace('upf/api', description='Management of OpenAPI')
api_manager_space = flask_api.namespace('upf/api-manager', description='Management of the manager of OpenAPI')

api_change_host_port = api_space.parser()
api_change_host_port.add_argument('upf-host', type=str, default="0.0.0.0", required=True)
api_change_host_port.add_argument('upf-port', type=str , default="{}".format(api_port_default), required=True)

api_manager_change_host_port = api_manager_space.parser()
api_manager_change_host_port.add_argument('upf-host', type=str, default="0.0.0.0", required=True)
api_manager_change_host_port.add_argument('upf-port', type=str , default="{}".format(api_manager_port_default), required=True)


SNAP="/snap/{}/current".format(snap_name)

UPLOAD_FOLDER="/var/snap/{}/current/".format(snap_name)
PARAMETER_FOLDER="/var/snap/{}/common/".format(snap_name)
CONFIG_OPEN_API = "api_conf.json"
CONFIG_OPEN_API_MANAGER = "api_manager_conf.json"
# DIR for testing
# UPLOAD_FOLDER="/home/cigarier/Downloads/tmp/oai-upf/"
# PARAMETER_FOLDER="/home/cigarier/Downloads/tmp/oai-upf/parameters/"
# 

flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'json', 'conf'}
flask_app.config['PARAMETER_FOLDER'] = PARAMETER_FOLDER
flask_app.config['CONFIG_OPEN_API'] = CONFIG_OPEN_API
flask_app.config['CONFIG_OPEN_API_MANAGER'] = CONFIG_OPEN_API_MANAGER
flask_app.config['JSON_SORT_KEYS'] = False

## log
logger = logging.getLogger('upf.openapi')
logging.basicConfig(level=logging.DEBUG)
logger.info('Starting the manager of OpenAPI of {}'.format(snap_name))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@api_manager_space.route("/conf")
class MainClassUpfConf(Resource):
    @api_manager_space.produces(["application/json"])
    def get(self):
        """
        Get configuration file of OpenAPI
        """
        config_file = '{}{}'.format(PARAMETER_FOLDER, CONFIG_OPEN_API_MANAGER)

        if os.path.exists(config_file) and os.path.isfile(config_file):
            try:
                with open(config_file) as f:
                    api_config_param = json.load(f)
                    """
                    # config file is of the form
                    api_config_param = {
                        'upf-host': host_upf,
                        'upf-port': port_upf
                    }
                    """
            except:
                api_config_param = {
                    'upf-host': '0.0.0.0',
                    'upf-port': api_manager_port_default
                }  
        else:
            api_config_param = {
                    'upf-host': '0.0.0.0',
                    'upf-port': api_manager_port_default
                }            
        response = make_response(jsonify(api_config_param))
        response.headers.set("Content-Type", "application/json")
        return response
        
@api_manager_space.route("/journal")
class MainClassUpfApiManagerJournal(Resource):
    @api_manager_space.produces(["text"])
    def get(self):
        """
        Get the journal of the manager of OpenAPI oai-upf
        """        
        proc = subprocess.Popen(["$SNAP/run journal apidman"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 
        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

## OpenAPI of oai-upf
@api_space.route("/conf")
class MainClassUpfConf(Resource):
    @api_space.produces(["application/json"])
    def get(self):
        """
        Get configuration file of OpenAPI
        """
        config_file = '{}{}'.format(PARAMETER_FOLDER, CONFIG_OPEN_API)

        if os.path.exists(config_file) and os.path.isfile(config_file):
            try:
                with open(config_file) as f:
                    api_config_param = json.load(f)
                    """
                    # config file is of the form
                    api_config_param = {
                        'upf-host': host_upf,
                        'upf-port': port_upf
                    }
                    """
            except:
                api_config_param = {
                    'upf-host': '0.0.0.0',
                    'upf-port': api_port_default
                }  
        else:
            api_config_param = {
                    'upf-host': '0.0.0.0',
                    'upf-port': api_port_default
                }            
        response = make_response(jsonify(api_config_param))
        response.headers.set("Content-Type", "application/json")
        return response

@api_space.route("/start")
class MainClassUpfApiRestart(Resource):
    @api_space.produces(["text"])
    @api_space.expect(api_change_host_port)
    @api_space.doc(params={
                "upf-host": "Valid IP address of oai-upf",
                "upf-port": "Valid port of oai-upf"
    })
    def put(self):
        """
        Start OpenAPI oai-upf
        WARNING: you may loose the connection if you enter non valid parameters
        """     
        args = api_change_host_port.parse_args()
        host_upf = args['upf-host']
        port_upf =  args['upf-port']
        # Write the config parameters to json file to be used when starting up the flask service
        config_file = os.path.join(flask_app.config['PARAMETER_FOLDER'], flask_app.config['CONFIG_OPEN_API'])
        with open(config_file, 'w') as f:
            config_parameters = {
                "upf-host": host_upf,
                "upf-port": port_upf
            }
            json.dump(config_parameters, f)
        str_1 = request.url
        str_2 = request.path
        current_url = str(request.url).split(request.path)
        current_url = current_url[0]
        new_url = str(current_url).split("//")
        new_url = '{}//{}:{}'.format(new_url[0], host_upf, port_upf)
        proc = subprocess.Popen(["$SNAP/run start apid"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        service_status = serialize_service_status(out)
        message = {
            'openapi': new_url,
            'openapi-manager': current_url,
            'note': "OpenAPI of {} will be available at {}".format(snap_name,new_url),
            'status': service_status,
            'error': str(err)
        }
        response = make_response(message)
        response.headers.set("Content-Type", "text")
        return response
@api_space.route("/stop")
class MainClassUpfApiStop(Resource):
    @api_space.produces(["application/json"])
    def get(self):
        """
        Stop the OpenAPI oai-upf
        """        
        proc = subprocess.Popen(["$SNAP/run stop apid"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

        # response = make_response(out)
        # response.headers.set("Content-Type", "text")
        # return response

@api_space.route("/restart")
class MainClassUpfApiManagerRestart(Resource):
    @api_space.produces(["text"])
    @api_space.expect(api_change_host_port)
    @api_space.doc(params={
                "upf-host": "Valid IP address of oai-upf",
                "upf-port": "Valid port of oai-upf"
    })
    def put(self):
        """
        Restart the OpenAPI of oai-upf
        WARNING: you may loose the connection if you enter non valid parameters
        """     
        args = api_change_host_port.parse_args()
        host_upf = args['upf-host']
        port_upf =  args['upf-port']
        # Write the config parameters to json file to be used when starting up the flask service
        config_file = os.path.join(flask_app.config['PARAMETER_FOLDER'], flask_app.config['CONFIG_OPEN_API'])
        with open(config_file, 'w') as f:
            config_parameters = {
                "upf-host": host_upf,
                "upf-port": port_upf
            }
            json.dump(config_parameters, f)
        str_1 = request.url
        str_2 = request.path
        current_url = str(request.url).split(request.path)
        current_url = current_url[0]
        new_url = str(current_url).split("//")
        new_url = '{}//{}:{}'.format(new_url[0], host_upf, port_upf)
        proc = subprocess.Popen(["$SNAP/run restart apid"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        service_status = serialize_service_status(out)
        message = {
            'openapi': new_url,
            'openapi-manager': current_url,
            'note': "OpenAPI of {} will be available at {}".format(snap_name,new_url),
            'status': service_status,
            'error': str(err)
        }
        response = make_response(message)
        response.headers.set("Content-Type", "text")
        return response

@api_space.route("/status")
class MainClassUpfApiStatus(Resource):
    @api_space.produces(["application/json"])
    def get(self):
        """
        Get the status of OpenAPI oai-upf
        """        
        proc = subprocess.Popen(["$SNAP/run status apid"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["oai-upf.api-journal"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        service_status = serialize_service_status(out)

        # out_decoded = out.decode("utf-8")
        # out_split = (out_decoded).split('\n')
        # service_status = list()
        # for item in out_split:
        #     if ('Service' in item) and ('Startup' in item) and ('Current' in item) and ('Notes' in item):
        #         pass
        #     else:
        #         if ('' != item):
        #             item_split = item.split(" ")
        #             current_service_status = list()
        #             for val in item_split:
        #                 if ('' != val):
        #                     current_service_status.append(val)
        #             svc_stat = {
        #                 "service": current_service_status[0],
        #                 "startup": current_service_status[1],
        #                 "current": current_service_status[2],
        #                 "notes": current_service_status[3]
        #             }
        #             service_status.append(svc_stat)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response
@api_space.route("/journal")
class MainClassUpfApiJournal(Resource):
    @api_space.produces(["text"])
    def get(self):
        """
        Get the journal of the OpenAPI oai-upf
        """        
        proc = subprocess.Popen(["$SNAP/run journal apid"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 
        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response


def serialize_service_status(status):
    status_decoded = status.decode("utf-8")
    status_split = (status_decoded).split('\n')
    service_status = list()
    for item in status_split:
        if ('Service' in item) and ('Startup' in item) and ('Current' in item) and ('Notes' in item):
            pass
        else:
            if ('' != item):
                item_split = item.split(" ")
                current_service_status = list()
                for val in item_split:
                    if ('' != val):
                        current_service_status.append(val)
                svc_stat = {
                    "service": current_service_status[0],
                    "startup": current_service_status[1],
                    "current": current_service_status[2],
                    "notes": current_service_status[3]
                }
                service_status.append(svc_stat)
    return service_status
if __name__ == "__main__":                                                     
    
    parser = argparse.ArgumentParser(description='Provide host and port for flask api of oai-upf')
        
    parser.add_argument('--upf-host', metavar='[option]', action='store', type=str,
                        required=False, default='0.0.0.0', 
                        help='Set OpenAPI-MANAGER IP address to bind to, 0.0.0.0 (default)')
    
    parser.add_argument('--upf-port', metavar='[option]', action='store', type=str,
                        required=False, default='{}'.format(api_manager_port_default), 
                        help='Set OenAPI manager port number: {} (default)'.format(api_manager_port_default))
    args = parser.parse_args()
    config_file = '{}{}'.format(PARAMETER_FOLDER, CONFIG_OPEN_API_MANAGER)
    
    if os.path.exists(config_file) and os.path.isfile(config_file):
        with open(config_file) as f:
            config_param = json.load(f)
            """
            # config file is of the form
            config_param = {
                'upf-host': host_upf,
                'upf-port': port_upf
            }
            """
            print("config_param={}".format(config_param))
            flask_app.run(host=config_param["upf-host"], port=config_param["upf-port"], debug=True)
    else:
        flask_app.run(host='{}'.format(api_manager_host_default), port='{}'.format(api_manager_port_default), debug=True)

