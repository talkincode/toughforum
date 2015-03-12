#!/usr/bin/env python3

from tornweb.webutils import route,authenticated
from tornweb.utils import decrypt,get_currtime,get_currdate
from .base import BasicHandler,credit_types
from tornweb.btform import dataform,rules
from db_models import CoeNode,CoePost,CoeReply,CoeUserPost,CoeUser,CoeCreditLog
from tornweb.btform.net import websafe

post_add_form = dataform.Form(
    dataform.Item("topic", rules.len_of(7,255),description=u"主题描述",),
    dataform.Item("content", rules.len_of(0,8192),description=u"主题内容",),
)

@route('/mps/post/new/(\w+)')
class NewPostHandler(BasicHandler):
    
    def get(self, node_name, template_variables={}):
        otoken = self.get_argument("otoken",None)
        openid = self.check_otoken(otoken)
        if not openid:
            return self.render("mps/message.html",msg="非法的访问")
         
        if not self.get_secure_cookie("username"):
            self.set_secure_cookie("username", openid, expires_days=30)    

        current_user = self.db.query(CoeUser).filter(
            CoeUser.username == openid).first()  

        if current_user.credit < abs(credit_types['create_post'].value):
            return self.render("mps/message.html",msg="你的硬币不足，无法发表主题")
                    
        node = self.db.query(CoeNode).filter(
            CoeNode.node_name==node_name
        ).first()

        if not node:
            return self.render("mps/message.html",msg=u"节点不存在")

        self.render("mps/post_add.html",node_name=node_name,node_desc=node.node_desc)

    def post(self,node_name):
        form = post_add_form()
        node = self.db.query(CoeNode).filter(
            CoeNode.node_name==node_name
        ).first()   

        if not form.validates(source=self.get_params()):
            return self.render("mps/post_add.html",
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

@route("/mps/post/(\d+)")
class PostDetailHandler(BasicHandler):

    def get(self,post_id,template_variables={}):
        otoken = self.get_argument("otoken",None)
        openid = self.check_otoken(otoken)
        if not openid:
            return self.render("mps/message.html",msg="非法的访问")

        current_user = self.db.query(CoeUser).filter(
            CoeUser.username == openid).first()         
         
        if not self.get_secure_cookie("username"):
            self.set_secure_cookie("username", openid, expires_days=30)     

        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render("mps/message.html",msg="访问的主题不存在")

        replys= self.db.query(CoeReply).filter(CoeReply.post_id==post_id).limit(200)
        self.render("mps/post_detail.html",post=post,replys=replys,otoken=otoken,username=openid)




@route("/mps/post/reply/(\d+)")
class PostReplyHandler(BasicHandler):

    def post(self,post_id):
        otoken = self.get_argument("otoken",None)
        openid = self.check_otoken(otoken)
        if not openid:
            return self.render("mps/message.html",msg="非法的访问")
             
        current_user = self.db.query(CoeUser).filter(
            CoeUser.username == openid).first()

        if not current_user:
            return self.render("mps/message.html",msg="用户不存在")

        if current_user.credit < abs(credit_types['reply_post'].value):
            return self.render_error(msg="你的硬币不足，无法发表回复")

        reply_content = self.get_argument("reply_content",None)
        _v = rules.len_of(3,8192)
        if not _v.valid(reply_content):
            return self.render("mps/message.html",msg=u"回复内容长度不符合要求,{0}".format(_v.msg))    

        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render("mps/message.html",msg=u"回复的主题不存在")

        username = current_user.username
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

        self.redirect("/mps/post/{0}?otoken={1}".format(post_id,otoken), permanent=False)



@route("/mps/post/collect/(\d+)")
class PostCollectHandler(BasicHandler):

    def get(self,post_id):
        otoken = self.get_argument("otoken",None)
        openid = self.check_otoken(otoken)
        if not openid:
            return self.render("mps/message.html",msg="非法的访问")
             
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render("mps/message.html",msg=u"主题不存在")

        cup = self.db.query(CoeUserPost).filter(
            CoeUserPost.username == openid,
            CoeUserPost.post_id == post_id).first()

        if not cup:
            cup = CoeUserPost()
            cup.username = openid
            cup.post_id = post_id
            cup.is_ignore = 0
            cup.is_collect = 1
            self.db.add(cup)
        else:
            cup.is_collect = 1

        self.db.commit()

        self.redirect("/mps/post/{0}?otoken={1}".format(post.post_id,otoken), permanent=False)

@route("/mps/post/uncollect/(\d+)")
class PostUnCollectHandler(BasicHandler):

    def get(self,post_id):
        otoken = self.get_argument("otoken",None)
        openid = self.check_otoken(otoken)
        if not openid:
            return self.render("mps/message.html",msg="非法的访问")

        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render("mps/message.html",msg=u"主题不存在")

        cup = self.db.query(CoeUserPost).filter(
            CoeUserPost.username == openid,
            CoeUserPost.post_id == post_id).first()

        if not cup:
            return self.redirect("/mps/post/{0}?otoken={1}".format(post.post_id,otoken), permanent=False)
        else:
            cup.is_collect = 0

        self.db.commit()

        self.redirect("/mps/post/{0}?otoken={1}".format(post.post_id,otoken), permanent=False)



@route("/mps/post/ignore/(\d+)")
class PostIgnoreHandler(BasicHandler):

    def get(self,post_id):
        otoken = self.get_argument("otoken",None)
        openid = self.check_otoken(otoken)
        if not openid:
            return self.render("mps/message.html",msg="非法的访问")
             
        current_user = self.db.query(CoeUser).filter(
            CoeUser.username == openid).first()  
                  
        post = self.db.query(CoePost).get(post_id)
        if not post:
            return self.render("mps/message.html",msg=u"主题不存在")

        if post.username == openid:
            return self.render("mps/message.html",msg=u"不能忽略自己的主题")

        cup = self.db.query(CoeUserPost).filter(
            CoeUserPost.username == openid,
            CoeUserPost.post_id == post_id).first()

        if not cup:
            cup = CoeUserPost()
            cup.username = openid
            cup.post_id = post_id
            cup.is_ignore = 1
            cup.is_collect = 0
            self.db.add(cup)
        else:
            cup.is_ignore = 1

        self.db.commit()

        return self.render("mps/message.html",msg="忽略成功，你再也见不到它了")



