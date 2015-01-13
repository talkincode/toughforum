#!/usr/bin/env python3

from tornweb.webutils import route,authenticated,auth_admin
from tornweb.utils import md5hash,get_uuid,get_currtime
from .base import BasicHandler
from tornweb.base import ApiMessage
from tornweb.btform import webform,rules
from tornweb.btform.rules import input_style,button_style
from tornado import gen
from db_models import CoeNode

is_tops = [(0, '不推荐'), (1, '推荐')]
is_hides = [(0, '不隐藏'), (1, '隐藏')]

node_add_form = webform.Form(
    webform.Textbox("node_name", rules.is_alphanum3(1, 32), description=u"节点名", size=32,required="required",**input_style),
    webform.Textbox("node_desc", rules.len_of(1,32), description="节点描述", size=32, required="required",**input_style),
    webform.Dropdown("is_top", description="首页推荐", args=is_tops, **input_style),
    webform.Dropdown("is_hide", description="是否隐藏", args=is_hides, **input_style),
    webform.Textarea("node_intro", rules.len_of(1,1024), description="节点介绍",**input_style),
    webform.Button("submit", type="submit", html="<b>提交</b>", **button_style),
    action="/manage/node/add",
    title="新增节点"
)

node_update_form = webform.Form(
    webform.Textbox("node_name", rules.is_alphanum3(1, 32), description=u"节点名", size=32,readonly="readonly",**input_style),
    webform.Textbox("node_desc", rules.len_of(1,32), description=u"节点描述", size=32, required="required",**input_style),
    webform.Dropdown("is_top", description=u"首页推荐", args=is_tops, **input_style),
    webform.Dropdown("is_hide", description=u"是否隐藏", args=is_hides, **input_style),
    webform.Textarea("node_intro", rules.len_of(1,1024), description="节点介绍",**input_style),
    webform.Button("submit", type="submit", html=u"<b>提交</b>", **button_style),
    action="/manage/node/modify",
    title=u"修改节点"
)


@route('/manage/nodes')
class NodeHandler(BasicHandler):

    @auth_admin
    def get(self, template_variables={}):
        node_query = self.db.query(CoeNode)
        page_data = self.get_page_data(node_query)
        self.render("manage/nodes.html",page_data=page_data)
   

@route('/manage/node/add')
class NodeAddHandler(BasicHandler):

    @auth_admin
    def get(self, template_variables={}):
        form = node_add_form()
        self.render("manage/base_form.html",form=form)

    @auth_admin
    def post(self):
        form = node_add_form()
        if not form.validates(source=self.get_params()):
            return self.render("manage/base_form.html",form=form)

        node = CoeNode()
        node.node_name = form.d.node_name 
        node.node_desc = form.d.node_desc
        node.created = get_currtime()
        node.is_top = int(form.d.is_top)
        node.is_hide = int(form.d.is_hide)
        node.node_intro = form.d.node_intro
        node.topic_count = 0
        self.db.add(node)
        self.db.commit()
        self.redirect("/manage/nodes", permanent=False)
           

@route('/manage/node/modify')
class NodeUpdateHandler(BasicHandler):

    @auth_admin
    def get(self, template_variables={}):
        node_name = self.get_argument('node_name')
        node = self.db.query(CoeNode).filter(CoeNode.node_name==node_name).first()
        if not node:
            return self.render_error(msg=u"节点不存在")     
        form = node_update_form()
        form.fill(node)
        self.render("manage/base_form.html",form=form)
   

    def post(self):
        form = node_update_form()
        if not form.validates(source=self.get_params()):
            return self.render("manage/base_form.html",form=form)

        node = self.db.query(CoeNode).filter(CoeNode.node_name==form.d.node_name).first()
        node.node_desc = form.d.node_desc
        node.is_top = int(form.d.is_top)
        node.is_hide = int(form.d.is_hide)
        node.node_intro = form.d.node_intro
        node.topic_count = 0

        self.db.commit()

        self.redirect('/manage/nodes',permanent=False)

@route("/manage/node/delete")
class NodeDeleteHandler(BasicHandler):

    def get(self,template_variables={}):
        node_name = self.get_argument("node_name")
        if not node_name:
            return self.render_error(msg=u"无效的节点名")
        self.db.query(CoeNode).filter(CoeNode.node_name==node_name).delete()
        self.redirect("/manage/nodes",permanent=False)








