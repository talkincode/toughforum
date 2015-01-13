#!/usr/bin/env python
#coding=utf-8
import sys
sys.path.insert(0,"..")
from tornweb.webutils import route,authenticated
from tornweb.utils import md5hash,get_uuid,get_currtime
from .base import BasicHandler
from tornweb.base import ApiMessage
from tornweb.btform import webform,rules
from tornweb.btform.rules import input_style,button_style
from tornado import gen
from hashlib import sha1
from tornado.util import ObjectDict
from tornado.options import options
from tornado.web import asynchronous
from lib.mpsai import AI
from lib import mpsmsg
from lib.mps_process import MsgProcess


ACCESS_TOKEN = ''
TOKEN_TIMEOUT = 0


@route("/mps")
class IndexHandler(BasicHandler):
    """ 微信消息主要处理控制器 """

    def check_xsrf_cookie(self):
        pass

    def get_error_html(self, status_code=500, **kwargs):
        """ 定制微信消息错误返回 """
        self.set_header("Content-Type", "application/xml;charset=utf-8")
        if self.touser and self.fromuser:
            reply = mpsmsg.reply_text(self.touser,self.fromuser,'回复h查看帮助。')
            self.write(reply)

    def check_signature(self):
        """ 微信消息验签处理 """
        signature = self.get_argument('signature', '')
        timestamp = self.get_argument('timestamp', '')
        nonce = self.get_argument('nonce', '')
        tmparr = [self.settings['mps_token'], timestamp, nonce]
        tmparr.sort()
        tmpstr = ''.join(tmparr)
        tmpstr = sha1(tmpstr.encode()).hexdigest()
        return tmpstr == signature

    def get(self):
        echostr = self.get_argument('echostr', '')
        if self.check_signature():
            self.write(echostr)
            self.logging.info("Signature check success.")
        else:
            self.logging.warning("Signature check failed.")

    @asynchronous
    def post(self):
        """ 微信消息处理 """
        if not self.check_signature():
            self.logging.warning("Signature check failed.")
            return
        self.set_header("Content-Type", "application/xml;charset=utf-8")

        body = self.request.body
        msg = mpsmsg.parse_msg(body)
        if not msg:
            self.logging.info('Empty message, ignored')
            return

        self.logging.info('message type %s from %s with %s', msg.type,
                          msg.fromuser, body.decode("utf-8"))

        reply_msg = MsgProcess(msg, self).process()
        self.logging.info('Replied to %s with "%s"', msg.fromuser, reply_msg)

        self.write(reply_msg)
        self.finish()
