#coding:utf-8
import logging
import requests
import json
import time
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from tornweb.base import ApiMessage

class MpsApi:

    def __init__(self):
        # self.api_address = "http://mpsapi.lingyatech.net"
        self.api_address = "https://api.weixin.qq.com"
        self.oauth_address = "https://open.weixin.qq.com"
        self.upload_address = "http://file.api.weixin.qq.com"


    def wx_gettoken_url(self):
        return '%s/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % \
               (self.api_address,settings['mps_appid'], settings['mps_secret'])     

    def wx_userinfo_url(self,openid):
        return '%s/cgi-bin/user/info?access_token=%s&openid=%s&lang=zh_CN'% \
        (self.api_address,self.get_mps_token(), openid)

    def wx_send_custommsg_url(self):
        return '%s/cgi-bin/message/custom/send?access_token=%s' % \
        (self.api_address,self.get_mps_token())

    def wx_sync_user_url(self):
        return '%s/cgi-bin/user/get?access_token=%s'%\
                (self.api_address,self.get_mps_token())

    def get_mps_token(self):
        _url = self.wx_gettoken_url()
        mps_access_token = settings.get('mps_access_token')
        if not mps_access_token:
            _resp = requests.get(_url)
            _json_obj = _resp.json()
            mps_access_token = _json_obj.get('access_token')
            mps_access_token_expires = time.time() + 6000
            if mps_access_token:
                logging.info('get a new access_token: ' + mps_access_token)
                settings['mps_access_token'] = mps_access_token_expires
                settings['mps_access_token_expires'] = mps_access_token_expires
        else:
            if "mps_access_token_expires" not in settings \
                    or settings['mps_access_token_expires'] < time.time():
                settings['mps_access_token'] = ''
                return self.get_mps_token()

        return mps_access_token    

 
    def get_weixin_user(self,openid):
        wxu_url = self.wx_userinfo_url(openid)
        wxu_resp = requests.get(wxu_url)
        return json.loads(wxu_resp.text)

    def send_customer_text_msg(self,openid,msg):
        wxu_url = self.wx_send_custommsg_url()
        logging.info(wxu_url)
        _msg = dict(touser=openid, msgtype='text', text={'content': msg})
        _msg = json.dumps(_msg, ensure_ascii=False)
        return requests.post(wxu_url,_msg.encode("utf-8"))

    @gen.coroutine
    def send_customer_text_async(self,openid,msg):
        _url = self.wx_send_custommsg_url()
        _msg = dict(touser=openid, msgtype='text', text={'content': msg})
        _msg = json.dumps(_msg, ensure_ascii=False)
        _headers = {"Content-Type": "application/json;charset=utf-8"}
        _params = dict(method='POST', headers=_headers, use_gzip=True,
                       body=_msg, connect_timeout=300, request_timeout=300)
        resp = yield AsyncHTTPClient().fetch(_url, **_params)
        rdata = json.loads(resp.body)
        if resp.code != 200 or 'errcode' in rdata > 0:
            return gen.Return(ApiMessage(code=resp.code, msg=resp.reason))
        else:
            apiresp = ApiMessage()
            apiresp.rdata=rdata
            apiresp.code=0
            apiresp.msg='success'
            return gen.Return(apiresp)

    @gen.coroutine
    def send_customer_news_async(self,openid,title,description,url='',pic_url=''):
        _url = self.wx_send_custommsg_url()
        _msg = dict(touser=openid, msgtype='news', news={'articles': [{"title":title,"description":description,"url":url, "picurl":pic_url}]})
        _msg = json.dumps(_msg, ensure_ascii=False)
        _headers = {"Content-Type": "application/json;charset=utf-8"}
        _params = dict(method='POST', headers=_headers, use_gzip=True,
                       body=_msg, connect_timeout=300, request_timeout=300)
        resp = yield AsyncHTTPClient().fetch(_url, **_params)
        rdata = json.loads(resp.body)
        if resp.code != 200 or 'errcode' in rdata > 0:
            return gen.Return(ApiMessage(code=resp.code, msg=resp.reason))
        else:
            apiresp = ApiMessage()
            apiresp.rdata=rdata
            apiresp.code=0
            apiresp.msg='success'
            return gen.Return(apiresp)

    @gen.coroutine
    def get_wx_user_info(self,openid):
        _url = self.wx_userinfo_url(openid)
        _headers = {"Content-Type": "application/json;charset=utf-8"}
        _params = dict(headers=_headers, use_gzip=True,connect_timeout=300, request_timeout=300)
        resp = yield AsyncHTTPClient().fetch(_url, **_params)
        rdata = json.loads(resp.body)
        if resp.code != 200 or 'errcode' in rdata > 0:
            return gen.Return(ApiMessage(code=resp.code, msg=resp.reason))
        else:
            apiresp = ApiMessage()
            apiresp.rdata=rdata
            apiresp.code=0
            apiresp.msg='success'
            return  gen.Return(apiresp)


mpsapi = MpsApi() 
