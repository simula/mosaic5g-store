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
import os, logging, subprocess, argparse   

from werkzeug.utils import cached_property
from werkzeug.datastructures import FileStorage

from apivars import *

SNAP="/snap/{}/current".format(snap_name)

UPLOAD_FOLDER="/var/snap/{}/current/".format(snap_name)
# PARAMETER_FOLDER="/var/snap/{}/common/".format(snap_name)
PARAMETER_FOLDER="/var/snap/{}/common/".format(snap_name)
CONFIG_OPEN_API = "api_conf.json"
CONFIG_OPEN_API_MANAGER = "api_manager_conf.json"
# DIR for testing
# UPLOAD_FOLDER="/home/cigarier/Downloads/tmp/flexran/"
# PARAMETER_FOLDER="/home/cigarier/Downloads/tmp/flexran/parameters/"

flask_app = Flask(__name__.split('.')[0])                                                        
flask_api = Api(flask_app, 
		  version = "1.0", 
		  title = "OpenAPI of flexran", 
		  description = "Manage the RAN controller FlexRAN throught OpenAPI ",
          ordered = True,
          terms_url= "https://www.openairinterface.org/?page_id=698",
          contact = "arouk@eurecom.fr, navid.nikaein@eurecom.fr")

flexran_space = flask_api.namespace('flexran', description='Management of FlexRAN')
api_space = flask_api.namespace('flexran/api', description='Management of OpenAPI')
api_manager_space = flask_api.namespace('flexran/api-manager', description='Management of the manager of OpenAPI')


upload_conf_file = flexran_space.parser()
upload_conf_file.add_argument('file', location='files', type=FileStorage, required=False)


upload_set_conf_file = flexran_space.parser()
upload_set_conf_file.add_argument('nbi-port', type=str, default="9999", required=False)
upload_set_conf_file.add_argument('sbi-port', type=str, default="2210", required=False)


conf_show_file = flexran_space.parser()
conf_show_file.add_argument('show-config-file', type=inputs.boolean, default=True, required=True)
conf_show_file.add_argument('file-name', type=str , required=False)



api_change_host_port = api_space.parser()
api_change_host_port.add_argument('api-flexran-host', type=str, default="{}".format(api_host_default), required=True)
api_change_host_port.add_argument('api-flexran-port', type=str , default="{}".format(api_port_default), required=True)


api_manager_change_host_port = api_manager_space.parser()
api_manager_change_host_port.add_argument('api-manager-flexran-host', type=str, default="{}".format(api_manager_host_default), required=True)
api_manager_change_host_port.add_argument('api-manager-flexran-port', type=str , default="{}".format(api_manager_port_default), required=True)

flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'json', 'conf'}
flask_app.config['PARAMETER_FOLDER'] = PARAMETER_FOLDER
flask_app.config['CONFIG_OPEN_API'] = CONFIG_OPEN_API
flask_app.config['CONFIG_OPEN_API_MANAGER'] = CONFIG_OPEN_API_MANAGER
flask_app.config['JSON_SORT_KEYS'] = False

## log
logger = logging.getLogger('flexran.openapi')
logging.basicConfig(level=logging.DEBUG)
logger.info('Starting OpenAPI of {}'.format(snap_name))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


"""
Example Usage:
GET: curl http://0.0.0.0:5530/flexran/ports
POST: curl -X POST "http://0.0.0.0:5530/flexran/ports?nbi-port=9999&sbi-port=2210"
"""
@flexran_space.route("/ports")
class MainClassFlexranConf(Resource):
    @flexran_space.produces(["application/json"])
    def get(self):
        """
        Get NBI and SBI ports of FlexRAN
        """
        # proc = subprocess.Popen(["flexran.ports"], stdout=subprocess.PIPE, shell=True)
        proc = subprocess.Popen(["$SNAP/conf ports"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        service_status = serialize_flexflexran_ports(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response


    @flexran_space.doc(params={
                "nbi-port": "nbi port",
                "sbi-port": "sbi port"
    })
    @flexran_space.expect(upload_set_conf_file)
    def post(self):
        """
        Set nbi and/or sbi ports
        """
        args = upload_set_conf_file.parse_args()
        nbi_port = args['nbi-port']
        sbi_port = args['sbi-port']
        print("nbi_port={}".format(nbi_port))
        print("sbi_port={}".format(sbi_port))
        if (type(nbi_port) == type(None)) and (type(sbi_port) == type(None)):
            status_code = 200
            return 'No SBI neither NBI ports provided. Nothing to do', status_code
        else:
            message_setting_ports = list()
            if (type(nbi_port) != type(None)):
                # proc = subprocess.Popen(["flexran.nbi-port {}".format(nbi_port)], stdout=subprocess.PIPE, shell=True)
                proc = subprocess.Popen(["$SNAP/conf nbi {}".format(nbi_port)], stdout=subprocess.PIPE, shell=True)
                (out, err) = proc.communicate() 

                nbi_setting_ports = {
                    "nbi-port":{
                        "notes": str(out.decode("utf-8"))
                    }
                }
                message_setting_ports.append(nbi_setting_ports)
                
                
            if (type(sbi_port) != type(None)):
                # proc = subprocess.Popen(["flexran.sbi-port {}".format(sbi_port)], stdout=subprocess.PIPE, shell=True)
                proc = subprocess.Popen(["$SNAP/conf sbi {}".format(sbi_port)], stdout=subprocess.PIPE, shell=True)
                (out, err) = proc.communicate() 

                # message_setting_ports["sbi-port"] = str(out.decode("utf-8"))
                sbi_setting_ports = {
                    "sbi-port":{
                        "notes": str(out.decode("utf-8"))
                    }
                }
                message_setting_ports.append(sbi_setting_ports)

            response = make_response(jsonify(message_setting_ports))
            response.headers.set("Content-Type", "application/json")
            return response


@flexran_space.route("/init")
class MainClassFlexranInit(Resource):
    @flexran_space.produces(["application/json"])
    def get(self):
        """
        Initialize the FlexRAN to the default values
        """        
        # proc = subprocess.Popen(["sudo flexran.init"], stdout=subprocess.PIPE, shell=True)
        proc = subprocess.Popen(["$SNAP/run init"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 
        service_status = serialize_flexflexran_ports(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

@flexran_space.route("/status")
class MainClassFlexranStatus(Resource):
    @flexran_space.produces(["application/json"])
    def get(self):
        """
        Get the status of FlexRAN
        """        
        proc = subprocess.Popen(["$SNAP/run status flexrand"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["flexran.status"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

@flexran_space.route("/status-all")
class MainClassFlexranStatusAll(Resource):
    @flexran_space.produces(["application/json"])
    def get(self):
        """
        Get the status of all the services
        """        
        proc = subprocess.Popen(["$SNAP/run status-all"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["flexran.status"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

@flexran_space.route("/start")
class MainClassFlexranStart(Resource):
    @flexran_space.produces(["application/json"])
    def get(self):
        """
        Start the service FlexRAN in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run start flexrand"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

        # response = make_response(out)
        # response.headers.set("Content-Type", "text")
        # return response

@flexran_space.route("/stop")
class MainClassFlexranStop(Resource):
    @flexran_space.produces(["application/json"])
    def get(self):
        """
        Stop the service FlexRAN
        """        
        proc = subprocess.Popen(["$SNAP/run stop flexrand"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

        # response = make_response(out)
        # response.headers.set("Content-Type", "text")
        # return response
@flexran_space.route("/restart")
class MainClassFlexranReStart(Resource):
    @flexran_space.produces(["application/json"])
    def get(self):
        """
        Restart the service FlexRAN in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run restart flexrand"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

@flexran_space.route("/journal")
class MainClassFlexranJournal(Resource):
    @flexran_space.produces(["text"])
    def get(self):
        """
        Get the journal of FlexRAN
        """        
        proc = subprocess.Popen(["$SNAP/run journal flexrand"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

# API
@api_space.route("/conf")
class MainClassApiConf(Resource):
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
                        'api-flexran-host': host_ran,
                        'api-flexran-port': port_ran
                    }
                    """
            except:
                api_config_param = {
                    'api-flexran-host': api_host_default,
                    'api-flexran-port': api_port_default
                }  
        else:
            api_config_param = {
                    'api-flexran-host': api_host_default,
                    'api-flexran-port': api_port_default
                }            
        response = make_response(jsonify(api_config_param))
        response.headers.set("Content-Type", "application/json")
        return response

@api_space.route("/journal")
class MainClassApiJournal(Resource):
    @api_space.produces(["text"])
    def get(self):
        """
        Get the journal of OpenAPI
        """        
        proc = subprocess.Popen(["$SNAP/run journal apid"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 
        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response



## Manager of OpenAPI of flexran
@api_manager_space.route("/conf")
class MainClassApiManagerConf(Resource):
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
                        'api-manager-flexran-host': host_ran,
                        'api-manager-flexran-port': port_ran
                    }
                    """
            except:
                api_config_param = {
                    'api-manager-flexran-host': api_manager_host_default,
                    'api-manager-flexran-port': api_manager_port_default
                }  
        else:
            api_config_param = {
                    'api-manager-flexran-host': api_manager_host_default,
                    'api-manager-flexran-port': api_manager_port_default
                }            
        response = make_response(jsonify(api_config_param))
        response.headers.set("Content-Type", "application/json")
        return response

@api_manager_space.route("/start")
class MainClassApiManagerStart(Resource):
    @api_manager_space.produces(["text"])
    @api_manager_space.expect(api_manager_change_host_port)
    @api_manager_space.doc(params={
                "api-manager-flexran-host": "Valid IP address of flexran",
                "api-manager-flexran-port": "Valid port of flexran"
    })
    def put(self):
        """
        Start the manager of OpenAPI flexran
        WARNING: you may loose the connection if you enter non valid parameters
        """     
        args = api_manager_change_host_port.parse_args()
        host_ran = args['api-manager-flexran-host']
        port_ran =  args['api-manager-flexran-port']
        # Write the config parameters to json file to be used when starting up the flask service
        config_file = os.path.join(flask_app.config['PARAMETER_FOLDER'], flask_app.config['CONFIG_OPEN_API_MANAGER'])
        with open(config_file, 'w') as f:
            config_parameters = {
                "api-manager-flexran-host": host_ran,
                "api-manager-flexran-port": port_ran
            }
            json.dump(config_parameters, f)
        str_1 = request.url
        str_2 = request.path
        current_url = str(request.url).split(request.path)
        current_url = current_url[0]
        new_url = str(current_url).split("//")
        new_url = '{}//{}:{}'.format(new_url[0], host_ran, port_ran)
        proc = subprocess.Popen(["$SNAP/run start apidman"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        service_status = serialize_service_status(out)

        message = {
            'openapi': current_url,
            'openapi-manager': new_url,
            'note': "OpenAPI manager of {} will be available at {}".format(snap_name,new_url),
            'status': service_status,
            'error': str(err)
        }
        response = make_response(message)
        response.headers.set("Content-Type", "text")
        return response
@api_manager_space.route("/stop")
class MainClassApiManagerStop(Resource):
    @api_manager_space.produces(["application/json"])
    def get(self):
        """
        Stop the manager of OpenAPI FlexRAN
        """        
        proc = subprocess.Popen(["$SNAP/run stop apidman"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

        # response = make_response(out)
        # response.headers.set("Content-Type", "text")
        # return response

@api_manager_space.route("/restart")
class MainClassApiManagerRestart(Resource):
    @api_manager_space.produces(["text"])
    @api_manager_space.expect(api_manager_change_host_port)
    @api_manager_space.doc(params={
                "api-manager-flexran-host": "Valid IP address of flexran",
                "api-manager-flexran-port": "Valid port of flexran"
    })
    def put(self):
        """
        Restart the manager of OpenAPI flexran
        WARNING: you may loose the connection if you enter non valid parameters
        """     
        args = api_manager_change_host_port.parse_args()
        host_ran = args['api-manager-flexran-host']
        port_ran =  args['api-manager-flexran-port']
        # Write the config parameters to json file to be used when starting up the flask service
        config_file = os.path.join(flask_app.config['PARAMETER_FOLDER'], flask_app.config['CONFIG_OPEN_API_MANAGER'])
        with open(config_file, 'w') as f:
            config_parameters = {
                "api-manager-flexran-host": host_ran,
                "api-manager-flexran-port": port_ran
            }
            json.dump(config_parameters, f)
        str_1 = request.url
        str_2 = request.path
        current_url = str(request.url).split(request.path)
        current_url = current_url[0]
        new_url = str(current_url).split("//")
        new_url = '{}//{}:{}'.format(new_url[0], host_ran, port_ran)
        proc = subprocess.Popen(["$SNAP/run restart apidman"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        service_status = serialize_service_status(out)
        message = {
            'openapi': current_url,
            'openapi-manager': new_url,
            'note': "OpenAPI manager of {} will be available at {}".format(snap_name,new_url),
            'status': service_status,
            'error': str(err)
        }
        response = make_response(message)
        response.headers.set("Content-Type", "text")
        return response

@api_manager_space.route("/status")
class MainClassApiManagerStatus(Resource):
    @api_manager_space.produces(["application/json"])
    def get(self):
        """
        Get the status of the manager of OpenAPI FlexRAN
        """        
        proc = subprocess.Popen(["$SNAP/run status apidman"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["flexran.apiman-journal"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response
@api_manager_space.route("/journal")
class MainClassApiManagerJournal(Resource):
    @api_manager_space.produces(["text"])
    def get(self):
        """
        Get the journal of the manager of OpenAPI FlexRAN
        """        
        proc = subprocess.Popen(["$SNAP/run journal apidman"], stdout=subprocess.PIPE, shell=True)
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

def serialize_flexflexran_ports(status):
    status_decoded = status.decode("utf-8")
    status_split = (status_decoded).split('\n')
    service_status = list()
    service_status_found = False
    nbi_port = None
    sbi_port = None
    for item in status_split:
        if ('SBI_PORT' in item):
            print("sbi={}".format(item))
            item_out = item.split(":")
            sbi_port = item_out[1].split(" ")
            sbi_port = sbi_port[len(sbi_port)-1]
        if ('NBI_PORT' in item):
            print("nbi={}".format(item))
            item_out = item.split(":")
            nbi_port = item_out[1].split(" ")
            nbi_port = nbi_port[len(nbi_port)-1]
        if service_status_found:
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
                    "notes": current_service_status[3],
                    "nbi-port": nbi_port,
                    "sbi-port": sbi_port
                }
                service_status.append(svc_stat)
        if ('Service' in item) and ('Startup' in item) and ('Current' in item) and ('Notes' in item):
            service_status_found = True
    if len(service_status) == 0:
        svc_stat = {
            "nbi-port": nbi_port,
            "sbi-port": sbi_port
        }
        service_status.append(svc_stat)
    return service_status
if __name__ == "__main__":                                                     
    
    parser = argparse.ArgumentParser(description='provide host and port for flask api of FlexRAN')
        
    parser.add_argument('--api-flexran-host', metavar='[option]', action='store', type=str,
                        required=False, default='{}'.format(api_host_default), 
                        help='Set OpenAPI-FlexRAN IP address to bind to, {} (default)'.format(api_host_default))
    
    parser.add_argument('--api-flexran-port', metavar='[option]', action='store', type=str,
                        required=False, default='{}'.format(api_port_default), 
                        help='Set flexran port number: {} (default)'.format(api_port_default))
    args = parser.parse_args()

    config_file = '{}{}'.format(PARAMETER_FOLDER, CONFIG_OPEN_API)

    if os.path.exists(config_file) and os.path.isfile(config_file):
        with open(config_file) as f:
            config_param = json.load(f)
            """
            # config file is of the form
            config_param = {
                'api-flexran-host': host_ran,
                'api-flexran-port': port_ran
            }
            """
            flask_app.run(host=config_param["api-flexran-host"], port=config_param["api-flexran-port"], debug=True)
    else:
        flask_app.run(host='{}'.format(api_host_default), port='{}'.format(api_port_default), debug=True)

