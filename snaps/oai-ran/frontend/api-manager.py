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

snap_name = "oai-ran"

api_host_default = '0.0.0.0'
api_port_default = 5550

api_manager_host_default = '0.0.0.0'
api_manager_port_default = 6660

flask_app = Flask(__name__.split('.')[0])                                                        
flask_api = Api(flask_app, 
		  version = "1.0", 
		  title = "Manager the OpenAPI of oai-ran", 
		  description = "Manage the manager of the OpenAPI of oai-ran",
          ordered = True,
          terms_url= "https://www.openairinterface.org/?page_id=698",
          contact = "arouk@eurecom.fr, navid.nikaein@eurecom.fr")

ran_space = flask_api.namespace('ran', description='Management of oai-ran')
api_space = flask_api.namespace('ran/api', description='Management of OpenAPI')
api_manager_space = flask_api.namespace('ran/api-manager', description='Management of the manager of OpenAPI')

api_change_host_port = api_space.parser()
api_change_host_port.add_argument('ran-host', type=str, default="0.0.0.0", required=True)
api_change_host_port.add_argument('ran-port', type=str , default="{}".format(api_port_default), required=True)

api_manager_change_host_port = api_manager_space.parser()
api_manager_change_host_port.add_argument('ran-host', type=str, default="0.0.0.0", required=True)
api_manager_change_host_port.add_argument('ran-port', type=str , default="{}".format(api_manager_port_default), required=True)


SNAP="/snap/{}/current".format(snap_name)

UPLOAD_FOLDER="/var/snap/{}/current/".format(snap_name)
PARAMETER_FOLDER="/var/snap/{}/common/".format(snap_name)
CONFIG_OPEN_API = "api_conf.json"
CONFIG_OPEN_API_MANAGER = "api_manager_conf.json"
# DIR for testing
# UPLOAD_FOLDER="/home/cigarier/Downloads/tmp/oai-ran/"
# PARAMETER_FOLDER="/home/cigarier/Downloads/tmp/oai-ran/parameters/"
# 

flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'json', 'conf'}
flask_app.config['PARAMETER_FOLDER'] = PARAMETER_FOLDER
flask_app.config['CONFIG_OPEN_API'] = CONFIG_OPEN_API
flask_app.config['CONFIG_OPEN_API_MANAGER'] = CONFIG_OPEN_API_MANAGER
flask_app.config['JSON_SORT_KEYS'] = False

## log
logger = logging.getLogger('ran.openapi')
logging.basicConfig(level=logging.DEBUG)
logger.info('Starting the manager of OpenAPI of {}'.format(snap_name))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@api_manager_space.route("/conf")
class MainClassRanConf(Resource):
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
                        'ran-host': host_ran,
                        'ran-port': port_ran
                    }
                    """
            except:
                api_config_param = {
                    'ran-host': '0.0.0.0',
                    'ran-port': api_manager_port_default
                }  
        else:
            api_config_param = {
                    'ran-host': '0.0.0.0',
                    'ran-port': api_manager_port_default
                }            
        response = make_response(jsonify(api_config_param))
        response.headers.set("Content-Type", "application/json")
        return response
        
@api_manager_space.route("/journal")
class MainClassRanApiManagerJournal(Resource):
    @api_manager_space.produces(["text"])
    def get(self):
        """
        Get the journal of the manager of OpenAPI oai-ran
        """        
        proc = subprocess.Popen(["$SNAP/run journal apidman"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 
        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

## OpenAPI of oai-ran
@api_space.route("/conf")
class MainClassRanConf(Resource):
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
                        'ran-host': host_ran,
                        'ran-port': port_ran
                    }
                    """
            except:
                api_config_param = {
                    'ran-host': '0.0.0.0',
                    'ran-port': api_port_default
                }  
        else:
            api_config_param = {
                    'ran-host': '0.0.0.0',
                    'ran-port': api_port_default
                }            
        response = make_response(jsonify(api_config_param))
        response.headers.set("Content-Type", "application/json")
        return response

@api_space.route("/start")
class MainClassRanApiRestart(Resource):
    @api_space.produces(["text"])
    @api_space.expect(api_change_host_port)
    @api_space.doc(params={
                "ran-host": "Valid IP address of oai-ran",
                "ran-port": "Valid port of oai-ran"
    })
    def put(self):
        """
        Start OpenAPI oai-ran
        WARNING: you may loose the connection if you enter non valid parameters
        """     
        args = api_change_host_port.parse_args()
        host_ran = args['ran-host']
        port_ran =  args['ran-port']
        # Write the config parameters to json file to be used when starting up the flask service
        config_file = os.path.join(flask_app.config['PARAMETER_FOLDER'], flask_app.config['CONFIG_OPEN_API'])
        with open(config_file, 'w') as f:
            config_parameters = {
                "ran-host": host_ran,
                "ran-port": port_ran
            }
            json.dump(config_parameters, f)
        str_1 = request.url
        str_2 = request.path
        current_url = str(request.url).split(request.path)
        current_url = current_url[0]
        new_url = str(current_url).split("//")
        new_url = '{}//{}:{}'.format(new_url[0], host_ran, port_ran)
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
class MainClassRanApiStop(Resource):
    @api_space.produces(["application/json"])
    def get(self):
        """
        Stop the OpenAPI oai-ran
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
class MainClassRanApiManagerRestart(Resource):
    @api_space.produces(["text"])
    @api_space.expect(api_change_host_port)
    @api_space.doc(params={
                "ran-host": "Valid IP address of oai-ran",
                "ran-port": "Valid port of oai-ran"
    })
    def put(self):
        """
        Restart the OpenAPI of oai-ran
        WARNING: you may loose the connection if you enter non valid parameters
        """     
        args = api_change_host_port.parse_args()
        host_ran = args['ran-host']
        port_ran =  args['ran-port']
        # Write the config parameters to json file to be used when starting up the flask service
        config_file = os.path.join(flask_app.config['PARAMETER_FOLDER'], flask_app.config['CONFIG_OPEN_API'])
        with open(config_file, 'w') as f:
            config_parameters = {
                "ran-host": host_ran,
                "ran-port": port_ran
            }
            json.dump(config_parameters, f)
        str_1 = request.url
        str_2 = request.path
        current_url = str(request.url).split(request.path)
        current_url = current_url[0]
        new_url = str(current_url).split("//")
        new_url = '{}//{}:{}'.format(new_url[0], host_ran, port_ran)
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
class MainClassRanApiStatus(Resource):
    @api_space.produces(["application/json"])
    def get(self):
        """
        Get the status of OpenAPI oai-ran
        """        
        proc = subprocess.Popen(["$SNAP/run status apid"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["oai-ran.api-journal"], stdout=subprocess.PIPE, shell=True)
        
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
class MainClassRanApiJournal(Resource):
    @api_space.produces(["text"])
    def get(self):
        """
        Get the journal of the OpenAPI oai-ran
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
    
    parser = argparse.ArgumentParser(description='Provide host and port for flask api of oai-ran')
        
    parser.add_argument('--ran-host', metavar='[option]', action='store', type=str,
                        required=False, default='0.0.0.0', 
                        help='Set OpenAPI-MANAGER IP address to bind to, 0.0.0.0 (default)')
    
    parser.add_argument('--ran-port', metavar='[option]', action='store', type=str,
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
                'ran-host': host_ran,
                'ran-port': port_ran
            }
            """
            print("config_param={}".format(config_param))
            flask_app.run(host=config_param["ran-host"], port=config_param["ran-port"], debug=True)
    else:
        flask_app.run(host='{}'.format(api_manager_host_default), port='{}'.format(api_manager_port_default), debug=True)

