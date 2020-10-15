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

SNAP="/snap/{}/current".format(snap_name)

UPLOAD_FOLDER="/var/snap/{}/current/".format(snap_name)
# PARAMETER_FOLDER="/var/snap/{}/common/".format(snap_name)
PARAMETER_FOLDER="/var/snap/{}/common/".format(snap_name)
CONFIG_OPEN_API = "api_conf.json"
CONFIG_OPEN_API_MANAGER = "api_manager_conf.json"
# DIR for testing
# UPLOAD_FOLDER="/home/cigarier/Downloads/tmp/oai-spgwc/"
# PARAMETER_FOLDER="/home/cigarier/Downloads/tmp/oai-spgwc/parameters/"

flask_app = Flask(__name__.split('.')[0])                                                        
flask_api = Api(flask_app, 
		  version = "1.0", 
		  title = "OpenAPI of oai-spgwc", 
		  description = "Manage the core network entity oai-spgwc throught OpenAPI ",
          ordered = True,
          terms_url= "https://www.openairinterface.org/?page_id=698",
          contact = "arouk@eurecom.fr, navid.nikaein@eurecom.fr")

spgwc_space = flask_api.namespace('spgwc', description='Management of spgwc')
db_space = flask_api.namespace('spgwc/db', description='Management of Database')
api_space = flask_api.namespace('spgwc/api', description='Management of API')
api_manager_space = flask_api.namespace('spgwc/api-manager', description='Management of the manager of OpenAPI')


upload_conf_file = spgwc_space.parser()
upload_conf_file.add_argument('file', location='files', type=FileStorage, required=False)

upload_set_conf_file = spgwc_space.parser()
upload_set_conf_file.add_argument('set-conf-file', type=inputs.boolean, default=True, required=True)
upload_set_conf_file.add_argument('config-file', type=str , required=False)
upload_set_conf_file.add_argument('file', location='files', type=FileStorage, required=False)

conf_show_file = spgwc_space.parser()
conf_show_file.add_argument('show-config-file', type=inputs.boolean, default=True, required=True)
conf_show_file.add_argument('file-name', type=str , required=False)

api_change_host_port = api_space.parser()
api_change_host_port.add_argument('spgwc-host', type=str, default="{}".format(api_host_default), required=True)
api_change_host_port.add_argument('spgwc-port', type=str , default="{}".format(api_port_default), required=True)


api_manager_change_host_port = api_manager_space.parser()
api_manager_change_host_port.add_argument('spgwc-host', type=str, default="{}".format(api_manager_host_default), required=True)
api_manager_change_host_port.add_argument('spgwc-port', type=str , default="{}".format(api_manager_port_default), required=True)

flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'json', 'conf'}
flask_app.config['PARAMETER_FOLDER'] = PARAMETER_FOLDER
flask_app.config['CONFIG_OPEN_API'] = CONFIG_OPEN_API
flask_app.config['CONFIG_OPEN_API_MANAGER'] = CONFIG_OPEN_API_MANAGER
flask_app.config['JSON_SORT_KEYS'] = False

## log
logger = logging.getLogger('spgwc.openapi')
logging.basicConfig(level=logging.DEBUG)
logger.info('Starting Open API of {}'.format(snap_name))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

"""
Example Usage:
GET: curl http://0.0.0.0:5553/spgwc/conf
POST: curl http://0.0.0.0:5553/spgwc/conf  -X POST -F file=@spgwc.conf
"""
@spgwc_space.route("/conf")
class MainClassSpgwcConf(Resource):
    @spgwc_space.produces(["text"])
    def get(self):
        """
        Get configuration file of oai-spgwc
        """
        # proc = subprocess.Popen(["oai-spgwc.conf-get"], stdout=subprocess.PIPE, shell=True)
        proc = subprocess.Popen(["$SNAP/conf echo-spgwc"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response


    @spgwc_space.doc(params={
                "set-conf-file": "Set the uploaded file (or chosen file via 'config-file') as config file if it is True, otherwise just upload the file. Default: True",
                "config-file": "Name of already existing file to set it as config file",
                "file": "upload file and set it as new config file if 'set-conf-file' is true"
    })
    @spgwc_space.expect(upload_set_conf_file)
    def post(self):
        """
        Upload/Set config file to oai-spgwc
        """
        args = upload_set_conf_file.parse_args()
        set_conf_file = args['set-conf-file']
        config_file =  args['config-file']
        uploaded_file = args['file'] 

        if (type(config_file) == type(None)) and (type(uploaded_file) == type(None)):
            status_code = 404
            return 'No File found. Either upload file or choose already existing file', status_code
        elif (type(config_file) != type(None)) and (type(uploaded_file) != type(None)):
            status_code = 404
            return 'Either only upload file or only choose already existing file, not both', status_code
        else:
            if (type(config_file) != type(None)):
                file_absolute = os.path.join(flask_app.config['UPLOAD_FOLDER'], config_file)
                if set_conf_file:
                    if allowed_file(config_file):
                        # Set alrteady existing file as config file UPLOAD_FOLDER
                        if os.path.exists(file_absolute):
                            if os.path.isfile(file_absolute):
                                logger.debug("command to set config file= {} {}".format("$SNAP/conf set-spgwc", file_absolute))
                                proc = subprocess.Popen(["$SNAP/conf set-spgwc {}".format(file_absolute)], stdout=subprocess.PIPE, shell=True)
                                (out, err) = proc.communicate()
                                
                                logger.debug("program out: {}".format(out))
                                logger.info("program out: {}".format(out))

                                logger.debug("program err: {}".format(err))
                                logger.info("program err: {}".format(err))
                                status_code = 200
                                return out.decode("utf-8"), status_code
                            else:
                                status_code = 400
                                return "Not valid file {}".format(file_absolute), status_code
                        else:
                            status_code = 400
                            return "The chosen file {} does not exist".format(file_absolute), status_code
                    else:
                        status_code = 400
                        return "The chosen file {} is not supported as config file. Choose valide config file".format(config_file), status_code
                else:
                    
                    if os.path.exists(file_absolute):            
                        if os.path.isfile(file_absolute):
                            status_code = 200
                            return "Nothing to do. Set 'set-conf-file' to true if you want to set already existing file as config file", status_code
                        else:
                            status_code = 400
                            return "The chosen file {} is not valid. Choose valid and already existing file and set 'set-conf-file' to true if you want to set it as config file".format(file_absolute), status_code    
                    else:
                        status_code = 400
                        return "The chosen file {} does not exist. Choose valid and already existing file and set 'set-conf-file' to true if you want to set it as config file".format(file_absolute), status_code    

            else:
                # Upload file and set it as config file if 'set_conf_file' is true
                config_parameters = (uploaded_file.read()).decode("utf-8")
                if uploaded_file and allowed_file(uploaded_file.filename):
                    logger.info("file={}".format(os.path.join(flask_app.config['UPLOAD_FOLDER'], secure_filename(uploaded_file.filename))))
                    file_absolute = os.path.join(flask_app.config['UPLOAD_FOLDER'], secure_filename(uploaded_file.filename))
                    with open(file_absolute, 'w') as conf_file:
                            conf_file.write(config_parameters)

                    if set_conf_file:
                        logger.debug("command to set config file= {} {}".format("$SNAP/conf set-spgwc", file_absolute))
                        proc = subprocess.Popen(["$SNAP/conf set-spgwc {}".format(file_absolute)], stdout=subprocess.PIPE, shell=True)
                        (out, err) = proc.communicate()
                        
                        logger.debug("program out: {}".format(out))
                        logger.info("program out: {}".format(out))

                        logger.debug("program err: {}".format(err))
                        logger.info("program err: {}".format(err))
                        status_code = 200
                        return out.decode("utf-8"), status_code
                    else:
                        status_code = 200
                        return 'The file {} is successfully uploaded to {}\n'.format(uploaded_file.filename, file_absolute), status_code
                else:
                    status_code = 400
                    return 'The file {} is not supported as config file\n'.format(uploaded_file.filename), status_code

@spgwc_space.route("/conf/list")
class MainClassSpgwcConfList(Resource):
    @spgwc_space.produces(["text"])
    def get(self):
        """
        Get list of configuration files of oai-spgwc
        """        
        # proc = subprocess.Popen(["oai-spgwc.conf-list"], stdout=subprocess.PIPE, shell=True)
        proc = subprocess.Popen(["$SNAP/conf ls-spgwc"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@spgwc_space.route("/conf/show")
class MainClassSpgwcConfShow(Resource):
    @spgwc_space.expect(conf_show_file)
    @spgwc_space.doc(params={"show-config-file": "Boolean value to indicate to show config file (true) of 'file-name' file (false). Default: True",
    "file-name": "File name to show if 'show-config-file'"
    
    })
    @spgwc_space.produces(["text"])
    def get(self):
        """
        Show the config of oai-spgwc
        """ 
        args = conf_show_file.parse_args()
        chosen_file = args['file-name']
        if args['show-config-file'] == False:
            
            if type(chosen_file) == type(None):
                status_code = 400
                return "Either choose file to show or set 'show-config-file' to true to show the config file", status_code  
            else:
                proc = subprocess.Popen(["$SNAP/conf cat-spgwc {}".format(chosen_file)], stdout=subprocess.PIPE, shell=True)
        else:
            if type(chosen_file) == type(None):
                # proc = subprocess.Popen(["oai-spgwc.conf-show"], stdout=subprocess.PIPE, shell=True)
                proc = subprocess.Popen(["$SNAP/conf cat-spgwc"], stdout=subprocess.PIPE, shell=True)
            else:
                status_code = 400
                return "Either choose file and set 'show-config-file' to false to show the chosen file, or set 'show-config-file' to true to show the config file", status_code      
        (out, err) = proc.communicate() 

        response = make_response(out)
        # response.headers.set("Content-Type", "json")
        response.headers.set("Content-Type", "text")
        return response


@spgwc_space.route("/init")
class MainClassSpgwcInit(Resource):
    @spgwc_space.produces(["text"])
    def get(self):
        """
        Initialize the oai-spgwc to the default values
        """        
        proc = subprocess.Popen(["$SNAP/init spgwc"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@spgwc_space.route("/status")
class MainClassSpgwcStatus(Resource):
    @spgwc_space.produces(["application/json"])
    def get(self):
        """
        Get the status of spgwc and api
        """        
        proc = subprocess.Popen(["$SNAP/run status spgwcd"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["oai-spgwc.status"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        out_decoded = out.decode("utf-8")
        out_split = (out_decoded).split('\n')
        service_status = list()
        for item in out_split:
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
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

@spgwc_space.route("/status-all")
class MainClassSpgwcStatusAll(Resource):
    @spgwc_space.produces(["application/json"])
    def get(self):
        """
        Get the status of all the services
        """        
        proc = subprocess.Popen(["$SNAP/run status-all"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["oai-spgwc.status"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

@spgwc_space.route("/start")
class MainClassSpgwcStart(Resource):
    @spgwc_space.produces(["text"])
    def get(self):
        """
        Start the service oai-spgwc in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run start spgwcd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@spgwc_space.route("/stop")
class MainClassSpgwcStop(Resource):
    @spgwc_space.produces(["text"])
    def get(self):
        """
        Stop the service oai-spgwc in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run stop spgwcd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response
@spgwc_space.route("/restart")
class MainClassSpgwcReStart(Resource):
    @spgwc_space.produces(["text"])
    def get(self):
        """
        Restart the service oai-spgwc in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run restart spgwcd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@spgwc_space.route("/journal")
class MainClassSpgwcJournal(Resource):
    @spgwc_space.produces(["text"])
    def get(self):
        """
        Get the journal of oai-spgwc
        """        
        proc = subprocess.Popen(["$SNAP/run journal spgwcd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

# API
@api_space.route("/conf")
class MainClassSpgwcConf(Resource):
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
                        'spgwc-host': host_spgwc,
                        'spgwc-port': port_spgwc
                    }
                    """
            except:
                api_config_param = {
                    'spgwc-host': api_host_default,
                    'spgwc-port': api_port_default
                }  
        else:
            api_config_param = {
                    'spgwc-host': api_host_default,
                    'spgwc-port': api_port_default
                }            
        response = make_response(jsonify(api_config_param))
        response.headers.set("Content-Type", "application/json")
        return response

@api_space.route("/journal")
class MainClassSpgwcApiJournal(Resource):
    @api_space.produces(["text"])
    def get(self):
        """
        Get the journal of API
        """        
        proc = subprocess.Popen(["$SNAP/run journal apid"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response


## Manager of OpenAPI of oai-spgwc
@api_manager_space.route("/conf")
class MainClassSpgwcConf(Resource):
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
                        'spgwc-host': host_spgwc,
                        'spgwc-port': port_spgwc
                    }
                    """
            except:
                api_config_param = {
                    'spgwc-host': api_manager_host_default,
                    'spgwc-port': api_manager_port_default
                }  
        else:
            api_config_param = {
                    'spgwc-host': api_manager_host_default,
                    'spgwc-port': api_manager_port_default
                }            
        response = make_response(jsonify(api_config_param))
        response.headers.set("Content-Type", "application/json")
        return response

@api_manager_space.route("/start")
class MainClassSpgwcApiManagerStart(Resource):
    @api_manager_space.produces(["text"])
    @api_manager_space.expect(api_manager_change_host_port)
    @api_manager_space.doc(params={
                "spgwc-host": "Valid IP address of oai-spgwc",
                "spgwc-port": "Valid port of oai-spgwc"
    })
    def put(self):
        """
        Start the manager of OpenAPI oai-spgwc
        WARNING: you may loose the connection if you enter non valid parameters
        """     
        args = api_manager_change_host_port.parse_args()
        host_spgwc = args['spgwc-host']
        port_spgwc =  args['spgwc-port']
        # Write the config parameters to json file to be used when starting up the flask service
        config_file = os.path.join(flask_app.config['PARAMETER_FOLDER'], flask_app.config['CONFIG_OPEN_API_MANAGER'])
        with open(config_file, 'w') as f:
            config_parameters = {
                "spgwc-host": host_spgwc,
                "spgwc-port": port_spgwc
            }
            json.dump(config_parameters, f)
        str_1 = request.url
        str_2 = request.path
        current_url = str(request.url).split(request.path)
        current_url = current_url[0]
        new_url = str(current_url).split("//")
        new_url = '{}//{}:{}'.format(new_url[0], host_spgwc, port_spgwc)
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
class MainClassSpgwcApiManagerStop(Resource):
    @api_manager_space.produces(["application/json"])
    def get(self):
        """
        Stop the manager of OpenAPI oai-spgwc
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
class MainClassSpgwcApiManagerRestart(Resource):
    @api_manager_space.produces(["text"])
    @api_manager_space.expect(api_manager_change_host_port)
    @api_manager_space.doc(params={
                "spgwc-host": "Valid IP address of oai-spgwc",
                "spgwc-port": "Valid port of oai-spgwc"
    })
    def put(self):
        """
        Restart the manager of OpenAPI oai-spgwc
        WARNING: you may loose the connection if you enter non valid parameters
        """     
        args = api_manager_change_host_port.parse_args()
        host_spgwc = args['spgwc-host']
        port_spgwc =  args['spgwc-port']
        # Write the config parameters to json file to be used when starting up the flask service
        config_file = os.path.join(flask_app.config['PARAMETER_FOLDER'], flask_app.config['CONFIG_OPEN_API_MANAGER'])
        with open(config_file, 'w') as f:
            config_parameters = {
                "spgwc-host": host_spgwc,
                "spgwc-port": port_spgwc
            }
            json.dump(config_parameters, f)
        str_1 = request.url
        str_2 = request.path
        current_url = str(request.url).split(request.path)
        current_url = current_url[0]
        new_url = str(current_url).split("//")
        new_url = '{}//{}:{}'.format(new_url[0], host_spgwc, port_spgwc)
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
class MainClassSpgwcApiManagerStatus(Resource):
    @api_manager_space.produces(["application/json"])
    def get(self):
        """
        Get the status of the manager of OpenAPI oai-spgwc
        """        
        proc = subprocess.Popen(["$SNAP/run status apidman"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["oai-spgwc.apiman-journal"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response
@api_manager_space.route("/journal")
class MainClassSpgwcApiManagerJournal(Resource):
    @api_manager_space.produces(["text"])
    def get(self):
        """
        Get the journal of the manager of OpenAPI oai-spgwc
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
if __name__ == "__main__":                                                     
    
    parser = argparse.ArgumentParser(description='provide host and port for flask api of oai-spgwc')
        
    parser.add_argument('--spgwc-host', metavar='[option]', action='store', type=str,
                        required=False, default='{}'.format(api_host_default), 
                        help='Set OpenAPI-SPGWC IP address to bind to, {} (default)'.format(api_host_default))
    
    parser.add_argument('--spgwc-port', metavar='[option]', action='store', type=str,
                        required=False, default='{}'.format(api_port_default), 
                        help='Set oai-spgwc port number: {} (default)'.format(api_port_default))
    args = parser.parse_args()

    config_file = '{}{}'.format(PARAMETER_FOLDER, CONFIG_OPEN_API)

    if os.path.exists(config_file) and os.path.isfile(config_file):
        with open(config_file) as f:
            config_param = json.load(f)
            """
            # config file is of the form
            config_param = {
                'spgwc-host': host_spgwc,
                'spgwc-port': port_spgwc
            }
            """
            flask_app.run(host=config_param["spgwc-host"], port=config_param["spgwc-port"], debug=True)
    else:
        flask_app.run(host='{}'.format(api_host_default), port='{}'.format(api_port_default), debug=True)

