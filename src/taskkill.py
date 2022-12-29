import os
import time
import request_main
request_main.release_event()
os.system('taskkill /F /im python.exe')
