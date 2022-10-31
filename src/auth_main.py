# Made by Kim.Seung.Hwan / ksana1215@interminds.ai
# -*- coding: utf-8 -*-
import base64
import json
import os

import requests
import serial
import redis
import datetime
import logging
# import config
import urllib3
import request_main
import ctypes
import configparser

config = configparser.ConfigParser()
config.read(os.path.join(os.path.split(__file__)[0],'config.ini'))
cf_path = config['path']['path']
storeId = config['refrigerators']['storeId']
cf_scanner_port = config['refrigerators']['scanner']
deviceId = config['refrigerators']['deviceId']
companyId = config['refrigerators']['companyId']
rd = redis.StrictRedis(host='localhost', port=6379, db=0)
Scanner = serial.Serial(port=cf_scanner_port, baudrate=9600, timeout=1)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(filename=cf_path + 'kiosk_status.log', level=logging.DEBUG)
logger = logging.getLogger('QRC_LOG')
NICEPOS = ctypes.windll.LoadLibrary(cf_path + 'DLL/NICEPOSICV105.dll')

def pass_auth(barcode):
    blank = ' '
    cat_id = '3946768'
    req_data = bytes(
        f'0437MDL{cat_id}0010000000000020010H1{blank * 10}{cat_id}001L{barcode}={blank * 102}00{blank * 24}1012002{blank * 5}1043003{blank * 192}',
        'utf-8')
    NVCAT = NICEPOS.PosSend2(b'211.33.136.2', 4141, req_data, b'NULL', b'NULL', b'NULL')  # 나정통 DLL 함수 호출
    if NVCAT == 1:
        dll_log = open(cf_path + f'log/{nvcat_log}.log')  # 응답값은 log파일에 저장
        response = dll_log.readlines()[-3]  # log파일 밑에서 3번째줄이 응답 전문
        result = response.split(' ')[24][10:14]  # No.27 = 응답메세지
        if result == '0000':
            rd.set('msg', 'sign')
            logger.info(f'[{log_time} | NVCAT result code : {result}]')
        else:
            rd.set('msg', 'auth_fail')
            logger.info(f'[{log_time} | NVCAT result code : {result}]')
    else:
        rd.set('msg', 'auth_fail')
        logger.info(f'[{log_time} | DLL PosSend2 Fail]')

def auth_mobile_id():
    try:
        data = {
            "cmd": 520,             # QR-CPM - 520 고정
            "m120Base64": barcode,
            "svcCode": "zkp.1",     # zkp.1 - 성인여부 제출 고정
            "branchName": storeId,
            "deviceId": deviceId
        }
        vo = {
            'result': False,
            'data': str(base64.b64encode(json.dumps(data).encode()), 'utf-8')
        }

        response = requests.post("http://localhost:8281/qrcpm/start", data=json.dumps(vo),
                            headers={"Content-Type": "application/json; charset=utf-8"}, timeout=40)

        res = response.json()
        res_result = res["result"]
        res_data = json.loads(base64.b64decode(res["data"]))
        page = rd.get('nowPage')
        if page == b'wait_mobileid':
            if res_result:
                if res_data["vpVerifyResult"] == "Y":
                    rd.set('msg', 'sign')
                    logger.info(f'[{log_time}]' + f'[Mobile ID Auth Success] : {res_data}')
                else:
                    rd.set('msg', 'auth_fail')
                    logger.info(f'[{log_time}]' + f'[Mobile ID Auth Fail] : {res_data}')
            else:
                rd.set('msg', 'auth_fail')
                logger.info(f'[{log_time}]' + f"[SP Server Access Fail] : {res_data}")

    except Exception as e:
        logger.info(f'[{log_time}]' + f"[SP Server Access ERROR] : {e}")
        page = rd.get('nowPage')
        if page == b'mobile_auth' or page == b'wait_mobileid':
            rd.set('msg', 'auth_fail')

def rrn_auth():
    try:
        data = {
            "svcTypeGb": 'IDM',
            "svcCustSubCd": companyId,
            "svcCustSupNm": storeId,
            "svcCustCd": deviceId,
            "svcCustNm": deviceId,
            "svcInstId": '3001000009',
            "svcSrvcCd": '02',
            "svcMthCd": '01',
            "svcQrCd": barcode
        }

        res = requests.post("https://idmc.jumin.go.kr/API/MobileIdcardAPITypeAInfo.do", data=json.dumps(data),
                            headers={"Content-Type": "application/json; charset=utf-8"}, timeout=60)

        result = res.json()
        if result['recTruflsResultCd'] == '00':     #진위결과코드 - 00: 성공 01: 실패
            if result['recAdltResultCd3'] == '00':  #성인인증결과(만19세 1월1일 기준) - 00: 성년 01: 미성년
                rd.set('msg', 'sign')
                logger.info(f'[{log_time}] [RRN Auth Success]')
            else:
                rd.set('msg', 'auth_fail')
                logger.info(f'[{log_time}] [RRN Auth Fail] : under age')
        else:
            rd.set('msg', 'auth_fail')
            logger.info(f'[{log_time}] [RRN Auth Fail] : {result}')

    except Exception as e:
        logger.info(f'[{log_time}]' + f"[RRN API SEND ERROR] : {e}")
        logger.info(f'barcode: {barcode}')
        rd.set('msg', 'auth_fail')

while True:
    try:
        t_time = datetime.datetime.now()
        log_time = t_time.strftime("%Y-%m-%d-%H:%M:%S")
        nvcat_log = t_time.strftime("%Y%m%d")
        page = rd.get('nowPage')
        barcode = Scanner.readline()
        barcode = barcode.decode('utf-8').rstrip()
        #관리자 바코드
        if len(barcode) > 0 and page == b'start' and barcode == '0123456789':
            rd.set('msg', 'admin')
            rd.set('door', 'admin')
        #PASS앱 성인 인증
        if len(barcode) > 0 and page == b'pass_auth':
            pass_auth(barcode)
        elif len(barcode) > 0 and page == b'mobile_auth':
            rd.set('msg', 'mobile_id')
            rd.set('nowPage', 'wait_mobileid')
            auth_mobile_id()
        elif len(barcode) > 0 and page == b'rrn_auth':
            rrn_auth()

    except Exception as err:
        rd.set('err_type', 'except')
        request_main.device_err()
        logger.info('[SCANNER FAIL]')
        logger.info(err)
        break
