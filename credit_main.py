# Made by Kim.Seung.Hwan / ksana1215@interminds.ai
# -*- coding: utf-8 -*-
import requests
import json
import redis
import logging
import datetime
import urllib3
# import config
import request_main
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

cf_path = config['path']['path']
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(filename=cf_path + 'kiosk_status.log', level=logging.DEBUG)
logger = logging.getLogger('EZRes_LOG')
rd = redis.StrictRedis(host='localhost', port=6379, db=0)

#카드 삽입 체크
def ck_check():
    insert_ck = requests.post('http://localhost:8090/?callback=jsonp12345678983543344&REQ=CK')
    insert_data = json.loads(insert_ck.text[insert_ck.text.index('(') + 1: insert_ck.text.rindex(')')].replace("'", '"'))
    insert_check = insert_data["MSG"]
    return insert_check

#토큰 발급
def tokenRes():
    tokenRes = requests.post('http://localhost:8090/?callback=jsonp12345678983543344&REQ=TR^^F^^^^^^^^^30^^^^TK^^^^^^^^^^^^^^^^^')
    tokenRes.raise_for_status()
    tokenRes.encoding = 'UTF-8'
    token_data = json.loads(tokenRes.text[tokenRes.text.index('(') + 1: tokenRes.text.rindex(')')].replace("'", '"'))
    logger.info("==" * 5 + "TokenRes Result" + "==" * 5)
    logger.info(log_time)
    logger.info(token_data)
    if token_data["SUC"] != '00':
        rd.set('msg','003')
        logger.info('fail')
    if token_data["SUC"] == '00' and token_data["RS04"]=='8001' and token_data["RS31"].strip() == 'M':
        rd.set('msg', 'sspay_deny')
        logger.info("==" * 5 + "삼성페이 거절" + "==" * 5)
        logger.info(log_time)
    if token_data["SUC"] == '00' and token_data['RS04'] == '0000' and token_data["RS31"].strip() == 'M':
        rd.set('msg', 'sspay_deny')
        logger.info("==" * 5 + "모바일 결제 거절" + "==" * 5)
        logger.info(log_time)
    if token_data["SUC"] == '00' and token_data['RS04'] == '0000' and token_data["RS31"].strip() != 'C':
        rd.set('msg', 'sspay_deny')
        logger.info("==" * 5 + "카드 아닌데 토큰발급됨" + "==" * 5)
        logger.info(log_time)
    if token_data["SUC"] == '00' and token_data['RS04'] != '0000' and token_data["RS31"].strip() == 'C':
        rd.set('msg', '003')
        logger.info("==" * 5 + "카드 맞는데 토큰발급 실패함" + "==" * 5)
        logger.info(log_time)
    if token_data["SUC"] == '00' and token_data['RS04'] != '0000' and token_data["RS31"].strip() != 'C':
        rd.set('msg', 'sspay_deny')
        logger.info("==" * 5 + "카드 아니고 토큰 발급 실패함" + "==" * 5)
        logger.info(log_time)
    if token_data["SUC"] == '00' and token_data['RS04'] == '0000' and token_data["RS31"].strip() == 'C':
        if token_data['RS11'] == '027' or  token_data['RS11'] == '006':
                rd.set('msg', 'hh_deny')
                logger.info("==" * 5 + "하나/현대카드 수기특약 거절" + "==" * 5)
                logger.info(log_time)
        else:
            rd.set('token', token_data['RS17'])
            token = rd.get('token').decode('utf-8')
            re_text = f'http://localhost:8090/?callback=jsonp12345678983543344&REQ=D1^^(repay)^00^^^^^^^^30^A^^^^^^^^^^^^^^^^^^^^TOKNKIC{token}^^^^'
            logger.info("==" * 5 + "재승인 Request" + "==" * 5)
            logger.info(log_time)
            logger.info(re_text)
            if token_data['RS34'] == 'N':
                # 신용카드는 직행
                rd.set('msg', 'remove')
                rd.set('method', 'credit')
                logger.info(log_time)
            elif token_data['RS34'] == 'Y':
                # 체크카드 가승인 승인/취소
                provis_text = f'http://localhost:8090/?callback=jsonp12345678983543344&REQ=D1^^30000^00^^^^^^^^30^A^^^^^^^^^^^^^^^^^^^^TOKNKIC{token}^^^^'
                provisRes = requests.post(provis_text)
                provisRes.raise_for_status()
                provisRes.encoding = 'UTF-8'
                provis_data = json.loads(provisRes.text[provisRes.text.index('(') + 1: provisRes.text.rindex(')')].replace("'", '"'))
                logger.info("==" * 5 + "체크카드 선승인 Request" + "==" * 5)
                logger.info(log_time)
                logger.info(provis_data)
                if provis_data['RS04'] == '0000':
                    rd.set('ap', provis_data['RS09'])
                    rd.set('cd', provis_data['RS08'])
                    rd.set('msg', 'remove')
                    rd.set('method', 'check')
                    logger.info("==" * 5 + "체크카드 선승인 SUCCESS" + "==" * 5)
                    logger.info(provis_data)
                    logger.info(log_time)
                elif provis_data['RS04'] == '8035':
                    rd.set('msg', 'no_money')
                    logger.info("==" * 5 + "카드 잔액 부족" + "==" * 5)
                    logger.info(log_time)
                else:
                    rd.set('msg','003')
                    logger.info("==" * 5 + "선승인 요청 Fail" + "==" * 5)
                    logger.info(log_time)

            
#체크카드 선승인 취소
def cancelProvis():
    if method == b'check':
        # 가승인 취소
        app_no = rd.get('ap').decode('utf-8')
        card_no = rd.get('cd').decode('utf-8')
        cancel_text = f'http://localhost:8090/?callback=jsonp12345678983543344&REQ=D4^^30000^^{refund_time}^{app_no}^^^^^^20^A^^^^^^^{card_no}^^^^^^^^^^^^^^^^^'
        cancelRes = requests.post(cancel_text)
        cancelRes.raise_for_status()
        cancelRes.encoding = 'UTF-8'
        logger.info("==" * 5 + "선승인 취소 전문" + "==" * 5)
        logger.info(cancel_text)
        logger.info("==" * 5 + "선승인 취소 Success" + "==" * 5)
        logger.info(cancelRes.text)

#본결제
def payment():
    order_list = rd.get('ol')
    order_list = json.loads(order_list)
    tp = []
    for order_list in order_list:
        price = int(order_list['goodsPrice']) * int(order_list['goodsCnt'])
        tp.append(price)
    total_price = sum(tp)
    if int(total_price) > 0:
        token = rd.get('token').decode('utf-8')
        res_text = f'http://localhost:8090/?callback=jsonp12345678983543344&REQ=D1^^{total_price}^00^^^^^^^^30^A^^^^^^^^^^^^^^^^^^^^TOKNKIC{token}^^^^'
        payRes = requests.post(res_text)
        payRes.raise_for_status()
        payRes.encoding = 'UTF-8'
        pay_data = json.loads(payRes.text[payRes.text.index('(') + 1: payRes.text.rindex(')')].replace("'", '"'))
        if pay_data['RS04'] == '0000':
            rd.set('msg', 'end')
            approve_no = pay_data['RS09']
            card_no = pay_data['RS08']
            logger.info("==" * 5 + "결제 성공" + "==" * 5)
            logger.info(log_time)
            logger.info(pay_data)
            logger.info("==" * 5 + "환불 Request" + "==" * 5)
            refund_param = f'http://localhost:8090/?callback=jsonp12345678983543344&REQ=D4^^{total_price}^^{refund_time}^{approve_no}^^^^^^20^A^^^^^^^{card_no}^^^^^^^^^^^^^^^^^'
            logger.info(log_time)
            logger.info(refund_param)
        elif pay_data['RS04'] == '8035':
            rd.set('msg', 'no_money')
            logger.info("==" * 5 + "체크카드 잔액부족" + "==" * 5)
            logger.info(log_time)
        elif pay_data['RS04'] == '8350':
            rd.set('msg', '003')
            logger.info("==" * 5 + "도난 분실카드" + "==" * 5)
            logger.info(log_time)
        else:
            rd.set('msg', '003')
    rd.delete('ap')
    rd.delete('cd')
    rd.delete('token')
    rd.delete('method')

#루프
while True:
    log_time = datetime.datetime.now()
    log_time = log_time.strftime("%Y-%m-%d-%H:%M:%S")
    refund_time = datetime.datetime.now()
    refund_time = refund_time.strftime("%y%m%d")
    try:
        msg = rd.get('msg')
        nowPage = rd.get('nowPage')
        method = rd.get('method')
        if msg is None:
            pass
        #토큰 발급
        elif msg == b'card':
            tokenRes()
        #체크카드일경우 가승인 취소
        elif msg == b'shopping':
            cancelProvis()
        #본결제 승인
        elif msg == b'cal':
            payment()
        #카드 제거 반복
        if nowPage == b'remove':
            if ck_check() == '011':
                rd.set('door', 'open')
                rd.set('msg', 'shopping')
                rd.set('nowPage', 'shopping')
                logger.info("==" * 5 + "카드 제거" + "==" * 5)
                logger.info(log_time)
            elif ck_check() == '010':
                ck_check()
                rd.set('msg', 'remove')
    except Exception as err:
        rd.set('msg', '003')
        request_main.device_err()
        logger.info("==" * 5 + 'PAYMENT FAIL' + "==" * 5)
        logger.info(err)
        #break
