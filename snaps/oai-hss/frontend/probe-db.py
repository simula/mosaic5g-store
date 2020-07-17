
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
# author Osama Arouk


import os
import argparse
from cassandra.cluster import Cluster
import json

def probe_db(cassandra_cluster):

    cluster = Cluster([cassandra_cluster])
    try:
        session = cluster.connect()
        strCQL = "SELECT cluster_name FROM system.local"
        pStatement = session.prepare(strCQL)
        rows = session.execute(pStatement)
        db_name = ""
        for row in rows:
            db_name = row[0]
            break
        status = {
            "{}".format(db_name):{
                "ip": cassandra_cluster,
                "status": "alive",
                "reason": ""
            }
        }
    except Exception as e:
        # e = e.__dict__
        status = {
            "db-cassandra":{
                "ip": cassandra_cluster,
                "status": 'not alive',
                "reason": str(e) #str([*e.values()][0])
            }
        }
    print(json.dumps(status, sort_keys=False, indent=2))
    
if __name__ == "__main__":                                                     
    
    parser = argparse.ArgumentParser(description='Check whether the database is alive')

    parser.add_argument('-C', '--cassandra-cluster', metavar='[option]', action='store', type=str,
                        required=False, default='172.17.0.2', 
                        help='Ip address of the database cassandra: 172.17.0.2 (default)')
    args = parser.parse_args()
    probe_db(args.cassandra_cluster)
    
    
    