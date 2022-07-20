# Made by Kim.Seung.Hwan / ksana1215@interminds.ai
# -*- coding: utf-8 -*-
import serial
import redis
import logging
import datetime
# import config
import urllib3
from playsound import playsound
import request_main
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

cf_path = config['path']['path']
cf_door_port = config['refrigerators']['door']
rd = redis.StrictRedis(host='localhost', port=6379, db=0)
Arduino = serial.Serial(port=cf_door_port, baudrate=9600, timeout=0.1)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(filename=cf_path+'kiosk_status.log',level=logging.DEBUG)
logger = logging.getLogger('DOOR_LOG')
log_time = datetime.datetime.now()
log_time = log_time.strftime("%Y-%m-%d-%H:%M:%S")
cnt = 0

while True:
    try:
        door = rd.get('door')
        uno = Arduino.readline()
        #문열림
        if door == b'open':
            Arduino.write(str('1').encode('utf-8'))
            rd.set('door','customer')
            request_main.door_open()
        #100초 알림
        if door == b'customer':
            cnt += 1
            if cnt > 2000:
                logger.info("=="*5+'LONG ALARM'+"=="*5)
                logger.info(log_time)
                playsound(cf_path + 'voice/' + "long.mp3", False)
                rd.set('err_type', 'long')
                request_main.device_err()
                cnt = 0
        else:
            cnt = 0
        #관리자 문열림
        if door == b'admin':
            Arduino.write(str('1').encode('utf-8'))
            rd.set('door', 'admin_open')
            request_main.admin_open()
        #100초 알림
        if door == b'admin_open':
            cnt += 1
            if cnt > 2000:
                logger.info("=="*5+'ADMIN LONG ALARM'+"=="*5)
                logger.info(log_time)
                playsound(cf_path + 'voice/' + "longlong.mp3", False)
                cnt = 0
        #문닫힘
        if uno == b'0\r\n':
            #관리자 권한
            if door == b'admin_open':
                request_main.admin_close()
            #고객
            elif door == b'customer':
                rd.delete('door')
                rd.set("msg",'infer')
                logger.info("=="*5+'DOOR_CLOSE --> CLIENT'+"=="*5)
                logger.info(log_time)
                request_main.door_close()

        #문여닫힘 에러
        if uno == b'2\r':
            rd.set('err_type','except')
            request_main.device_err()
            logger.info("==" * 5 + 'DOOR LOCK ERR' + "==" * 5)
            logger.info(log_time)

    except Exception as err:
        rd.set('err_type', 'except')
        request_main.device_err()
        logger.info("==" * 5 + 'ARDUINO FAIL' + "==" * 5)
        logger.info(err)
        break
