from flask import Flask, render_template, request, jsonify, json, url_for
from werkzeug.utils import secure_filename
import subprocess
import os                                                                      
app = Flask(__name__)                                                          
TEMP_DIR="/var/snap/oai-hss/current/"
TEMP_DIR="/home/mineuse"
SNAP="/snap/oai-hss/current/"

dbip="172.17.0.2"


# PSOT methods

@app.route('/hss/mme', methods = ['GET', 'POST'])
def mme():                                                                   
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(TEMP_DIR+f.filename))
        f.save(os.path.join(TEMP_DIR, secure_filename(f.filename)))
        print(f)

        status_code = 200
        proc = subprocess.Popen(["$SNAP/run add-mme", f.filename], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        # print ("program output:", err)
        return out, status_code
    else:
        status_code = 200
        proc = subprocess.Popen(["$SNAP/run dump-mme"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        # print ("program output:", err)
        return out, status_code

	
@app.route('/hss/conf', methods = ['GET', 'POST'])
def conf():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(TEMP_DIR+f.filename))
        f.save(os.path.join(TEMP_DIR, secure_filename(f.filename)))
        print(f)
    
        proc = subprocess.Popen(["$SNAP/conf set-hss",f.filename ], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        # print ("program output:", err)
        status_code = 200
        return 'The file {} is uploaded successfully\n'.format(f.filename), status_code
    else: 
        status_code = 200
        proc = subprocess.Popen(["$SNAP/conf echo-hss"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        print ("program output:", err)
        return out, status_code


@app.route('/hss/users', methods = ['GET', 'POST'])
def users():
    if request.method == 'POST':
        # check if the post request has the file part
        f = request.files['file']
        f.save(secure_filename(TEMP_DIR+f.filename))
        f.save(os.path.join(TEMP_DIR, secure_filename(f.filename)))
        print(f.read())
    
        status_code = 200
        proc = subprocess.Popen(["$SNAP/run add-users", f.filename], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        # print ("program output:", err)
        return out, status_code
    else:
        print ("GET")
        status_code = 200
        proc = subprocess.Popen(["$SNAP/run dump-mme"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        # print ("program output:", err)
        return out, status_code
        
@app.route('/hss/db/ip')
def db_ip():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run db-ip"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    #print ("program output:", (out.decode("utf-8")).strip())
    return (out.decode("utf-8")).strip(), status_code


    
@app.route('/hss/conf/list')
def list_conf():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/conf ls-hss"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/conf/show')
def show_conf():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/conf cat-hss"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/db/clean')
def clean_db():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run clean-db"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/db/reset')
def reset_db():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run reset-db"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code



# Daemon API

@app.route('/hss/init')
def hss_init():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/init hss"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/status')
def hss_status():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run status"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/start')
def hss_start():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run start hssd"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/stop')
def hss_stop():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run stop hssd"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print ("program output:", err)
    return out, status_code

@app.route('/hss/journal')
def hss_journal():                                                                   
    status_code = 200
    proc = subprocess.Popen(["$SNAP/run journal hssd"], stdout=subprocess.PIPE, shell=True)
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
    
    app.run(host="0.0.0.0", port=1234, debug=True)
