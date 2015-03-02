#!/usr/bin/env python3

from tornweb.webutils import route,authenticated
from tornweb.utils import md5hash,get_uuid,get_currtime,resize_img
from .base import BasicHandler,credit_types
from tornweb.base import ApiMessage
from tornweb.btform import dataform,rules
from tornweb.btform.net import websafe
from tornweb.btform.rules import input_style,button_style
from tornado import gen
from db_models import CoeNode,CoePost,CoeReply,CoeUserPost,CoeUser,CoeCreditLog,CoePostAppend
import tempfile
import time
import os

post_add_form = dataform.Form(
    dataform.Item("topic", rules.len_of(7,255),description=u"主题描述",),
    dataform.Item("content", rules.len_of(0,8192),description=u"主题内容",),
)

post_update_form = dataform.Form(
    dataform.Item("post_id", rules.is_number,description=u"主题ID",),
    dataform.Item("topic", rules.len_of(7,255),description=u"主题描述",),
    dataform.Item("content", rules.len_of(0,8192),description=u"主题内容",),
)

@route('/post/new/(\w+)')
class NewPostHandler(BasicHandler):
    
    @authenticated
    def get(self, node_name, template_variables={}):

        if self.current_user.actived == 0:
            return self.render_error(msg="你的账号未激活，不能发表主题")

        if self.current_user.credit < abs(credit_types['create_post'].value):
            return self.render_error(msg="你的象牙币不足，无法发表主题")
                    
        node = self.db.query(CoeNode).filter(
            CoeNode.node_name==node_name
        ).first()

        if not node:
            return self.render_error(msg=u"节点不存在")

        self.render("post_add.html",node_name=node_name,node_desc=node.node_desc)

    @authenticated
    def post(self,node_name):
        form = post_add_form()
        node = self.db.query(CoeNode).filter(
            CoeNode.node_name==node_name
        ).first()        
        if not form.validates(source=self.get_params()):
            return self.render("post_add.html",
                topic=form.d.topic,
                content=form.d.content,
                node_name=node_name,
                node_desc=node.node_desc,
                msg=form.errors
            )

        post = CoePost()
        post.node_name = node_name
        post.topic = websafe(form.d.topic)
        post.content = websafe(form.d.content)
        post.created = get_currtime()
        post.username = self.current_user.username
        post.reply_count = 0
        post.is_ignore = 0
        self.db.add(post)
        node.topic_count = node.topic_count + 1

        user = self.db.query(CoeUser).filter(
            CoeUser.username == self.current_user.username
            ).first()

        user.credit = user.credit + credit_types['create_post'].value
        clog = CoeCreditLog()
        clog.username = user.username
        clog.op_type = credit_types['create_post'].name
        clog.op_desc = credit_types['create_post'].desc
        clog.credit_val = credit_types['create_post'].value
        clog.balance = user.credit
        clog.created = get_currtime()
        self.db.add(clog)

        self.db.commit()

        self.redirect("/node/{0}".format(node_name), permanent=False)


@route('/post/edit/(\d+)')
class EditPostHandler(BasicHandler):
    
    @authenticated
    def get(self, post_id, template_variables={}):
        
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render_error(msg="访问的主题不存在")
   
        node = self.db.query(CoeNode).filter(
            CoeNode.node_name==post.node_name
        ).first()

        if not node:
            return self.render_error(msg=u"节点不存在")

        self.render("post_edit.html",node=node,post_id=post_id,topic=post.topic,content=post.content)

    @authenticated
    def post(self,post_id):
        form = post_update_form()
        if not form.validates(source=self.get_params()):
            return self.render("post_edit.html",
                post_id=form.d.post_id,
                topic=form.d.topic,
                content=form.d.content,
                msg=form.errors
            )
            
        post = self.db.query(CoePost).get(post_id)
        post.topic = form.d.topic
        post.content = form.d.content

        self.db.commit()

        self.redirect("/post/{0}".format(form.d.post_id), permanent=False)


@route('/post/res/upload')
class PostImageUploadHandler(BasicHandler):
    def check_xsrf_cookie(self):
        pass

    # @authenticated
    def post(self, *args, **kwargs):
        imgurl = self.upload_image(self.request)
        self.write(imgurl)

@route("/post/(\d+)")
class PostDetailHandler(BasicHandler):

    def get(self,post_id,template_variables={}):
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render_error(msg=u"访问的主题不存在")

        node = self.db.query(CoeNode).filter(
            CoeNode.node_name==post.node_name
        ).first()

        appends = self.db.query(CoePostAppend).filter(
            CoePostAppend.post_id == post_id
            ).order_by(CoePostAppend.created.asc()).limit(10)

        reply_query = self.db.query(CoeReply).filter(CoeReply.post_id==post_id)
        page_data = self.get_page_data(reply_query)
        self.render("post_detail.html",post=post,page_data=page_data,node=node,appends=appends)

@route("/post/move/(\d+)")
class PostMoveHandler(BasicHandler):

    @authenticated
    def get(self,post_id,template_variables={}):
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render_error(msg="访问的主题不存在")
        nodes = self.db.query(CoeNode).filter(
            CoeNode.is_hide == 0).all()
        self.render("post_move.html",post=post,nodes=nodes)

    @authenticated
    def post(self,post_id):
        post = self.db.query(CoePost).get(post_id)
        node_name = self.get_argument("node_name")
        if not node_name:
            return self.render_error(msg="无效节点名")
        if not post:
            return self.render_error(msg="访问的主题不存在")

        post.node_name = node_name
        self.db.commit()
        self.redirect("/post/{0}".format(post_id), permanent=False)

@route("/post/append/(\d+)")
class PostAppendHandler(BasicHandler):

    @authenticated
    def get(self,post_id,template_variables={}):
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render_error(msg="访问的主题不存在")
        if self.current_user.username not in post.username:
            return self.render_error(msg="非法的访问")
        self.render("post_append.html",post=post)

    @authenticated
    def post(self,post_id):
        post = self.db.query(CoePost).get(post_id)
        post_append = self.get_argument("content")
        if not post_append:
            return self.render_error(msg="内容不能为空")

        if len(post_append) > 8192:
            return self.render_error(msg="长度不能超过8192")

        if not post:
            return self.render_error(msg="访问的主题不存在")

        append = CoePostAppend()
        append.post_id = post_id
        append.content = post_append
        append.created = get_currtime()

        self.db.add(append)
        self.db.commit()
        self.redirect("/post/{0}".format(post_id), permanent=False)



@route("/post/reply/(\d+)")
class PostReplyHandler(BasicHandler):

    @authenticated
    def post(self,post_id):
        if self.current_user.credit < abs(credit_types['reply_post'].value):
            return self.render_error(msg="你的象牙币不足，无法发表回复")

        reply_content = self.get_argument("reply_content",None)
        _v = rules.len_of(3,8192)
        if not _v.valid(reply_content):
            return self.render_error(msg=u"回复内容长度不符合要求,{0}".format(_v.msg))    

        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render_error(msg=u"回复的主题不存在")

        username = self.current_user.username
        reply = CoeReply()
        reply.created = get_currtime()
        reply.post_id = int(post_id)
        reply.username = username
        reply.content = websafe(reply_content)
        reply.is_ignore = 0

        self.db.add(reply)

        post.last_reply_user = username
        post.last_reply_time = reply.created
        post.reply_count = post.reply_count + 1

        #credit operate
        post_user = self.db.query(CoeUser).filter(
            CoeUser.username == post.username
            ).first()

        reply_user = self.db.query(CoeUser).filter(
            CoeUser.username == reply.username
            ).first()

        post_user.credit = post_user.credit + credit_types['get_reply_post'].value
        reply_user.credit = reply_user.credit + credit_types['reply_post'].value

        clog = CoeCreditLog()
        clog.username = post_user.username
        clog.op_type = credit_types['get_reply_post'].name
        clog.op_desc = credit_types['get_reply_post'].desc
        clog.credit_val = credit_types['get_reply_post'].value
        clog.balance = post_user.credit
        clog.created = get_currtime()

        clog2 = CoeCreditLog()
        clog2.username = reply_user.username
        clog2.op_type = credit_types['reply_post'].name
        clog2.op_desc = credit_types['reply_post'].desc
        clog2.credit_val = credit_types['reply_post'].value
        clog2.balance = reply_user.credit
        clog2.created = get_currtime()     

        self.db.add(clog)
        self.db.add(clog2) 

        self.db.commit()
        self.db.flush()

        self.redirect("/post/{0}".format(post_id), permanent=False)


@route("/post/collect/(\d+)")
class PostCollectHandler(BasicHandler):
    @authenticated
    def post(self,post_id):
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render_json(code=1,msg=u"主题不存在")

        cup = self.db.query(CoeUserPost).filter(
            CoeUserPost.username == self.current_user.username,
            CoeUserPost.post_id == post_id).first()

        if not cup:
            cup = CoeUserPost()
            cup.username = self.current_user.username
            cup.post_id = post_id
            cup.is_ignore = 0
            cup.is_collect = 1
            self.db.add(cup)
        else:
            cup.is_collect = 1

        self.db.commit()

        return self.render_json(msg="ok")

@route("/post/uncollect/(\d+)")
class PostUnCollectHandler(BasicHandler):
    @authenticated
    def post(self,post_id):
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render_json(code=1,msg=u"主题不存在")

        cup = self.db.query(CoeUserPost).filter(
            CoeUserPost.username == self.current_user.username,
            CoeUserPost.post_id == post_id).first()

        if not cup:
            return self.render_json(msg="ok")
        else:
            cup.is_collect = 0

        self.db.commit()

        return self.render_json(msg="ok")



@route("/post/ignore/(\d+)")
class PostIgnoreHandler(BasicHandler):
    @authenticated
    def post(self,post_id):
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render_json(code=1,msg=u"主题不存在")

        if post.username == self.current_user.username:
            return self.render_json(code=1,msg=u"不能忽略自己的主题")

        cup = self.db.query(CoeUserPost).filter(
            CoeUserPost.username == self.current_user.username,
            CoeUserPost.post_id == post_id).first()

        if not cup:
            cup = CoeUserPost()
            cup.username = self.current_user.username
            cup.post_id = post_id
            cup.is_ignore = 1
            cup.is_collect = 0
            self.db.add(cup)
        else:
            cup.is_ignore = 1

        self.db.commit()

        return self.render_json(msg="ok")

@route("/post/unignore/(\d+)")
class PostUnIgnoreHandler(BasicHandler):
    @authenticated
    def post(self,post_id):
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render_json(code=1,msg=u"主题不存在")

        cup = self.db.query(CoeUserPost).filter(
            CoeUserPost.username == self.current_user.username,
            CoeUserPost.post_id == post_id).first()

        if not cup:
            return self.render_json(msg="ok")
        else:
            cup.is_ignore = 0

        self.db.commit()
        return self.render_json(msg="ok")


@route("/post/sysignore/(\d+)")
class SysIgnoreHandler(BasicHandler):
    @authenticated
    def post(self,post_id):
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render_json(code=1,msg=u"主题不存在")

        post.is_ignore = 1
        self.db.commit()
        return self.render_json(msg="ok")        
