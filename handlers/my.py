#!/usr/bin/env python3

from tornweb.webutils import route,authenticated
from tornweb.utils import md5hash,get_uuid,get_currtime
from .base import BasicHandler
from tornweb.base import ApiMessage
from tornweb.btform import webform,rules
from tornweb.btform.rules import input_style,button_style
from tornado import gen
from db_models import CoeUser,CoeNode,CoePost,CoeCreditLog
from sqlalchemy.sql import exists

@route("/my/posts")
class PostsHandler(BasicHandler):

    @authenticated
    def get(self,template_vars={}):
        upcs = self.get_user_post_collects(self.current_user.username)
        post_query = self.db.query(CoePost).filter(
            CoePost.post_id.in_(upcs)
            ).order_by(CoePost.created.desc())
        page_data = self.get_page_data(post_query)
        self.render("myposts.html",page_data=page_data)

@route("/my/follows")
class FollowsHandler(BasicHandler):

    @authenticated
    def get(self,template_vars={}):
        ufs = self.get_user_follows(self.current_user.username)
        post_query = self.db.query(CoePost).filter(
            CoePost.username.in_(ufs)
            ).order_by(CoePost.created.desc())
        page_data = self.get_page_data(post_query)
        self.render("myfollows.html",page_data=page_data)        


@route('/my/credit/log')
class MyCreditLogHandler(BasicHandler):

    @authenticated
    def get(self, template_variables={}):
        clogs = self.db.query(CoeCreditLog).filter(
                CoeCreditLog.username == self.current_user.username
            ).order_by(CoeCreditLog.created.desc())
        page_data = self.get_page_data(clogs)
        self.render("credit_log.html",page_data=page_data)    



