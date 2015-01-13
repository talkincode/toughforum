#!/usr/bin/env python3

from tornweb.webutils import route,authenticated,auth_admin
from tornweb.utils import md5hash,get_uuid,get_currtime
from .base import BasicHandler,credit_types
from tornweb.base import ApiMessage
from tornweb.btform import webform,rules
from tornweb.btform.rules import input_style,button_style
from tornado import gen
from db_models import CoeOption,CoeUser,CoeCreditLog



@route('/manage/users')
class UsersHandler(BasicHandler):

    @auth_admin
    def get(self, template_variables={}):
        users = self.db.query(CoeUser).order_by(CoeUser.created.desc())
        page_data = self.get_page_data(users)
        self.render("manage/users.html",page_data=page_data)


@route("/manage/active/(.*)")
class UserActiveHandler(BasicHandler):

    @auth_admin
    def post(self,username,templates_vars={}):
        user = self.db.query(CoeUser).filter(
            CoeUser.username == username,
        ).first()

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

        self.render_json(msg="激活成功")        
