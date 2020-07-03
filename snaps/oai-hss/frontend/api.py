from flask import Flask, render_template, request, jsonify, json, url_for
from werkzeug.utils import secure_filename
import subprocess
import os, logging   
import argparse


app = Flask(__name__)                                                          


snap_name = "oai-hss"

SNAP="/snap/{}/current".format(snap_name)

UPLOAD_FOLDER="/var/snap/{}/current/".format(snap_name)
PARAMETER_FOLDER="/var/snap/{}/common/usr/share/parameters/".format(snap_name)

ALLOWED_EXTENSIONS = {'json', 'conf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PARAMETER_FOLDER'] = PARAMETER_FOLDER

# database ip
dbip="172.17.0.2"

## log
logger = logging.getLogger('hss.openapi')
logging.basicConfig(level=logging.ERROR)
logger.info('Starting Open API of {}'.format(snap_name))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

"""
Example Usage:
GET: usage example: curl http://0.0.0.0:1234/hss/mme
POST: usage example: curl http://0.0.0.0:1234/hss/mme  -X POST -F file=@hss_add_mme_param.json
"""
@app.route('/hss/mme', methods = ['GET', 'POST'])
def mme():                                                                   
    if request.method == 'POST':
        if 'file' not in request.files:
            status_code = 404
            return 'No file found\n', status_code
        file = request.files['file']
        # if user does not select file
        if file.filename == '':
            return 'No file selected\n', status_code
        if file and allowed_file(file.filename):
            file.save(os.path.join(app.config['PARAMETER_FOLDER'], secure_filename(file.filename)))
            logger.info("file={}".format(os.path.join(app.config['PARAMETER_FOLDER'], secure_filename(file.filename))))
            file_absolute = os.path.join(app.config['PARAMETER_FOLDER'], secure_filename(file.filename))
            try:
                with open(file_absolute) as f:
                    json_parameters = json.load(f)
                    """
                    Expected fiels for adding mme with example values
                    {
                        "mme-id": "4",
                        "mme-hostname": "ubuntu.openair5G.eur",
                        "realm": "openair5G.eur",
                        "cluster-ip-address": "192.168.1.223",
                        "mme-isdn": "208",
                        "ue-reachability": 1,
                        "database-reset": "no"
                    }"""
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
            except Exception as ex:
                message = "Error while trying to open the file {}\n".format(file_absolute)
                status_code = 400
                print("error= ", ex)
                return message, status_code
        else:
            status_code = 400
            return 'The file {} is NOT supported as config file\n'.format(file.filename), status_code
    else:
        status_code = 200
        proc = subprocess.Popen(["$SNAP/run dump-mme"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        return out, status_code

	
"""
Example Usage:
GET: curl http://0.0.0.0:1234/hss/conf
POST: curl http://0.0.0.0:1234/hss/conf  -X POST -F file=@hss_rel14.json
"""
@app.route('/hss/conf', methods = ['GET', 'POST'])
def conf():
    if request.method == 'POST':
        if 'file' not in request.files:
            status_code = 404
            logger.debug("No file found")
            logger.info("No file found")
            return 'No file found\n', status_code
        file = request.files['file']
        # if user does not select file
        if file.filename == '':
            logger.debug("No file selected")
            logger.info("No file selected")
            return 'No file selected\n', status_code
        if file and allowed_file(file.filename):
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
            logger.info("file={}".format(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))))
            file_absolute = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            
            logger.debug("command to set config file= {} {}".format("$SNAP/conf set-hss", file_absolute))
            proc = subprocess.Popen(["$SNAP/conf set-hss {}".format(file_absolute)], stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
            
            logger.debug("program out: {}".format(out))
            logger.info("program out: {}".format(out))

            logger.debug("program err: {}".format(err))
            logger.info("program err: {}".format(err))

            
            status_code = 200
            return 'The file {} is uploaded successfully\n'.format(file.filename), status_code
        else:
            status_code = 400
            return 'The file {} is NOT supported as config file\n'.format(file.filename), status_code
    else: 
        status_code = 200
        proc = subprocess.Popen(["$SNAP/conf echo-hss"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        print ("program output:", err)
        return out, status_code


"""
Example Usage: 
GET: curl http://0.0.0.0:1234/hss/users
POST: curl http://0.0.0.0:1234/hss/users  -X POST -F file=@hss_add_users_param.json
"""

@app.route('/hss/users', methods = ['GET', 'POST'])
def users():                                                                   
    if request.method == 'POST':
        if 'file' not in request.files:
            status_code = 404
            logger.debug("No file found")
            logger.info("No file found")
            return 'No file found\n', status_code
        file = request.files['file']
        # if user does not select file
        if file.filename == '':
            return 'No file selected\n', status_code
        if file and allowed_file(file.filename):
            file.save(os.path.join(app.config['PARAMETER_FOLDER'], secure_filename(file.filename)))
            logger.info("file={}".format(os.path.join(app.config['PARAMETER_FOLDER'], secure_filename(file.filename))))
            file_absolute = os.path.join(app.config['PARAMETER_FOLDER'], secure_filename(file.filename))

            try:
                with open(file_absolute) as f:
                    json_parameters = json.load(f)
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
            except Exception as ex:
                message = "Error while trying to open the file {}\n".format(file_absolute)
                status_code = 400
                print("error= ", ex)
                return message, status_code
        else:
            status_code = 400
            return 'The file {} is NOT supported as config file\n'.format(file.filename), status_code
    else:
        status_code = 200
        proc = subprocess.Popen(["$SNAP/run dump-users"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        return out, status_code

    
@app.route('/hss/conf/list', methods = ['GET'])
def list_conf():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/conf ls-hss"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/conf/show', methods = ['GET'])
def show_conf():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/conf cat-hss"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/db/ip', methods = ['GET'])
def db_ip():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run db-ip"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    #print ("program output:", (out.decode("utf-8")).strip())
    return '{} \n'.format((out.decode("utf-8")).strip()), status_code

@app.route('/hss/db/clean', methods = ['GET'])
def clean_db():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run clean-db"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/db/reset', methods = ['GET'])
def reset_db():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run reset-db"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

# Daemon API
@app.route('/hss/init', methods = ['GET'])
def hss_init():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/init hss"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/status', methods = ['GET'])
def hss_status():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run status"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/start', methods = ['GET'])
def hss_start():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run start hssd"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/stop', methods = ['GET'])
def hss_stop():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run stop hssd"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/restart', methods = ['GET'])
def hss_restart():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run restart hssd"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/journal', methods = ['GET'])
def hss_journal():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run journal hssd"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/api/journal', methods = ['GET'])
def api_journal():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run journal apid"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code
# example: curl http://0.0.0.0:5000/ran/conf/set -X POST -H "Content-Type: multipart/form-data"  -F "file=@enb.band7.tm1.50PRB.usrpb210.conf"



#OpenAPI ENDPOINTs
@app.route('/')                                                                
def oai_hss_endpoints():                                                                   
    routes = []

    for rule in app.url_map.iter_rules():

        if rule.endpoint == 'static' :
            break  
        methods = ','.join(sorted(rule.methods))
        routes.append ({"api": str(rule), "endpoint": str(rule.endpoint), "methods" : str(methods)})

    return json.dumps(routes)

if __name__ == "__main__":                                                     
    
    parser = argparse.ArgumentParser(description='Pass host and port for flask api of hss')
        
    parser.add_argument('--hss-host', metavar='[option]', action='store', type=str,
                        required=False, default='0.0.0.0', 
                        help='Set OpenAPI-HSS IP address to bind to, 0.0.0.0 (default)')
    
    parser.add_argument('--hss-port', metavar='[option]', action='store', type=str,
                        required=False, default='1234', 
                        help='Set hss port number: 1234 (default)')
    args = parser.parse_args()
    app.run(host=args.hss_host, port=args.hss_port, debug=True)

