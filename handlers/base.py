#!/usr/bin/env python3

# from tornweb.webutils import authenticated
from tornweb.webutils import route
from tornweb.btform.webform import Storage
from tornweb import utils
from tornweb.paginator import Paginator
from tornweb.base import BaseHandler
from tornado.web import HTTPError,RequestHandler
from tornweb.base import ApiMessage
from mako.template import Template
from sqlalchemy.sql import exists
from logging import DEBUG
from tornado import gen
from Crypto.Cipher import AES
import binascii
import tempfile
import time
import datetime
import requests
import tornado.web
import json
import re
import upyun
import functools
import markdown2
from db_models import (CoeUser,CoeUserRalation,CoeUserPost,CoeCreditLog,
    CoeUserPostReply)
from beaker.cache import CacheManager
#############################################################################

cache = CacheManager(cache_regions={
      'short_term':{ 'type': 'memory', 'expire': 300 },
      'long_term':{ 'type': 'ext:memcached', 'url': '127.0.0.1:11211', 'expire': 3600 } 
      }) 

def markdown(src):
    ext = ['code-friendly','cuddled-lists','smarty-pants',
    'fenced-code-blocks','footnotes','metadata','tables','tag-friendly']
    return  markdown2.markdown(src,extras=ext)

##############################################################################

def encrypt(x,_key):
    if not x:return ''
    x = type(x) == str and x.encode() or x
    result =  AES.new(_key, AES.MODE_ECB).encrypt(x.ljust(len(x)+(16-len(x)%16)))
    return binascii.hexlify(result)

def decrypt(x,_key):
    if not x or len(x)%16 > 0 :return ''
    x = type(x) == str and x.encode() or x
    x = binascii.unhexlify(x)
    return AES.new(_key, AES.MODE_ECB).decrypt(x).strip()    

class CreditOpt():
    def __init__(self,name,desc,value):
        self.name = name
        self.desc = desc 
        self.value = value

credit_types = {
    'new_join' : CreditOpt('new_join','新手注册奖励',1000 ),
    'weixin_join' : CreditOpt('weixin_join','新手微信注册奖励',1000 ),
    'active_user' : CreditOpt('active_user','新手激活奖励',500 ),
    'invite_join' : CreditOpt('invite_join','（被）邀请新手奖励',200 ),
    'day_login' : CreditOpt('day_login','每日登陆奖励',30 ),
    'create_post' : CreditOpt('create_post','创建主题消费',-30 ),
    'reply_post' : CreditOpt('reply_post' , '回复主题消费',-20), 
    'get_reply_post' : CreditOpt('get_reply_post' , '主题被回复收益',20), 
}


##############################################################################

class BasicHandler(BaseHandler):
    '''基类 handler
    '''
    def __init__(self, *argc, **argkw):
        super(BasicHandler, self).__init__(*argc, **argkw)
        self.tp_lookup = self.application.g.tp_lookup
        self.db = self.application.g.db


    def write_error(self, status_code,**kwargs):
        if status_code == 404:
            return self.render_error(msg="404:页面不存在")
        elif status_code == 403:
            return self.render_error(msg="403:非法的请求")
        elif status_code == 500:
            # if options.debug:
            #     return self.render_string("error.html", msg=traceback.format_exc())
            return self.render_error(msg="500:服务器处理失败，请联系管理员")
        else:
            super(BaseHandler, self).write_error(status_code, **kwargs)

    def render(self, template_name, **template_vars):
        html = self.render_string(template_name, **template_vars)
        self.write(html)

    def render_error(self, **template_vars):
        tpl = "error.html"
        html = self.render_string(tpl, **template_vars)
        self.write(html)

    def render_string(self, template_name, **template_vars):
        template_vars["xsrf_form_html"] = self.xsrf_form_html
        template_vars["current_user"] = self.current_user
        template_vars["request"] = self.request
        template_vars["handler"] = self
        template_vars["utils"] = utils
        template_vars["markdown"] = markdown
        template_vars["system_name"] = self.application.settings['system_name']
        mytemplate = self.tp_lookup.get_template(template_name)
        return mytemplate.render(**template_vars)


    def render_from_string(self, template_string, **template_vars):
        template = Template(template_string)
        return template.render(**template_vars)    

    def get_current_user(self):
        db = self.db
        @cache.cache('find_user_by_username',expire=300)
        def find_user(username):
            return db.query(CoeUser).filter(CoeUser.username==username.decode()).first()
        username = self.get_secure_cookie("username")
        last_login = self.get_secure_cookie("last_login")
        if not username: return None
        user = find_user(username)
        if not user:return None
        session_user = Storage()
        session_user['username'] = user.username
        session_user['nickname'] = user.nickname
        session_user['credit'] = user.credit
        session_user['headurl'] = user.headurl or ''
        session_user['email'] = user.email
        session_user['signature'] = user.signature
        session_user['realname'] = user.realname
        session_user['is_admin'] = False
        session_user['actived'] = user.actived
        if user and user.email == self.settings['admin_email']:
            session_user['is_admin'] = True

        if not last_login or (datetime.datetime.now() - datetime.datetime.strptime(last_login.decode(),'%Y-%m-%d')).days >= 1:
            user = self.db.query(CoeUser).filter(CoeUser.username==username.decode()).first()
            user.credit = user.credit +  credit_types['day_login'].value
            clog = CoeCreditLog()
            clog.username = user.username
            clog.op_type = credit_types['day_login'].name
            clog.op_desc = credit_types['day_login'].desc
            clog.credit_val = credit_types['day_login'].value
            clog.balance = user.credit
            clog.created = utils.get_currtime()
            self.db.add(clog)
            self.db.commit()
            self.set_secure_cookie("last_login", utils.get_currdate(), expires_days=1)

        return session_user

    @cache.cache('get_user_head',expire=3600)
    def get_user_head(self,username):
        ''' 获取用户头像 @todo 需要缓存'''
        return self.db.query(CoeUser.headurl).filter(CoeUser.username==username).scalar()

    @cache.cache('get_nickname',expire=3600)
    def get_nickname(self,username):
        user = self.db.query(CoeUser).filter(CoeUser.username==username).first()
        return user.nickname or user.username

    @cache.cache('get_user_follows',expire=3600)    
    def get_user_follows(self,username):
        ''' 获取用户关注的用户 @todo 需要缓存'''
        return [ uf[0] for uf in self.db.query(CoeUserRalation.target_user).filter(
                CoeUserRalation.username==username,
                CoeUserRalation.is_follow==1
            ).limit(1000)]

    @cache.cache('get_user_blocks',expire=3600)
    def get_user_blocks(self,username):
        ''' 获取用户屏蔽的用户 @todo 需要缓存'''
        return [ ub[0] for ub in self.db.query(CoeUserRalation.target_user).filter(
                CoeUserRalation.username==username,
                CoeUserRalation.is_block==1
            ).limit(1000)]

    @cache.cache('get_user_post_collects',expire=3600)
    def get_user_post_collects(self,username):
        ''' 获取用户收藏的主题 @todo 需要缓存'''
        return [ pid[0] for pid in self.db.query(CoeUserPost.post_id).filter(
                CoeUserPost.username==username,
                CoeUserPost.is_collect==1
            ).limit(1000)]

    @cache.cache('get_user_post_ignores',expire=3600)
    def get_user_post_ignores(self,username):
        ''' 获取用户忽略的主题 @todo 需要缓存'''
        return [ pid[0] for pid in self.db.query(CoeUserPost.post_id).filter(
                CoeUserPost.username==username,
                CoeUserPost.is_ignore==1
            ).limit(1000)]

    @cache.cache('get_user_postreply_ignores',expire=3600)
    def get_user_postreply_ignores(self,username):
        ''' 获取用户忽略的主题回复 @todo 需要缓存'''
        return [ pid[0] for pid in self.db.query(CoeUserPostReply.reply_id).filter(
                CoeUserPostReply.username==username,
                CoeUserPostReply.is_ignore==1
            ).limit(1000)]

    @cache.cache('get_user_book_collects',expire=3600)
    def get_user_book_collects(self,username):
        ''' 获取用户收藏的笔记本 @todo 需要缓存'''
        return [ pid[0] for pid in self.db.query(CoeUserBook.book_id).filter(
                CoeUserBook.username==username,
                CoeUserBook.is_collect==1
            ).limit(1000)]

    @cache.cache('get_user_book_ignores',expire=3600)
    def get_user_book_ignores(self,username):
        ''' 获取用户忽略的笔记本 @todo 需要缓存'''
        return [ pid[0] for pid in self.db.query(CoeUserBook.book_id).filter(
                CoeUserBook.username==username,
                CoeUserBook.is_ignore==1
            ).limit(1000)]

    @cache.cache('get_user_bookreply_ignores',expire=3600)
    def get_user_bookreply_ignores(self,username):
        ''' 获取用户忽略的笔记本回复 @todo 需要缓存'''
        return [ pid[0] for pid in self.db.query(CoeUserBookReply.reply_id).filter(
                CoeUserBookReply.username==username,
                CoeUserBookReply.is_ignore==1
            ).limit(1000)]

    def sendmail(self,subject,html,tos=[]):
        return requests.post(
            self.settings['mail_api_url'],
            auth=("api", self.settings['mail_api_key']),
            data={"from": self.settings['mail_from'],
                  "to": tos,
                  "subject": subject,
                  "text": html})

    def upload_image(self, request):
        settings = self.settings
        username = self.get_argument("username","system")
        def _upload_yun_img(imgfile,dest_name):
            _space = settings['upyun_space']
            _user = settings['upyun_user']
            _pwd = settings['upyun_pwd']
            _server = settings['upyun_server']
            up = upyun.UpYun(_space, _user, _pwd, timeout=30, endpoint=upyun.ED_TELECOM)
            res = up.put('/%s/%s/%s'%(_space,username,dest_name), imgfile)      
            return "%s/%s/%s/%s" % (_server,_space,username,dest_name)    

        form_file = request.files['Filedata'][0]
        tf = tempfile.NamedTemporaryFile("w+b", delete=True)
        tf.write(form_file['body'])
        tf.seek(0)
        dstname = str(int(time.time())) + '.' + form_file['filename'].split('.').pop()
        imgurl = _upload_yun_img(tf.file,dstname)
        tf.close()
        return imgurl


    def filterRes(self,src,thumb='720mark'):
        settings = self.settings
        #filter innner image
        def _filter_img(value):
            imgs = re.findall('(%s/static/res/[a-zA-Z0-9]+.[a-zA-Z]{3})\s?'%settings['server_base'], value)
            for img in imgs:
                value = value.replace(img, '<a href="' + img + '" target="_blank"><img src="' + img + '" class="post-img" border="0" /></a>')
            
            imgs = re.findall('(%s/%s/([a-zA-Z0-9]+/)?[a-zA-Z0-9]+.[a-zA-Z]{3})\s?'%(settings['upyun_server'],settings['upyun_space']), value)
            for img in imgs:
                value = value.replace(img[0], '<a href="' + img[0] + '" target="_blank"><img src="' + img[0] + '!'+ thumb +'" class="post-img" border="0" /></a>')

            # src from v2ex https://github.com/livid/v2ex/blob/master/v2ex/templatetags/filters.py
            imgs = re.findall('(http://ww[0-9]{1}.sinaimg.cn/[a-zA-Z0-9]+/[a-zA-Z0-9]+.[a-z]{3})\s?', value)
            for img in imgs:
                value = value.replace(img, '<a href="' + img + '" target="_blank"><img src="' + img + '" class="post-img" border="0" /></a>')
            baidu_imgs = re.findall('(http://(bcs.duapp.com|img.xiachufang.com|i.xiachufang.com)/([a-zA-Z0-9\.\-\_\/]+).jpg)\s?', value)
            for img in baidu_imgs:
                value = value.replace(img[0], '<a href="' + img[0] + '" target="_blank"><img src="' + img[0] + '" class="post-img" border="0" /></a>')
            yinxiang_imgs = re.findall("(https://app.yinxiang.com/shard/.*\.(jpg|jpeg|png))\s?",value,re.IGNORECASE) 
            for img in yinxiang_imgs:
                value = value.replace(img[0], '<a href="' + img[0] + '" target="_blank"><img src="' + img[0] + '" class="post-img" border="0" /></a>')

            return value

        # filter video
        def _filter_tudou(value):
            videos = re.findall('(http://www.tudou.com/programs/view/[a-zA-Z0-9\=]+/)\s?', value)
            if (len(videos) > 0):
                for video in videos:
                    video_id = re.findall('http://www.tudou.com/programs/view/([a-zA-Z0-9\=]+)/', video)
                    value = value.replace('http://www.tudou.com/programs/view/' + video_id[0] + '/', '<embed src="http://www.tudou.com/v/' + video_id[0] + '/" quality="high" width="638" height="420" align="middle" allowScriptAccess="sameDomain" type="application/x-shockwave-flash"></embed>')
                return value
            else:
                return value    

        def _filter_youku(value):
            videos = re.findall('(http://v.youku.com/v_show/id_[a-zA-Z0-9\=]+.html)\s?', value)
            if (len(videos) > 0):
                for video in videos:
                    video_id = re.findall('http://v.youku.com/v_show/id_([a-zA-Z0-9\=]+).html', video)
                    value = value.replace('http://v.youku.com/v_show/id_' + video_id[0] + '.html', '<embed src="http://player.youku.com/player.php/sid/' + video_id[0] + '/v.swf" quality="high" width="638" height="420" align="middle" allowScriptAccess="sameDomain" type="application/x-shockwave-flash"></embed>')
                return value
            else:
                return value     

        value = _filter_img(src)
        value = _filter_youku(value)
        value = _filter_tudou(value)
        return value.replace("\n","<br>")      

    def get_1img_from_content(self,value):
        imgs = re.findall('(%s/%s/([a-zA-Z0-9]+/)?[a-zA-Z0-9]+.[a-z]{3})\s?'%(self.settings['upyun_server'],self.settings['upyun_space']), value)
        return len(imgs) > 0 and imgs[0][0] or ''

    def encrypt_username(self,username):
        if not username:return None
        return encrypt(username,self.settings['openid_aes_key']).decode()

    def decrypt_username(self,dest):
        if not dest:return None
        return decrypt(dest.encode(),self.settings['openid_aes_key']).decode()

    def encrypt_otoken(self,openid):
        prefix = utils.get_currdate()
        return encrypt("%s:%s"%(prefix,openid),self.settings['openid_aes_key']).decode()

    def check_otoken(self,otoken):
        if not otoken:return None
        _src = decrypt(otoken.encode(),self.settings['openid_aes_key']).decode()
        _array = _src.split(":")
        if len(_array) !=2:
            return None
        prefix = _array[0]
        openid = _array[1]
        # if prefix != utils.get_currdate():
        #     return None
        if (datetime.datetime.now() - datetime.datetime.strptime(prefix,'%Y-%m-%d')).days > 15:
            return None
        if not self.db.query(exists().where(CoeUser.username == openid)).scalar():
            return None
        return openid



@route("/404.html")
class NotFoundHandler(BasicHandler):
    def get(self):
        self.write_error(404)
    
class PageNotFoundHandler(RequestHandler):

    def initialize(self, status_code):
        self.set_status(status_code)    

    def get(self,**kwargs):
        self.redirect("/404.html", permanent=False)

tornado.web.ErrorHandler = PageNotFoundHandler


