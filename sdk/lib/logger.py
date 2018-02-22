"""
   Licensed to the Mosaic5G under one or more contributor license
   agreements. See the NOTICE file distributed with this
   work for additional information regarding copyright ownership.
   The Mosaic5G licenses this file to You under the
   Apache License, Version 2.0  (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
  
    	http://www.apache.org/licenses/LICENSE-2.0
  
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
 -------------------------------------------------------------------------------
   For more information about the Mosaic5G:
   	contact@mosaic-5g.io
"""

"""
    File name: logger.py
    Author: navid nikaein
    Description: Warpper around the python logging library
    version: 1.0
    Date created: 7 July 2017
    Date last modified: 7 July 2017 
    Python Version: 2.7
"""

import io
import time
import logging


class logger(object):

    def __init__(self, log_level='info'):
        super(logger, self).__init__()
        self.log_level=log_level
       

    def init_logger(self):
    
        """initializing the pythong logger """
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename='/tmp/jujuagent.log',
                            filemode='w')
        
        # define a Handler which writes INFO messages or higher to the sys.stderr
        self.console = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.console.setFormatter(formatter)
        # add the handler to the root logger
        
        logging.getLogger('').addHandler(self.console)
        self.log = logging.getLogger('flexran_sdk')
        
        if self.log_level == 'debug':
            self.console.setLevel(logging.DEBUG)
            self.log.setLevel(logging.DEBUG)
        elif self.log_level == 'info':
            self.console.setLevel(logging.INFO)
            self.log.setLevel(logging.INFO)
        elif self.log_level == 'warn':
            self.console.setLevel(logging.WARNING)
            self.log.setLevel(logging.WARNING)
        elif self.log_level == 'error':
            self.console.setLevel(logging.ERROR)
            self.log.setLevel(logging.ERROR)
        elif self.log_level == 'critic':
            self.console.setLevel(logging.CRITICAL)
            self.log.setLevel(logging.CRITICAL)
        else:
            self.console.setLevel(logging.INFO)
            self.log.setLevel(logging.INFO)

        return self.log
