# Made by Kim.Seung.Hwan / ksana1215@interminds.ai
# -*- coding: utf-8 -*-
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
config.read('config.ini')
cf_path = config['path']['path']
cf_scanner_port = config['refrigerators']['scanner']
rd = redis.StrictRedis(host='localhost', port=6379, db=0)
Scanner = serial.Serial(port=cf_scanner_port, baudrate=9600, timeout=1)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(filename=cf_path + 'kiosk_status.log', level=logging.DEBUG)
logger = logging.getLogger('QR_LOG')
NICEPOS = ctypes.windll.LoadLibrary(cf_path + 'DLL/NICEPOSICV105.dll')

while True:
    try:
        log_time = datetime.datetime.now()
        log_time = log_time.strftime("%Y-%m-%d-%H:%M:%S")
        nvcat_log = datetime.datetime.now()
        nvcat_log = nvcat_log.strftime("%Y%m%d")
        page = rd.get('nowPage')
        barcode = Scanner.readline()
        barcode = barcode.decode('utf-8').rstrip()
        #관리자 바코드
        if len(barcode) > 0 and page == b'start' and barcode == '0123456789':
            rd.set('msg', 'admin')
            rd.set('door', 'admin')
        #PASS앱 성인 인증
        if len(barcode) > 0 and page == b'auth_adult':
            blank = ' '
            cat_id = '3946768'
            req_data = bytes(f'0437MDL{cat_id}0010000000000020010H1{blank * 10}{cat_id}001L{barcode}={blank * 102}00{blank * 24}1012002{blank * 5}1043003{blank * 192}','utf-8')
            NVCAT = NICEPOS.PosSend2(b'211.33.136.2', 4141, req_data, b'NULL', b'NULL', b'NULL') #나정통 DLL 함수 호출
            if NVCAT == 1:
                logger.info("==" * 5 + 'DLL PosSend2 Success' + "==" * 5)
                logger.info(log_time)
                dll_log = open(cf_path+f'log/{nvcat_log}.log') #응답값은 log파일에 저장
                response = dll_log.readlines()[-3] #log파일 밑에서 3번째줄이 응답 전문
                result = response.split(' ')[24][10:14] #No.27 = 응답메세지
                logger.info(response)
                if result == '0000':
                    rd.set('msg', 'sign')
                    logger.info("==" * 5 + 'Adult Pass Success' + "==" * 5)
                    logger.info('NVCAT result code : ' + result)
                    rd.set('msg', 'sign')
                else:
                    rd.set('msg', 'auth_fail')
                    logger.info("==" * 5 + 'Adult Auth Fail' + "==" * 5)
                    logger.info('NVCAT result code : ' + result)
            else:
                rd.set('msg', 'auth_fail')
                logger.info("==" * 5 + 'DLL PosSend2 Fail' + "==" * 5)
                logger.info(log_time)

    except Exception as err:
        rd.set('err_type', 'except')
        request_main.device_err()
        logger.info("==" * 5 + 'SCANNER FAIL' + "==" * 5)
        logger.info(err)
        break
