#!/bin/sh
python  -u C:/Users/kwon/Desktop/ProjectTest/KIOSK_IMD/src/taskkill.py
python  -u C:/Users/kwon/Desktop/ProjectTest/KIOSK_IMD/src/auth_main.py &
python  -u C:/Users/kwon/Desktop/ProjectTest/KIOSK_IMD/src/door_main.py &
python  -u C:/Users/kwon/Desktop/ProjectTest/KIOSK_IMD/src/credit_main.py &
python  -u C:/Users/kwon/Desktop/ProjectTest/KIOSK_IMD/src/adult_app_main.py &



