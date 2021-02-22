#!/usr/bin/python
# coding=utf-8

import sys
import time
import struct
import db
import threading

# for debug
import pprint
from var_dump import var_dump
sys.path.append('/root/8036/pycharm-debug.egg')
import pydevd
pydevd.settrace('192.168.8.100', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
#pydevd.settrace('192.168.7.8', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)

from HeatController.Controller8036 import *

SerialPort = "/dev/ttyS0"
global HeatCtl
HeatCtl = Controller8036(SerialPort)

#connection = None
#global connection
DBConnect = db.Database()


if HeatCtl.testConnection():
    print("Connect is success")
else:
    print("Error. No connect to Heat controller")

def main(HeatCtl):
    HeatCtl.UpdateSensorsHistory()
loop_counter = 1
#main(HeatCtl)

while True:
     try:
         main(HeatCtl)
     except:
         print("Unknown ERROR")
         pass
     finally:
         time.sleep( 60 ) # 1 min.
         loop_counter +=1
         print("loop:"+str(loop_counter))
         pass


from flask import jsonify
from api_utils import ResponsiveFlask

app = ResponsiveFlask(__name__)

@app.route('/')
def index():
    return {'api': '1'}

@app.route('/get/temp/')
def get_temp():
    temperature = {}
    temperature[1] = {'sensor_value': 24.0, 'addr': '283f3ae90200007b', 'link_id': 2 }
    temperature[2] = {'sensor_value':  0.0, 'addr': '28b03ce902000029', 'link_id': 3 }
    temperature[3] = {'sensor_value': 21.9, 'addr': '28bd24e902000021', 'link_id': 4 }
    result = jsonify(temperature)
    return result

@app.errorhandler(404)
def page_not_found(error):
    return {'error': 'This API method does not exist'}, 404



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=None)