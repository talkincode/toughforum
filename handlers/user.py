#!/usr/bin/env python3

from tornweb.webutils import route,authenticated,auth_admin
from tornweb.utils import md5hash,get_uuid,get_currtime,thumb_img
from .base import BasicHandler,credit_types
from tornweb.base import ApiMessage
from tornweb.btform import webform,rules
from tornweb.btform.rules import input_style,button_style
from tornado import gen
from tornado.web import HTTPError
from db_models import CoeUser,CoePost,CoeUserRalation,CoeCreditLog,CoeInvite
import tempfile
import time
import os

profile_form = webform.Form(
    webform.Textbox("username", rules.is_alphanum3(6, 64), description=u"用户名", size=32,readonly="readonly",**input_style),
    webform.Textbox("email", rules.is_email, description=u"电子邮箱", size=128,readonly="readonly",**input_style),
    webform.Textbox("nickname", rules.len_of(0, 64), description=u"用户昵称", size=64,**input_style),
    webform.Textbox("signature", rules.len_of(0, 256), description=u"签名", size=256,**input_style),
    webform.Button("submit", type="submit", html=u"<b>更新资料</b>", **{"class":"btn btn-default"}),
    action="/user/update",
    title=u"用户资料"
)

password_form = webform.Form(
    webform.Password("password", rules.len_of(6,32), description=u"旧密码", size=32, required="required",**input_style),
    webform.Password("password2", rules.len_of(6,32), description=u"新密码", size=32, required="required",**input_style),
    webform.Password("password22", rules.len_of(6,32), description=u"确认新密码", size=32, required="required",**input_style),
    webform.Button("submit", type="submit", html=u"<b>修改密码</b>", **{"class":"btn btn-default"}),
    action="/user/password",
    title=u"密码修改"
)


@route("/user/settings")
class SettingsHandler(BasicHandler):

    @authenticated
    def get(self,templates_vars={}):
        pf_form = profile_form()
        pwd_form = password_form()
        user = self.db.query(CoeUser).filter(CoeUser.username==self.current_user.username).first()
        pf_form.fill(user)
        uinv = self.db.query(CoeInvite).filter(CoeInvite.username == self.current_user.username).first()
        self.render("settings.html",pf_form=pf_form,pwd_form=pwd_form,uinv=uinv)

@route("/user/settings/head/upload/(.*)")
class SettingsHeadHandler(BasicHandler):
    def check_xsrf_cookie(self):
        pass
    # @authenticated
    def post(self, username,*args, **kwargs):      
        print(self.request.cookies)
        user = self.db.query(CoeUser).filter(CoeUser.username==username).first()
        if not user:
            self.write("用户不存在")
            return

        imgurl = self.upload_image(self.request)
        user.headurl = imgurl
        self.db.commit()
        self.write(imgurl)


@route("/user/update")
class UserUpdateHandler(BasicHandler):

    @authenticated
    def post(self):
        pf_form = profile_form()
        if not pf_form.validates(source=self.get_params()):
            return self.render("base_form.html",form=pf_form)

        user = self.db.query(CoeUser).filter(CoeUser.username==pf_form.d.username).first()

        if pf_form.d.nickname is not None and pf_form.d.nickname != user.nickname:
            if self.db.query(CoeUser).filter(CoeUser.nickname==pf_form.d.nickname).count() > 0:
                return self.render_error(msg="用户昵称被使用")

        user.nickname = pf_form.d.nickname
        user.signature = pf_form.d.signature
        self.db.commit()

        self.redirect('/user/settings',permanent=False)     

@route("/user/password")
class PasswordHandler(BasicHandler):

    @authenticated
    def post(self):
        pwd_form = password_form()
        if not pwd_form.validates(source=self.get_params()):
            return self.render("base_form.html",form=pwd_form)

        if pwd_form.d.password2 != pwd_form.d.password22:
            return self.render("base_form.html",form=pwd_form,msg=u"确认密码不一致")


        user = self.db.query(CoeUser).filter(CoeUser.username==username.decode()).first()
        user.passdord = md5hash(pwd_form.d.password.encode())
        self.db.commit()

        self.redirect('/user/settings',permanent=False)             

@route("/user/profile/(.*)")
class ProfileHandler(BasicHandler):

    def get(self,username,templates_vars={}):
        username = self.decrypt_username(username)
        user = self.db.query(CoeUser).filter(CoeUser.username==username).first()
        posts = self.db.query(CoePost).filter(CoePost.username==username).limit(20)
        self.render("user_profile.html",user=user,posts=posts)



@route("/user/posts/(.*)")
class UserPostsHandler(BasicHandler):

    def get(self,username,templates_vars={}):
        username = self.decrypt_username(username)
        user = self.db.query(CoeUser).filter(CoeUser.username==username).first()
        posts = self.db.query(CoePost).filter(CoePost.username==username)
        page_data = self.get_page_data(posts)
        self.render("user_posts.html",user=user,page_data=page_data)

@route("/user/follow/(.*)")
class UserFollowHandler(BasicHandler):

    @authenticated
    def post(self,username,templates_vars={}):
        if username == self.current_user.username:
            self.render_json(code=1,msg="不能follow自己")
            return

        user = self.db.query(CoeUser).filter(CoeUser.username==username).first()
        if not user:
            self.render_json(code=1,msg="用户不存在")
            return

        cur = self.db.query(CoeUserRalation).filter(
            CoeUserRalation.username == self.current_user.username,
            CoeUserRalation.target_user == username).first()

        is_new = False
        if not cur:
            cur = CoeUserRalation()
            cur.username = self.current_user.username
            cur.target_user = username
            is_new = True

        cur.is_follow = 1
        cur.is_block = 0

        if is_new:
            self.db.add(cur)

        self.db.commit()
        self.db.flush();
        self.render_json(code=0,msg="ok")


@route("/user/unfollow/(.*)")
class UserUnFollowHandler(BasicHandler):

    @authenticated
    def post(self,username,templates_vars={}):
        if username == self.current_user.username:
            self.render_json(code=1,msg="不能unfollow自己")
            return

        user = self.db.query(CoeUser).filter(CoeUser.username==username).first()
        if not user:
            self.render_json(code=1,msg="用户不存在")
            return

        cur = self.db.query(CoeUserRalation).filter(
            CoeUserRalation.username == self.current_user.username,
            CoeUserRalation.target_user == username).first()

        if not cur:
            return self.render_json(msg="ok")

        cur.is_follow = 0
        if is_new:
            self.db.add(cur)
        self.db.commit()
        self.render_json(code=0,msg="ok")
        

@route("/user/block/(.*)")
class UserBlockHandler(BasicHandler):

    @authenticated
    def post(self,username,templates_vars={}):
        if username == self.current_user.username:
            self.render_json(code=1,msg="不能block自己")
            return

        user = self.db.query(CoeUser).filter(CoeUser.username==username).first()
        if not user:
            self.render_json(code=1,msg="用户不存在")
            return

        cur = self.db.query(CoeUserRalation).filter(
            CoeUserRalation.username == self.current_user.username,
            CoeUserRalation.target_user == username).first()

        is_new = False
        if not cur:
            cur = CoeUserRalation()
            cur.username = self.current_user.username
            cur.target_user = username
            is_new = True

        cur.is_follow = 0
        cur.is_block = 1
        if is_new:
            self.db.add(cur)        
        self.db.commit()
        self.render_json(code=0,msg="ok")
        
@route("/user/unblock/(.*)")
class UserUnBlockHandler(BasicHandler):

    @authenticated
    def post(self,username,templates_vars={}):
        if username == self.current_user.username:
            self.render_json(code=1,msg="不能unblock自己")
            return

        user = self.db.query(CoeUser).filter(CoeUser.username==username).first()
        if not user:
            self.render_json(code=1,msg="用户不存在")
            return

        cur = self.db.query(CoeUserRalation).filter(
            CoeUserRalation.username == self.current_user.username,
            CoeUserRalation.target_user == username).first()

        if not cur:
            self.render_json(code=0,msg="ok")
            return

        cur.is_block = 0  
        self.db.commit()
        self.render_json(code=0,msg="ok")


@route("/user/sysblock/(.*)")
class SysBlockHandler(BasicHandler):

    @auth_admin
    def post(self,username,templates_vars={}):
        if username == self.current_user.username:
            self.render_json(code=1,msg="不能block自己")
            return

        user = self.db.query(CoeUser).filter(CoeUser.username==username).first()
        if not user:
            self.render_json(code=1,msg="用户不存在")
            return

        user.is_ignore = 1
   
        self.db.commit()
        self.render_json(code=0,msg="ok")


@route("/user/reactive")
class ReActiveHandler(BasicHandler):

    @authenticated
    def post(self,templates_vars={}):
        last_send = self.get_secure_cookie("last_send_active") 
        if last_send:
            sec = int(time.time()) - int(float(last_send))
            if sec < 60:
                return self.render_json(code=1,msg="每间隔60秒才能发送一次,还需等待%s秒"% int(60-sec))

        self.set_secure_cookie("last_send_active", str(time.time()), expires_days=1)
        user = self.db.query(CoeUser).filter(CoeUser.username==self.current_user.username).first()
        try:
            self.sendmail('%s,请验证您在印象加油站注册的电子邮件地址'%user.username,
                self.render_string("mail.html",user=user),
                tos=[user.email])
            self.render_json(code=0,msg="激活邮件已经发送")  
        except :
            self.logging.exception("发送注册邮件至<%s>出错"%user.email)
            self.render_json(code=0,msg="激活邮件发送失败") 




