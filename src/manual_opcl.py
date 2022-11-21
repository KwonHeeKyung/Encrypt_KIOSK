# Made by Kim.Seung.Hwan / ksana1215@interminds.ai
# -*- coding: utf-8 -*-
import os
import redis
import time
import json
import requests
import urllib3
import datetime

import logging

import configparser
config = configparser.ConfigParser()
config.read(os.path.join(os.path.split(__file__)[0],'config.ini'))

cf_path = config['path']['path']
cf_company_id = config['refrigerators']['companyId']
cf_store_id = config['refrigerators']['storeId']
cf_device_id = config['refrigerators']['deviceId']
cf_network_server = config['network_info']['server_request_url']
cf_master_server = config['network_info']['raspberry_base_url']
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(filename=cf_path + 'kiosk_status.log', level=logging.DEBUG)
logger = logging.getLogger('API_LOG')
rd = redis.StrictRedis(host='localhost', port=6379, db=0)
msg = rd.get('msg')

def admin_opcl():
    log_time = datetime.datetime.now()
    log_time = log_time.strftime("%Y-%m-%d-%H:%M:%S")
    res = requests.post(f'{cf_master_server}manage_door', json={'deviceId': cf_device_id, 'doorStatus': 'O'},
                        verify=False)
    logger.info(f'[{log_time} | 관리자 OPEN SUCCESS]' + '\n' + str(res.text))
    if json.loads(res.text)['resultCode'] == '000':
        res = requests.post(f'{cf_master_server}manage_door', json={'deviceId': cf_device_id, 'doorStatus': 'C'},
                            verify=False)
        logger.info(f'[{log_time} | 관리자 CLOSE SUCCESS]' + '\n' + str(res.text))
        if json.loads(res.text)['resultCode'] == '000':
            rd.set('msg', 'admin_close')
        else:
            rd.set('msg', '001')
        rd.delete('door')


admin_opcl()
