#!/usr/bin/env python3
#coding=utf-8
import sys
sys.path.insert(0,'..')
from db_models import CoeUser,CoePost,CoeNode,CoeCreditLog
from tornweb.utils import  get_currtime
from tornweb.btform.net import websafe
from handlers.base import credit_types

__name__ = 'idea'

def test(data, msg=None, bot=None, handler=None):
    return data.strip().startswith("idea ")

def respond(data, msg=None, bot=None, handler=None):
    data = data.strip()[5:]
    if len(data) < 9:
        return "至少要有9个字吧！"

    node = handler.db.query(CoeNode).filter(
            CoeNode.node_name=="inspirations"
    ).first() 

    post = CoePost()
    post.node_name = node.node_name
    post.topic = websafe(data)
    post.content = ''
    post.created = get_currtime()
    post.username = msg.fromuser
    post.reply_count = 0
    post.is_ignore = 0
    handler.db.add(post)
    node.topic_count = node.topic_count + 1

    user = handler.db.query(CoeUser).filter(
        CoeUser.username == msg.fromuser
        ).first()

    user.credit = user.credit + credit_types['create_post'].value
    clog = CoeCreditLog()
    clog.username = user.username
    clog.op_type = credit_types['create_post'].name
    clog.op_desc = credit_types['create_post'].desc
    clog.credit_val = credit_types['create_post'].value
    clog.balance = user.credit
    clog.created = get_currtime()
    handler.db.add(clog)
    handler.db.commit()

    return '分享成功'

