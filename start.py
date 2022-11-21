# 실행파일 생성: pyinstaller -w -F start.py --icon=start_icon.ico

import datetime
import subprocess
import time
import redis
import urllib3
import logging
import configparser

config = configparser.ConfigParser()
config.read('src/config.ini')
cf_path = config['path']['path']
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(filename=cf_path + 'kiosk_status.log', level=logging.DEBUG)
logger = logging.getLogger('BACKGROUND_LOG')
rd = redis.StrictRedis(host='localhost', port=6379, db=0)

if __name__ == '__main__':
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.CREATE_NO_WINDOW
        credit_main = subprocess.Popen("python -u ./src/credit_main.py", creationflags=0x08000000)
        door_main = subprocess.Popen("python -u ./src/door_main.py", creationflags=0x08000000)
        auth_main = subprocess.Popen("python -u ./src/auth_main.py", creationflags=0x08000000)

        # app_main = subprocess.Popen("python -u ./src/app_main.py", creationflags=0x08000000)
        app_main = subprocess.Popen("python -u ./src/adult_app_main.py", creationflags=0x08000000)

        re_time = datetime.datetime.now()

        while app_main.poll() is None:
            if auth_main.poll() is not None:
                t_time = datetime.datetime.now()
                interval = t_time - re_time
                if interval.total_seconds() > 60:
                    auth_main = subprocess.Popen("python -u ./src/auth_main.py", creationflags=0x08000000)
                    log_time = t_time.strftime("%Y-%m-%d-%H:%M:%S")
                    logger.info(f'[{log_time}] [auth_main.py RESTART]')
                    rd.set('msg', 'auth_fail')
                    re_time = t_time
            time.sleep(5)

        app_main.wait()
    finally:
        app_main.terminate()
        app_main.kill()
        credit_main.terminate()
        credit_main.kill()
        door_main.terminate()
        door_main.kill()
        auth_main.terminate()
        auth_main.kill()
