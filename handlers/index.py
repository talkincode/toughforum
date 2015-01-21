#!/usr/bin/env python3

from tornweb.webutils import route,authenticated
from tornweb.utils import md5hash,get_uuid,get_currtime,get_currdate
from .base import BasicHandler,credit_types,cache
from tornweb.base import ApiMessage
from tornweb.btform import webform,rules
from tornweb.btform.rules import input_style,button_style
from tornado import gen
from db_models import CoeUser,CoeNode,CoePost,CoeOption,CoeCreditLog,CoeInvite
from sqlalchemy.sql import exists

login_form = webform.Form(
    webform.Textbox("username", rules.is_alphanum3(6, 32), description=u"用户名", size=32,required="required",**input_style),
    webform.Password("password", rules.len_of(1,32), description=u"登录密码", size=32, required="required",**input_style),
    webform.Button("submit", type="submit", html=u"<b>登陆</b>", **button_style),
    webform.Hidden("next",value="/"),
    action="/login",
    title=u"用户登陆"
)

join_form = webform.Form(
    webform.Textbox("username", rules.is_alphanum3(6, 32), description=u"用户名", size=32,required="required",**input_style),
    webform.Password("password", rules.len_of(1,32), description=u"登录密码", size=32, required="required",**input_style),
    webform.Textbox("email", rules.is_email, description=u"电子邮箱", size=64,required="required",**input_style),
    webform.Button("submit", type="submit", html=u"<b>注册</b>", **button_style),
    action="/join",
    title=u"用户注册"
)


@route("/")
class IndexHandler(BasicHandler):

    @cache.cache('find_all_posts',expire=600)
    def find_all_posts(self):
        return self.db.query(CoePost).order_by(CoePost.created.desc())

    def get(self,template_vars={}):
        nodes = self.db.query(CoeNode).filter(CoeNode.is_top==1).all()
        post_query = self.find_all_posts()
        page_data = self.get_page_data(post_query)
        self.render("index.html",nodes=nodes,page_data=page_data)

@route("/login")
class LoginHandler(BasicHandler):
    def get(self,template_variables={}):
        form = login_form()
        form.next.set_value(self.get_argument('next','/'))
        self.render("login.html",form=form)

    def post(self):
        next = self.get_argument("next", "/")
        form = login_form()
        if not form.validates(source=self.get_params()):
            self.render("login.html", form=form)
            return

        user = self.db.query(CoeUser).filter(
            CoeUser.username == form.d.username,
            CoeUser.password == md5hash(form.d.password.encode())
        ).first()

        if not user:
            return self.render("login.html",form=form,msg=u"用户名密码不符合")
        else:
            _curday = get_currdate()
            day_clog = self.db.query(CoeCreditLog).filter(
                CoeCreditLog.op_type == 'day_login',
                CoeCreditLog.username == user.username,
                CoeCreditLog.created >= _curday + ' 00:00:00',
                CoeCreditLog.created <= _curday + ' 23:59:59'
                ).first()

            if not day_clog:
                user.credit = user.credit +  credit_types['day_login'].value
                clog = CoeCreditLog()
                clog.username = user.username
                clog.op_type = credit_types['day_login'].name
                clog.op_desc = credit_types['day_login'].desc
                clog.credit_val = credit_types['day_login'].value
                clog.balance = user.credit
                clog.created = get_currtime()
                self.db.add(clog)   
                self.db.commit()         

        self.set_secure_cookie("username", form.d.username, expires_days=30)
        self.redirect(next, permanent=False)


@route("/logout")
class LogoutHandler(BasicHandler):
    def get(self,template_variables={}):
        self.clear_cookie("username")
        self.redirect("/", permanent=False)



@route("/join")
class JoinHandler(BasicHandler):
    def get(self,template_variables={}):
        form = join_form()
        ref = self.get_argument("r",None)
        self.render("join.html",form=form,ref=ref)

    def post(self):
        form = join_form()
        if not form.validates(source=self.get_params()):
            self.render("join.html", form=form)
            return

        if self.db.query(exists().where(CoeUser.username == form.d.username)).scalar():
            self.render("join.html",form=form,msg=u"用户{0}已被使用".format(form.d.username))
            return

        if self.db.query(exists().where(CoeUser.email == form.d.email)).scalar():
            self.render("join.html",form=form,msg=u"用户邮箱{0}已被使用".format(form.d.email))
            return
        
        user = CoeUser()
        user.username = form.d.username
        user.password = md5hash(form.d.password.encode())
        user.email = form.d.email
        user.created = get_currtime()
        user.actived = 0
        user.active_code = get_uuid() 
        user.credit = credit_types['new_join'].value
        user.is_ignore = 0
        user.headurl = self.settings['default_head']
        self.db.add(user)

        clog = CoeCreditLog()
        clog.username = user.username
        clog.op_type = credit_types['new_join'].name
        clog.op_desc = credit_types['new_join'].desc
        clog.credit_val = credit_types['new_join'].value
        clog.balance = user.credit
        clog.created = get_currtime()
        self.db.add(clog)

        ref = self.get_argument("ref",None)
        print(ref)
        if ref:
            cui = self.db.query(CoeInvite).filter(CoeInvite.invite_code==ref).first() 
            print(cui)
            if cui :
                cui.invite_hit = cui.invite_hit + 1
                cui.invite_total = cui.invite_total + 1
                #邀请码主任获取奖励,被系统忽略屏蔽的用户邀请都没有奖励
                ref_user = self.db.query(CoeUser).filter(CoeUser.username==cui.username).first()
                print(ref_user)
                if ref_user and ref_user.is_ignore == 0:
                    ref_user.credit = ref_user.credit + credit_types['invite_join'].value
                    clog1 = CoeCreditLog()
                    clog1.username = cui.username
                    clog1.op_type = credit_types['invite_join'].name
                    clog1.op_desc = credit_types['invite_join'].desc
                    clog1.credit_val = credit_types['invite_join'].value
                    clog1.balance = ref_user.credit
                    clog1.created = get_currtime()
                    self.db.add(clog1)

                    user.credit = user.credit + credit_types['invite_join'].value
                    clog2 = CoeCreditLog()
                    clog2.username = user.username
                    clog2.op_type = credit_types['invite_join'].name
                    clog2.op_desc = credit_types['invite_join'].desc
                    clog2.credit_val = credit_types['invite_join'].value
                    clog2.balance = user.credit
                    clog2.created = get_currtime()
                    self.db.add(clog2)

        ui = CoeInvite()
        ui.username = user.username
        ui.invite_code = get_uuid()
        ui.invite_hit = 0
        ui.invite_total = 0
        ui.created = get_currtime()
        self.db.add(ui)

        self.db.commit()

        self.set_secure_cookie("username", user.username, expires_days=30)
        self.render("message.html",msg=u"注册成功,请前往您的邮箱根据激活邮件提示完成账号激活!")
        try:
            self.sendmail('%s,请验证您在%s注册的电子邮件地址'%(user.username,self.settings['system_name'])
                self.render_string("mail.html",user=user)
                tos=[user.email])
        except :
            self.logging.exception("发送注册邮件至<%s>出错"%user.email)


@route("/active/(.*)")
class ActiveHandler(BasicHandler):
    def get(self,active_code,template_variables={}):

        user = self.db.query(CoeUser).filter(
            CoeUser.active_code == active_code,
        ).first()

        if not user:
            self.render_error(msg="无效的激活码")

        if user.actived == 1:
            self.render_error(msg="用户已经激活")

        user.actived = 1
        user.credit = user.credit + credit_types['active_user'].value

        clog = CoeCreditLog()
        clog.username = user.username
        clog.op_type = credit_types['active_user'].name
        clog.op_desc = credit_types['active_user'].desc
        clog.credit_val = credit_types['active_user'].value
        clog.balance = user.credit
        clog.created = get_currtime()
        self.db.add(clog)

        self.db.commit()
        self.render("message.html",msg=u"恭喜您，激活成功，你现在可以自由的发表主题了。")










        
                 