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

snap_name = "oai-hss"

api_host_default = '0.0.0.0'
api_port_default = 5551

api_manager_host_default = '0.0.0.0'
api_manager_port_default = 6661

UPLOAD_FOLDER="/var/snap/{}/current/".format(snap_name)
# PARAMETER_FOLDER="/var/snap/{}/common/".format(snap_name)
PARAMETER_FOLDER="/var/snap/{}/common/".format(snap_name)
CONFIG_OPEN_API = "api_conf.json"
CONFIG_OPEN_API_MANAGER = "api_manager_conf.json"
# DIR for testing
# UPLOAD_FOLDER="/home/cigarier/Downloads/tmp/oai-hss/"
# PARAMETER_FOLDER="/home/cigarier/Downloads/tmp/oai-hss/parameters/"
# 

flask_app = Flask(__name__.split('.')[0])                                                        
flask_api = Api(flask_app, 
		  version = "1.0", 
		  title = "OpenAPI of oai-hss", 
		  description = "Manage the core network entity oai-hss throught OpenAPI ",
          ordered = True,
          terms_url= "https://www.openairinterface.org/?page_id=698",
          contact = "arouk@eurecom.fr, navid.nikaein@eurecom.fr")

hss_space = flask_api.namespace('hss', description='Management of hss')
db_space = flask_api.namespace('hss/db', description='Management of Database')
api_space = flask_api.namespace('hss/api', description='Management of API')
api_manager_space = flask_api.namespace('hss/api-manager', description='Management of the manager of OpenAPI')


upload_json_file = hss_space.parser()
upload_json_file.add_argument('file', location='files', type=FileStorage, required=False)


upload_set_conf_file = hss_space.parser()
upload_set_conf_file.add_argument('set-conf-file', type=inputs.boolean, default=True, required=True)
upload_set_conf_file.add_argument('config-file', type=str , required=False)
upload_set_conf_file.add_argument('file', location='files', type=FileStorage, required=False)


conf_show_file = hss_space.parser()
conf_show_file.add_argument('show-config-file', type=inputs.boolean, default=True, required=True)
conf_show_file.add_argument('file-name', type=str , required=False)

api_change_host_port = api_space.parser()
api_change_host_port.add_argument('hss-host', type=str, default="{}".format(api_host_default), required=True)
api_change_host_port.add_argument('hss-port', type=str , default="{}".format(api_port_default), required=True)


api_manager_change_host_port = api_manager_space.parser()
api_manager_change_host_port.add_argument('hss-host', type=str, default="{}".format(api_manager_host_default), required=True)
api_manager_change_host_port.add_argument('hss-port', type=str , default="{}".format(api_manager_port_default), required=True)

# model = flask_api.model('Name Model', 
# 				  {'name': fields.String(required = True, 
#     					  				 description="Name of the person", 
#     					  				 help="Name cannot be blank.")})

flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'json', 'conf'}
flask_app.config['PARAMETER_FOLDER'] = PARAMETER_FOLDER
flask_app.config['CONFIG_OPEN_API'] = CONFIG_OPEN_API
flask_app.config['CONFIG_OPEN_API_MANAGER'] = CONFIG_OPEN_API_MANAGER
flask_app.config['JSON_SORT_KEYS'] = False

# database ip
dbip="172.17.0.2"

## log
logger = logging.getLogger('hss.openapi')
logging.basicConfig(level=logging.DEBUG)
logger.info('Starting Open API of {}'.format(snap_name))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


model_add_mme = hss_space.model('Accepted values of adding new MME', {
    'mme-id': fields.Integer(default=4),
    'mme-hostname': fields.String(description='mme hostname concatenated with the realm', default='ubuntu.openair5G.eur'),
    'realm': fields.String(description='The realm of your network', default='openair5G.eur'),
    'cluster-ip-address': fields.String(description='The ip address of your clster Cassandra', default='172.17.0.2'),
    'mme-isdn': fields.Integer(description='MME ISDN', default=208),
    'ue-reachability': fields.Boolean(description='UE reachability', default=False)
    }
)

model_add_users = hss_space.model('Accepted values of adding new Users', {
    'help': fields.Boolean(description='Getting help of how to add users', default=False),
    'cluster-ip-address': fields.String(description='The ip address of your clster Cassandra', default='172.17.0.2'),
    'read-file': fields.String(description='read list of IMSI configuration from JSON file'),
    'imsi': fields.String(description='single IMSI, IMSI range of form `start-end` or IMSI regex to match IMSIs in the database. Multiple IMSIs are handled in order. For a new IMSI, will create entry', default="208950000000001-208950000000010"),
    'apn': fields.String(description='The realm of your network', default='openair5G.eur'),
    'apn2': fields.String(description='The realm of your network', default='internet'),
    'access-restriction': fields.String(description='Access Restriction', default='41'),
    "mme-id": fields.Integer(description='MME ID', default=3),
    "key":fields.String(description='LTE K', default='8baf473f2f8fd09487cccbd7097c6862 for OP 1111...'),
    "mme-hostname": fields.String(description='MME Host', default='ubuntu.openair5G.eur'),
    "msisdn": fields.String(description='MSISDN or MSISDN range of form `start-end` (default: single 33663000021). Multiple MSISDN are handled in order. If multiple MSISDN are given, their number needs to match the number of IMSIs', default='33663000021'),
    "opc":fields.String(description='LTE OPc', default='8e27b6af0e692e750f32667a3b14605d for OP 1111...'),
    
    "sqn":fields.Integer(description='USIM SQN', default=21),
    "realm": fields.String(description=' Realm of the CN', default='openair5G.eur'),
    "rand":fields.String(description=' Realm of the CN', default='2683b376d1056746de3b254012908e0e'),
    "static-ue-ipv4-allocation": fields.String(description='UE IPv4 address statically allocated by HSS (not set if not provided)', default=''),
    "static-ue-ipv6-allocation": fields.String(description='UE IPv6 address statically allocated by HSS (not set if not provided)', default=''),
    "database-reset": fields.Boolean(description='reset the DB', default=False)
    }
)

"""
Example Usage:
GET: usage example: curl http://0.0.0.0:5551/hss/mme
POST: usage example: curl http://0.0.0.0:5551/hss/mme  -X POST -F file=@hss_add_mme_param.json
"""
@hss_space.route("/mme")
class MainClassHssMme(Resource):
    @hss_space.produces(["text"])
    def get(self):
        """
        Get list of registered mme in hss
        """        
        # proc = subprocess.Popen(["oai-hss.dump-mme"], stdout=subprocess.PIPE, shell=True)
        proc = subprocess.Popen(["$SNAP/run dump-mme"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response
    
    @hss_space.expect(upload_json_file, model_add_mme)
    @hss_space.doc(params={"file": "Upload json file with the requireds fields (see below an example) to add one or more MME to OAI-HSS"})
    def post(self):
        """
        Add mme to oai-hss
        """
        status_code = 200
        args = upload_json_file.parse_args()
        uploaded_file = args['file']
        if type(uploaded_file) == type(None):
            status_code = 200
            return 'No Json File found', status_code
        else:
            """
            Expected fields for adding mme with example values
            {
                "mme-id": "4",
                "mme-hostname": "ubuntu.openair5G.eur",
                "realm": "openair5G.eur",
                "cluster-ip-address": "192.168.1.223",
                "mme-isdn": "208",
                "ue-reachability": 1,
                "database-reset": "no"
            }
            """
            json_parameters = (uploaded_file.read()).decode("utf-8")
            json_parameters = json.loads(json_parameters)
            
            message = dict()
            counter = 0 
            for item in json_parameters:
                command_base = "$SNAP/run add-mme"
                command = command_base
                logger.debug("command_base={}".format(command))
                error_param = False
                try:
                    mme_id = item["mme-id"]
                    if isinstance(mme_id, int):
                        command = '{} --id {}'.format(command, mme_id)
                    else:
                        message[counter] = "Invalid value {} for MME Id. It should be integer value".format(mme_id)
                        error_param = True
                except:
                    pass
                
                try:
                    mme_hostname = item["mme-hostname"]
                    if mme_hostname != "":
                        command = '{} --mme-identity {}'.format(command, mme_hostname)
                except:
                    pass
                
                try:
                    realm = item["realm"]
                    if realm != "":
                        command = '{} --realm {}'.format(command, realm)
                except:
                    pass
                try:
                    cluster_ip_address = item["cluster-ip-address"]
                    if cluster_ip_address != "":
                        command = '{} --cassandra-cluster {}'.format(command, cluster_ip_address)
                except:
                    pass
                try:
                    mme_isdn = item["mme-isdn"]
                    if isinstance(mme_isdn, int):
                        command = '{} --mme-isdn {}'.format(command, mme_isdn)
                    else:
                        message[counter] = "Invalid value {} for mme-isdn. It should be integer value".format(mme_isdn)
                        error_param = True
                except:
                    pass
                try:
                    ue_reachability = item["ue-reachability"]
                    if isinstance(mme_isdn, int):
                        command = '{} --ue-reachability {}'.format(command, ue_reachability)
                    else:
                        message[counter] = "Invalid value {} for ue-reachability. It should be integer value".format(ue_reachability)
                        error_param = True
                except:
                    pass
                try:
                    database_reset = item["database-reset"]
                    if type(database_reset)==type(True):
                        if database_reset:
                            command = '{} --truncate'.format(command)
                    else:
                        message[counter] = "Invalid value {} for database-reset. It should be boolean value".format(ue_reachability)
                        error_param = True
                except:
                    pass
                
                if command_base != command:
                    if not error_param:
                        logger.debug("command to execute: {}".format(command))
                        logger.info("command to execute: {}".format(command))
                        proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
                        (out, err) = proc.communicate()
                        
                        logger.debug("command out: {}".format(out))
                        logger.info("command out: {}".format(out))

                        logger.debug("command err: {}".format(err))
                        logger.info("command err: {}".format(err))
                        
                        message[counter] = out.decode("utf-8")
                else:
                    message[counter] = "Nothing to add"
                    logger.info
                counter += 1
            status_code = 200
            return message, status_code


"""
Example Usage:
GET: curl http://0.0.0.0:5551/hss/conf
POST: curl http://0.0.0.0:5551/hss/conf  -X POST -F file=@hss_rel14.json
"""
@hss_space.route("/conf")
class MainClassHssConf(Resource):
    @hss_space.produces(["text"])
    def get(self):
        """
        Get configuration file of oai-hss
        """
        # proc = subprocess.Popen(["oai-hss.conf-get"], stdout=subprocess.PIPE, shell=True)
        proc = subprocess.Popen(["$SNAP/conf echo-hss"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response


    @hss_space.doc(params={
                "set-conf-file": "Set the uploaded file (or chosen file via 'config-file') as config file if it is True, otherwise just upload the file. Default: True",
                "config-file": "Name of already existing file to set it as config file",
                "file": "upload file and set it as new config file if 'set-conf-file' is true"
    })
    @hss_space.expect(upload_set_conf_file)
    def post(self):
        """
        Upload/Set config file to oai-hss
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
                                logger.debug("command to set config file= {} {}".format("$SNAP/conf set-hss", file_absolute))
                                proc = subprocess.Popen(["$SNAP/conf set-hss {}".format(file_absolute)], stdout=subprocess.PIPE, shell=True)
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
                        logger.debug("command to set config file= {} {}".format("$SNAP/conf set-hss", file_absolute))
                        proc = subprocess.Popen(["$SNAP/conf set-hss {}".format(file_absolute)], stdout=subprocess.PIPE, shell=True)
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


"""
Example Usage: 
GET: curl http://0.0.0.0:5551/hss/users
POST: curl http://0.0.0.0:5551/hss/users  -X POST -F file=@hss_add_users_param.json
"""
@hss_space.route("/users")
class MainClassHssUsers(Resource):
    @hss_space.produces(["text"])
    def get(self):
        """
        Get list of Users
        """        
        # proc = subprocess.Popen(["oai-hss.dump-users"], stdout=subprocess.PIPE, shell=True)
        proc = subprocess.Popen(["$SNAP/run dump-users"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response
    
    @hss_space.expect(upload_json_file, model_add_users)
    @hss_space.doc(params={"file": "Upload json file with the requireds fields (see below an example) to add one or more MME to OAI-HSS"})
    def post(self):
        """
        Add mme to oai-hss
        """
        status_code = 200
        args = upload_json_file.parse_args()
        uploaded_file = args['file']  # This is FileStorage instance
        if type(uploaded_file) == type(None):
            status_code = 200
            return 'No Json File found', status_code
        else:
            try:
                json_parameters = (uploaded_file.read()).decode("utf-8")
                json_parameters = json.loads(json_parameters)
                """
                Expected fiels for adding mme with example values
                {
                    "help": false,
                    "cluster-ip-address": "192.168.1.223",
                    "read-file": "",
                    "imsi": "208950000000001-208950000000010",
                    "apn":"oai.ipv4",
                    "apn2":"oai.openair5G.eur",
                    "access-restriction": 41,
                    "mme-id": "3",
                    "key":"8baf473f2f8fd09487cccbd7097c6862",
                    "mme-hostname": "cigarier.openair5G.eur",
                    "msisdn":"33663000021",
                    "opc":"8e27b6af0e692e750f32667a3b14605d",
                    "sqn":21,
                    "realm": "openair5G.eur",
                    "rand":"2683b376d1056746de3b254012908e0e",
                    "static-ue-ipv4-allocation": "",
                    "static-ue-ipv6-allocation": "",
                    "database-reset": false
                }
                """
                message = dict()
                counter = 0 
                for item in json_parameters:
                    command_base = "$SNAP/run add-users"
                    command = command_base
                    error_param = False
                    help_param = False
                    
                    try:
                        help_param = item["help"]
                        if type(help_param)==type(True):
                            if help_param:
                                command = '{} --help'.format(command)
                        else:
                            message[counter] = "Invalid value {} for help. It should be boolean value".format(help_param)
                            error_param = True
                    except:
                        pass
                    if not help_param:
                        try:
                            cluster_ip_address = item["cluster-ip-address"]
                            if cluster_ip_address != "":
                                command = '{} --cassandra-cluster {}'.format(command, cluster_ip_address)
                        except:
                            pass

                        try:
                            read_file = item["read-file"]
                            if read_file != "":
                                command = '{} --read-file {}'.format(command, read_file)
                        except:
                            pass
                    
                        try:
                            imsi = item["imsi"]
                            if imsi != "":
                                command = '{} --imsi {}'.format(command, imsi)
                        except:
                            pass
                        
                        try:
                            apn = item["apn"]
                            if apn != "":
                                command = '{} --apn {}'.format(command, apn)
                        except:
                            pass
                        
                        try:
                            apn2 = item["apn2"]
                            if apn2 != "":
                                command = '{} --apn2 {}'.format(command, apn2)
                        except:
                            pass

                        try:
                            access_restriction = item["access-restriction"]
                            if access_restriction != "":
                                command = '{} --access-restriction {}'.format(command, int(access_restriction))
                        except:
                            pass
                            
                        try:
                            mme_id = item["mme-id"]
                            if isinstance(mme_id, int):
                                command = '{} --mme-id {}'.format(command, mme_id)
                            else:
                                message[counter] = "Invalid value {} for mme id. It should be integer value".format(mme_id)
                                error_param = True
                        except:
                            pass

                        try:
                            key_param = item["key"]
                            if key_param != "":
                                command = '{} --key {}'.format(command, key_param)
                        except:
                            pass
                            
                        try:
                            mme_hostname = item["mme-hostname"]
                            if mme_hostname != "":
                                command = '{} --mme-identity {}'.format(command, mme_hostname)
                        except:
                            pass

                        try:
                            msisdn = item["msisdn"]
                            if msisdn != "":
                                command = '{} --msisdn {}'.format(command, msisdn)
                        except:
                            pass
                        
                        try:
                            opc = item["opc"]
                            if opc != "":
                                command = '{} --opc {}'.format(command, opc)
                        except:
                            pass

                        try:
                            sqn_param = item["sqn"]
                            if isinstance(sqn_param, int):
                                command = '{} --sqn {}'.format(command, sqn_param)
                            else:
                                message[counter] = "Invalid value {} for sqn. It should be integer value".format(sqn_param)
                                error_param = True
                        except:
                            pass

                        try:
                            realm = item["realm"]
                            if realm != "":
                                command = '{} --realm {}'.format(command, realm)
                        except:
                            pass

                        try:
                            rand = item["rand"]
                            if rand != "":
                                command = '{} --rand {}'.format(command, rand)
                        except:
                            pass

                        try:
                            static_ue_ipv4_allocation = item["static-ue-ipv4-allocation"]
                            if static_ue_ipv4_allocation != "":
                                command = '{} --static-ue-ipv4-allocation {}'.format(command, static_ue_ipv4_allocation)
                        except:
                            pass
                            
                        try:
                            static_ue_ipv6_allocation = item["static-ue-ipv6-allocation"]
                            if static_ue_ipv6_allocation != "":
                                command = '{} --static-ue-ipv6-allocation {}'.format(command, static_ue_ipv6_allocation)
                        except:
                            pass

                        try:
                            database_reset = item["database-reset"]
                            if type(database_reset)==type(True):
                                if database_reset:
                                    command = '{} --truncate'.format(command)
                            else:
                                message[counter] = "Invalid value {} for database-reset. It should be boolean value".format(database_reset)
                                error_param = True
                        except:
                            pass
                    
                    if command_base != command:
                        if not error_param:
                            logger.info("command to execute: {}".format(command))
                            logger.debug("command to execute: {}".format(command))
                            proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
                            (out, err) = proc.communicate()
                            logger.debug("command out: {}".format(out))
                            logger.info("command out: {}".format(out))
                            
                            logger.debug("command err: {}".format(err))
                            logger.info("command err: {}".format(err))

                            message[counter] = out.decode("utf-8")
                    else:
                        message[counter] = "Nothing to add"
                    counter += 1
                status_code = 200
                return message, status_code
            except:
                status_code = 200
                return 'Error while trying to read the json file', status_code

  
@hss_space.route("/conf/list")
class MainClassHssConfList(Resource):
    @hss_space.produces(["text"])
    def get(self):
        """
        Get list of configuration files of oai-hss
        """        
        # proc = subprocess.Popen(["oai-hss.conf-list"], stdout=subprocess.PIPE, shell=True)
        proc = subprocess.Popen(["$SNAP/conf ls-hss"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@hss_space.route("/conf/show")
class MainClassHssConfShow(Resource):
    @hss_space.expect(conf_show_file)
    @hss_space.doc(params={"show-config-file": "Boolean value to indicate to show config file (true) of 'file-name' file (false). Default: True",
                        "file-name": "File name to show if 'show-config-file'"
    
    })
    @hss_space.produces(["text"])
    def get(self):
        """
        Show the config of oai-hss
        """ 
        args = conf_show_file.parse_args()
        chosen_file = args['file-name']
        if args['show-config-file'] == False:
            
            if type(chosen_file) == type(None):
                status_code = 400
                return "Either choose file to show or set 'show-config-file' to true to show the config file", status_code  
            else:
                proc = subprocess.Popen(["$SNAP/conf cat-hss {}".format(chosen_file)], stdout=subprocess.PIPE, shell=True)
        else:
            if type(chosen_file) == type(None):
                # proc = subprocess.Popen(["oai-hss.conf-show"], stdout=subprocess.PIPE, shell=True)
                proc = subprocess.Popen(["$SNAP/conf cat-hss"], stdout=subprocess.PIPE, shell=True)
            else:
                status_code = 400
                return "Either choose file and set 'show-config-file' to false to show the chosen file, or set 'show-config-file' to true to show the config file", status_code      
        (out, err) = proc.communicate() 

        response = make_response(out)
        # response.headers.set("Content-Type", "json")
        response.headers.set("Content-Type", "text")
        return response


@db_space.route("/ip")
class MainClassHssDbIp(Resource):
    @db_space.produces(["text"])
    def get(self):
        """
        Get the ip address of the database
        """        
        proc = subprocess.Popen(["$SNAP/run db-ip"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@db_space.route("/probe")
class MainClassHssDbProbe(Resource):
    # @db_space.produces(["text"])
    def get(self):
        """
        Check whether the database is alive
        """        
        # proc = subprocess.Popen(["python3 probe-db.py"], stdout=subprocess.PIPE, shell=True)
        proc = subprocess.Popen(["$SNAP/run probe-db"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 
        response = make_response(out)
        response.headers.set("Content-Type", "json")
        return response

@db_space.route("/clean")
class MainClassHssDbClean(Resource):
    @db_space.produces(["text"])
    def get(self):
        """
        Clean the database
        """        
        proc = subprocess.Popen(["$SNAP/run clean-db"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@db_space.route("/reset")
class MainClassHssDbReset(Resource):
    @db_space.produces(["text"])
    def get(self):
        """
        Reset the database
        """        
        proc = subprocess.Popen(["$SNAP/run reset-db"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@hss_space.route("/init")
class MainClassHssInit(Resource):
    @hss_space.produces(["text"])
    def get(self):
        """
        Initialize the oai-hss to the default values
        """        
        proc = subprocess.Popen(["$SNAP/init hss"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@hss_space.route("/status")
class MainClassHssStatus(Resource):
    @hss_space.produces(["application/json"])
    def get(self):
        """
        Get the status of oai-hss
        """        
        proc = subprocess.Popen(["$SNAP/run status hssd"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["oai-hss.status"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

@hss_space.route("/status-all")
class MainClassHssStatusAll(Resource):
    @hss_space.produces(["application/json"])
    def get(self):
        """
        Get the status of all the services
        """        
        proc = subprocess.Popen(["$SNAP/run status-all"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["oai-hss.status"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

@hss_space.route("/start")
class MainClassHssStart(Resource):
    @hss_space.produces(["application/json"])
    def get(self):
        """
        Start the service oai-hss in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run start hssd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

@hss_space.route("/stop")
class MainClassHssStop(Resource):
    @hss_space.produces(["application/json"])
    def get(self):
        """
        Stop the service oai-hss in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run stop hssd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response
@hss_space.route("/restart")
class MainClassHssReStart(Resource):
    @hss_space.produces(["application/json"])
    def get(self):
        """
        Restart the service oai-hss in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run restart hssd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response

@hss_space.route("/journal")
class MainClassHssJournal(Resource):
    @hss_space.produces(["text"])
    def get(self):
        """
        Get the journal of oai-hss
        """        
        proc = subprocess.Popen(["$SNAP/run journal hssd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

# API
@api_space.route("/conf")
class MainClassHssConf(Resource):
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
                        'hss-host': host_hss,
                        'hss-port': port_hss
                    }
                    """
            except:
                api_config_param = {
                    'hss-host': api_host_default,
                    'hss-port': api_port_default
                }  
        else:
            api_config_param = {
                    'hss-host': api_host_default,
                    'hss-port': api_port_default
                }            
        response = make_response(jsonify(api_config_param))
        response.headers.set("Content-Type", "application/json")
        return response
@api_space.route("/journal")
class MainClassHssApiJournal(Resource):
    @hss_space.produces(["text"])
    def get(self):
        """
        Get the journal of API
        """        
        proc = subprocess.Popen(["$SNAP/run journal apid"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

## Manager of OpenAPI of oai-hss
@api_manager_space.route("/conf")
class MainClassHssConf(Resource):
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
                        'hss-host': host_hss,
                        'hss-port': port_hss
                    }
                    """
            except:
                api_config_param = {
                    'hss-host': api_manager_host_default,
                    'hss-port': api_manager_port_default
                }  
        else:
            api_config_param = {
                    'hss-host': api_manager_host_default,
                    'hss-port': api_manager_port_default
                }            
        response = make_response(jsonify(api_config_param))
        response.headers.set("Content-Type", "application/json")
        return response

@api_manager_space.route("/start")
class MainClassHssApiManagerStart(Resource):
    @api_manager_space.produces(["text"])
    @api_manager_space.expect(api_manager_change_host_port)
    @api_manager_space.doc(params={
                "hss-host": "Valid IP address of oai-hss",
                "hss-port": "Valid port of oai-hss"
    })
    def put(self):
        """
        Start the manager of OpenAPI oai-hss
        WARNING: you may loose the connection if you enter non valid parameters
        """     
        args = api_manager_change_host_port.parse_args()
        host_hss = args['hss-host']
        port_hss =  args['hss-port']
        # Write the config parameters to json file to be used when starting up the flask service
        config_file = os.path.join(flask_app.config['PARAMETER_FOLDER'], flask_app.config['CONFIG_OPEN_API_MANAGER'])
        with open(config_file, 'w') as f:
            config_parameters = {
                "hss-host": host_hss,
                "hss-port": port_hss
            }
            json.dump(config_parameters, f)
        str_1 = request.url
        str_2 = request.path
        current_url = str(request.url).split(request.path)
        current_url = current_url[0]
        new_url = str(current_url).split("//")
        new_url = '{}//{}:{}'.format(new_url[0], host_hss, port_hss)
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
class MainClassHssApiManagerStop(Resource):
    @api_manager_space.produces(["application/json"])
    def get(self):
        """
        Stop the manager of OpenAPI oai-hss
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
class MainClassHssApiManagerRestart(Resource):
    @api_manager_space.produces(["text"])
    @api_manager_space.expect(api_manager_change_host_port)
    @api_manager_space.doc(params={
                "hss-host": "Valid IP address of oai-hss",
                "hss-port": "Valid port of oai-hss"
    })
    def put(self):
        """
        Restart the manager of OpenAPI oai-hss
        WARNING: you may loose the connection if you enter non valid parameters
        """     
        args = api_manager_change_host_port.parse_args()
        host_hss = args['hss-host']
        port_hss =  args['hss-port']
        # Write the config parameters to json file to be used when starting up the flask service
        config_file = os.path.join(flask_app.config['PARAMETER_FOLDER'], flask_app.config['CONFIG_OPEN_API_MANAGER'])
        with open(config_file, 'w') as f:
            config_parameters = {
                "hss-host": host_hss,
                "hss-port": port_hss
            }
            json.dump(config_parameters, f)
        str_1 = request.url
        str_2 = request.path
        current_url = str(request.url).split(request.path)
        current_url = current_url[0]
        new_url = str(current_url).split("//")
        new_url = '{}//{}:{}'.format(new_url[0], host_hss, port_hss)
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
class MainClassHssApiManagerStatus(Resource):
    @api_manager_space.produces(["application/json"])
    def get(self):
        """
        Get the status of the manager of OpenAPI oai-hss
        """        
        proc = subprocess.Popen(["$SNAP/run status apidman"], stdout=subprocess.PIPE, shell=True)
        # proc = subprocess.Popen(["oai-hss.apiman-journal"], stdout=subprocess.PIPE, shell=True)
        
        (out, err) = proc.communicate() 
        service_status = serialize_service_status(out)
        response = make_response(jsonify(service_status))
        response.headers.set("Content-Type", "application/json")
        return response
@api_manager_space.route("/journal")
class MainClassHssApiManagerJournal(Resource):
    @api_manager_space.produces(["text"])
    def get(self):
        """
        Get the journal of the manager of OpenAPI oai-hss
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
    
    parser = argparse.ArgumentParser(description='Pass host and port for flask api of hss')
        
    parser.add_argument('--hss-host', metavar='[option]', action='store', type=str,
                        required=False, default='{}'.format(api_host_default), 
                        help='Set OpenAPI-HSS IP address to bind to, {} (default)'.format(api_host_default))
    
    parser.add_argument('--hss-port', metavar='[option]', action='store', type=str,
                        required=False, default='{}'.format(api_port_default), 
                        help='Set oai-hss port number: {} (default)'.format(api_port_default))
    args = parser.parse_args()

    config_file = '{}{}'.format(PARAMETER_FOLDER, CONFIG_OPEN_API)

    if os.path.exists(config_file) and os.path.isfile(config_file):
        with open(config_file) as f:
            config_param = json.load(f)
            """
            # config file is of the form
            config_param = {
                'hss-host': host_hss,
                'hss-port': port_hss
            }
            """
            flask_app.run(host=config_param["hss-host"], port=config_param["hss-port"], debug=True)
    else:
        flask_app.run(host='{}'.format(api_host_default), port='{}'.format(api_port_default), debug=True)
