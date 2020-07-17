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
from flask_restplus import Api, Resource, fields
from werkzeug.utils import secure_filename
import subprocess
import os, logging   
import argparse
from werkzeug.utils import cached_property
from werkzeug.datastructures import FileStorage


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


upload_json_file = hss_space.parser()
upload_json_file.add_argument('file', location='files', type=FileStorage, required=False)


model = flask_api.model('Name Model', 
				  {'name': fields.String(required = True, 
    					  				 description="Name of the person", 
    					  				 help="Name cannot be blank.")})

snap_name = "oai-hss"


SNAP="/snap/{}/current".format(snap_name)

UPLOAD_FOLDER="/var/snap/{}/current/".format(snap_name)
PARAMETER_FOLDER="/var/snap/{}/common/usr/share/parameters/".format(snap_name)

# DIR for testing
# UPLOAD_FOLDER="/home/cigarier/Downloads/tmp/oai-hss/"
# PARAMETER_FOLDER="/home/cigarier/Downloads/tmp/oai-hss/parameters/"
# 

flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'json', 'conf'}
flask_app.config['PARAMETER_FOLDER'] = PARAMETER_FOLDER

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
        uploaded_file = args['file']  # This is FileStorage instance
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


    @hss_space.expect(upload_json_file)
    @hss_space.doc(params={"file": "Upload json file with the requireds fields (see below an example) to add one or more MME to OAI-HSS"})
    def post(self):
        """
        Set config file to oai-hss
        """
        status_code = 200
        args = upload_json_file.parse_args()
        uploaded_file = args['file']  # This is FileStorage instance
        if type(uploaded_file) == type(None):
            status_code = 200
            return 'No Json File found', status_code
        else:
            json_parameters = (uploaded_file.read()).decode("utf-8")
            json_parameters = json.loads(json_parameters)
            if uploaded_file and allowed_file(uploaded_file.filename):
                uploaded_file.save(os.path.join(flask_app.config['UPLOAD_FOLDER'], secure_filename(uploaded_file.filename)))
                logger.info("file={}".format(os.path.join(flask_app.config['UPLOAD_FOLDER'], secure_filename(uploaded_file.filename))))
                file_absolute = os.path.join(flask_app.config['UPLOAD_FOLDER'], secure_filename(uploaded_file.filename))
                with open(file_absolute, 'w') as json_file:
                    json.dump(json_parameters, json_file, indent=2, separators=(", ", ": "), sort_keys=True)

                logger.debug("command to set config file= {} {}".format("$SNAP/conf set-hss", file_absolute))
                proc = subprocess.Popen(["$SNAP/conf set-hss {}".format(file_absolute)], stdout=subprocess.PIPE, shell=True)
                (out, err) = proc.communicate()
                
                logger.debug("program out: {}".format(out))
                logger.info("program out: {}".format(out))

                logger.debug("program err: {}".format(err))
                logger.info("program err: {}".format(err))
                status_code = 200
                return 'The file {} is successfully uploaded to {}\n'.format(uploaded_file.filename, file_absolute), status_code
            else:
                status_code = 400
                return 'The file {} is NOT supported as config file\n'.format(uploaded_file.filename), status_code


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
    # @hss_space.produces(["text"])
    def get(self):
        """
        Show the config of oai-hss
        """        
        # proc = subprocess.Popen(["oai-hss.conf-show"], stdout=subprocess.PIPE, shell=True)
        proc = subprocess.Popen(["$SNAP/conf cat-hss"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "json")
        # response.headers.set("Content-Type", "text")
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
    @hss_space.produces(["text"])
    def get(self):
        """
        Get the status of hss and api
        """        
        proc = subprocess.Popen(["$SNAP/run status"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@hss_space.route("/start")
class MainClassHssStart(Resource):
    @hss_space.produces(["text"])
    def get(self):
        """
        Start the service oai-hss in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run start hssd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response

@hss_space.route("/stop")
class MainClassHssStop(Resource):
    @hss_space.produces(["text"])
    def get(self):
        """
        Stop the service oai-hss in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run stop hssd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
        return response
@hss_space.route("/restart")
class MainClassHssReStart(Resource):
    @hss_space.produces(["text"])
    def get(self):
        """
        Restart the service oai-hss in deamon mode
        """        
        proc = subprocess.Popen(["$SNAP/run restart hssd"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate() 

        response = make_response(out)
        response.headers.set("Content-Type", "text")
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
if __name__ == "__main__":                                                     
    
    parser = argparse.ArgumentParser(description='Pass host and port for flask api of hss')
        
    parser.add_argument('--hss-host', metavar='[option]', action='store', type=str,
                        required=False, default='0.0.0.0', 
                        help='Set OpenAPI-HSS IP address to bind to, 0.0.0.0 (default)')
    
    parser.add_argument('--hss-port', metavar='[option]', action='store', type=str,
                        required=False, default='5551', 
                        help='Set hss port number: 5551 (default)')
    args = parser.parse_args()
    flask_app.run(host=args.hss_host, port=args.hss_port, debug=True)
    #############################
    # # new way to change the config of api by taking them from config file. like the config file of hss
    # config_file = '{}{}'.format(PARAMETER_FOLDER, "api_conf.json")
    # try:
    #     with open(config_file) as f:
    #         config_param = json.load(f)
    #         flask_app.run(host=config_param["hss-host"], port=config_param["hss-port"], debug=True)
    # except:
    #     flask_app.run(host='0.0.0.0', port='5551', debug=True)