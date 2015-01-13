#!/usr/bin/env python3

from tornweb.webutils import route,authenticated
from tornweb.utils import md5hash,get_uuid,get_currtime
from .base import BasicHandler
from tornweb.base import ApiMessage
from tornweb.btform import webform,rules
from tornweb.btform.rules import input_style,button_style
from tornado import gen
from db_models import CoeNode,CoePost

@route('/node/(\w+)')
class IndexHandler(BasicHandler):
    def get(self,node_name, template_variables={}):
        nodes = self.db.query(CoeNode).filter(CoeNode.is_top==1).all()
        node = self.db.query(CoeNode).filter(
            CoeNode.node_name==node_name
        ).first()

        if not node:
            return self.render_error(msg=u"节点不存在")

        post_query = self.db.query(CoePost).filter(
            CoePost.node_name == node_name
        ).order_by(CoePost.created.desc())

        page_data = self.get_page_data(post_query)

        self.render("node_index.html",
            page_data=page_data,
            node_name=node_name,
            node_desc=node.node_desc,
            node_intro=node.node_intro,
            nodes=nodes
        )



