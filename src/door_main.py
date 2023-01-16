# Made by Kim.Seung.Hwan / ksana1215@interminds.ai
# -*- coding: utf-8 -*-
import os
import time
import serial
import redis
import logging
import datetime
import config
import urllib3
from playsound import playsound
import request_main
cf_path = config.path['path']
cf_door_port = config.refrigerators['door']
rd = redis.StrictRedis(host='localhost', port=6379, db=0)
Arduino = serial.Serial(port=cf_door_port, baudrate=9600, timeout=0.1)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(filename=cf_path+'kiosk_status.log',level=logging.DEBUG)
logger = logging.getLogger('UNO_LOG')
cnt = 0
flg = 0
while True:
    log_time = datetime.datetime.now()
    log_time = log_time.strftime("%Y-%m-%d-%H:%M:%S")
    door = rd.get('door')
    try:
        uno = str(Arduino.readline().decode('utf-8').rstrip())

        #고객 문열림
        if door == b'open':
            logger.info(f'[{log_time} | DOOR_OPEN --> CLIENT]')
            Arduino.write(str('1').encode('utf-8'))
            rd.set('door','customer')
            request_main.door_open()

        #고객 문닫힘
        if uno == '0' and door == b'customer':
            logger.info(f'[{log_time} | DOOR_CLOSE --> CLIENT]')
            rd.delete('door')
            rd.set("msg",'infer')
            request_main.door_close()
            if rd.get('err_type') == b'long':
                request_main.release_event()

        # 관리자 문열림
        if door == b'admin':
            Arduino.write(str('1').encode('utf-8'))
            rd.set('door', 'admin_open')
            request_main.admin_open()

        #관리자 문닫힘
        if uno == '0' and door == b'admin_open':
            request_main.admin_close()

        #100초 알림
        elif door == b'customer' or door == b'admin_open':
            cnt += 1
            if cnt > 3000 and door == b'customer':
                playsound(cf_path + 'voice/' + "long.mp3", False)
                rd.set('err_type', 'long')
                request_main.device_err()
                cnt = 0
            if cnt > 3000 and door == b'admin_open':
                playsound(cf_path + 'voice/' + "longlong.mp3", False)
                cnt = 0
        else:
            cnt = 0

        # 방어로직 카운트
        if uno == '2':
            flg += 1
        #방어로직 2회발생시 알림 발생
        if uno == '2' and flg == 2:
            rd.set('err_type', 'lock')
            rd.set('msg','device_err')
            logger.info(f'[{log_time} | LOCK ERR]')
            request_main.device_err()
        # 문 다시 닫힘 / 관리자 오클 / 키오스크 재실행
        if uno == 'r' and flg > 0:
            logger.info(f'[{log_time} | DOOR RECLOSED]')
            request_main.admin_open()
            request_main.admin_close()
            logger.info(f'[{log_time} | REBOOT]')
            os.system(cf_path + 'start.sh')

        # 냉장고 내부 재시작
        if door == b'restart':
            Arduino.write(str('80').encode('utf-8'))
            rd.delete('door')
            time.sleep(60)
            Arduino.write(str('81').encode('utf-8'))
            time.sleep(60)
            rd.delete('door')
    except Exception as err:
        rd.set('err_type', 'except')
        rd.set('msg', 'device_err')
        request_main.device_err()
        logger.info(f'[{log_time} | ARDUINO FAIL]' + '\n' + str(err))
        break
