# Made by Kim.Seung.Hwan / ksana1215@interminds.ai
# -*- coding: utf-8 -*-
import os

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
config.read(os.path.join(os.path.split(__file__)[0],'config.ini'))

cf_path = config['path']['path']
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(filename=cf_path + 'kiosk_status.log', level=logging.DEBUG)
logger = logging.getLogger('EZR_LOG')
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
    if token_data["SUC"] == '01':
        rd.set('msg','003')
        logger.info(f'[{log_time} | TokenRes Fail]' + '\n' +str(token_data))
    if token_data["SUC"] == '00' and token_data["RS04"]=='8001' and token_data["RS31"].strip() == 'M':
        rd.set('msg', 'sspay_deny')
        logger.info(f'[{log_time} | 삼성페이 거절]')
    if token_data["SUC"] == '00' and token_data['RS04'] == '0000' and token_data["RS31"].strip() == 'M':
        rd.set('msg', 'sspay_deny')
        logger.info(f'[{log_time} | 모바일 결제 거절]')
    if token_data["SUC"] == '00' and token_data['RS04'] == '0000' and token_data["RS31"].strip() != 'C':
        rd.set('msg', 'sspay_deny')
        logger.info(f'[{log_time} | 카드 아닌데 토큰발급됨]')
    if token_data["SUC"] == '00' and token_data['RS04'] != '0000' and token_data["RS31"].strip() == 'C':
        rd.set('msg', '003')
        logger.info(f'[{log_time} | 카드 맞는데 토큰발급 실패함]')
    if token_data["SUC"] == '00' and token_data['RS04'] != '0000' and token_data["RS31"].strip() != 'C':
        rd.set('msg', 'sspay_deny')
        logger.info(f'[{log_time} | 카드 아니고 토큰 발급 실패함]')
    if token_data["SUC"] == '00' and token_data['RS04'] == '0000' and token_data["RS31"].strip() == 'C':
        if token_data['RS11'] == '027' or  token_data['RS11'] == '006':
                rd.set('msg', 'hh_deny')
                logger.info(f'[{log_time} | 하나/현대카드 수기특약 거절]')
        else:
            logger.info(f'[{log_time} | TokenRes Result]' + '\n' + f'[TID : {token_data["RQ02"]}, 응답코드 :{token_data["RS04"]}, 카드사 코드 : {token_data["RS11"]}, Token : {token_data["RS17"]}]')
            rd.set('token', token_data['RS17'])
            token = rd.get('token').decode('utf-8')
            re_text = f'http://localhost:8090/?callback=jsonp12345678983543344&REQ=D1^^(재청구금액)^00^^^^^^^^30^A^^^^^^^^^^^^^^^^^^^^TOKNKIC{token}^^^^'
            logger.info(f'[{log_time} | 재승인 요청시 전문]'+'\n'+f'[{re_text}]')
            if token_data['RS34'] == 'N':
                # 신용카드는 직행
                rd.set('msg', 'remove')
                rd.set('method', 'credit')
            elif token_data['RS34'] == 'Y':
                # 체크카드 선승인/취소
                provis_text = f'http://localhost:8090/?callback=jsonp12345678983543344&REQ=D1^^30000^00^^^^^^^^30^A^^^^^^^^^^^^^^^^^^^^TOKNKIC{token}^^^^'
                provisRes = requests.post(provis_text)
                provisRes.raise_for_status()
                provisRes.encoding = 'UTF-8'
                provis_data = json.loads(provisRes.text[provisRes.text.index('(') + 1: provisRes.text.rindex(')')].replace("'", '"'))
                if provis_data['RS04'] == '0000':
                    rd.set('ap', provis_data['RS09'])
                    rd.set('cd', provis_data['RS08'])
                    rd.set('msg', 'remove')
                    rd.set('method', 'check')
                    cancel_text = f'http://localhost:8090/?callback=jsonp12345678983543344&REQ=D4^^30000^^{refund_time}^{provis_data["RS09"]}^^^^^^20^A^^^^^^^{provis_data["RS08"]}^^^^^^^^^^^^^^^^^'
                    logger.info(f'[{log_time} | 체크카드 선승인 SUCCESS]' +'\n'+ f'[카드사 : {provis_data["RS14"]}, 선승인금액 : {provis_data["RQ07"]}, 승인번호 : {provis_data["RS09"]}, 고유거래번호 : {provis_data["RS08"]}]'+ '\n' + f'[선승인 취소 전문 : {cancel_text}]')
                elif provis_data['RS04'] == '8035':
                    rd.set('msg', 'no_money')
                    logger.info(f'[{log_time} | 카드 잔액 부족]' + '\n' + str(provis_data["RS16"]) + str(provis_data["RS17"]))
                else:
                    rd.set('msg','003')
                    logger.info(f'[{log_time} | 선승인 요청 Fail]' + '\n' + str(provis_data["RS16"]) + str(provis_data["RS17"]))

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
        cancelRes_text = json.loads(cancelRes.text[cancelRes.text.index('(') + 1: cancelRes.text.rindex(')')].replace("'", '"'))
        if cancelRes_text["RS04"] == '0000':
            logger.info(f'[{log_time} | 선승인 취소]' +'\n'+
                    f'[카드사 : {cancelRes_text["RS14"]}, 승인번호 : {cancelRes_text["RS09"]}, 고유거래번호 : {cancelRes_text["RS08"]}, 거래취소여부 : {cancelRes_text["RS04"]}]')
        else:
            logger.info(str(cancelRes_text["RS16"]) + str(cancelRes_text["RS17"]))
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
            refund_param = f'http://localhost:8090/?callback=jsonp12345678983543344&REQ=D4^^{total_price}^^{refund_time}^{pay_data["RS09"]}^^^^^^20^A^^^^^^^{pay_data["RS08"]}^^^^^^^^^^^^^^^^^'
            logger.info(f'[{log_time} | 결제 성공]' +'\n'+
                        f'[카드사 : {pay_data["RS14"]}, 결제청구액 : {pay_data["RQ07"]}, 승인번호 : {pay_data["RS09"]}, 고유거래번호 : {pay_data["RS08"]}]'+'\n'+
                        f'[본거래 취소전문 : {refund_param}]')
        elif pay_data['RS04'] == '8035':
            rd.set('msg', 'no_money')
            logger.info(f'[{log_time} | 체크카드 잔액부족]')
        elif pay_data['RS04'] == '8350':
            rd.set('msg', '003')
            logger.info(f'[{log_time} | 도난 분실카드]')
        else:
            rd.set('msg', '003')
    rd.delete('ap')
    rd.delete('cd')
    rd.delete('token')
    rd.delete('method')

#루프
while True:
    t_time = datetime.datetime.now()
    log_time = t_time.strftime("%Y-%m-%d-%H:%M:%S")
    refund_time = t_time.strftime("%y%m%d")
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
                logger.info(f'[{log_time} | 카드 제거]')
            elif ck_check() == '010':
                ck_check()
                rd.set('msg', 'remove')
    except Exception as err:
        rd.set('msg', '003')
        logger.info('[PAYMENT FAIL]')
        logger.info(err)

