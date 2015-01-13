#!/usr/bin/env python3
#coding=utf-8
import sys
sys.path.insert(0,'..')
import random
from tornweb.utils import get_uuid,get_currtime,md5hash
from db_models import CoeUser,CoeCreditLog,CoeInvite
from handlers.base import credit_types

__name__ = 'subscribe'

def test(data, msg=None, bot=None, handler=None):
    return data.strip().startswith('event:subscribe')

def respond(data, msg=None, bot=None, handler=None):
    user = handler.db.query(CoeUser).filter(CoeUser.username==msg.fromuser).first()
    if not user:
        user = CoeUser()
        user.username = msg.fromuser
        user.password = str(random.randint(100000,10000000))
        user.nickname = str(random.randint(100000,10000000))
        user.email = "%s@tough.radius"%msg.fromuser
        user.created = get_currtime()
        user.actived = 1
        user.active_code = get_uuid() 
        user.credit = credit_types['weixin_join'].value
        user.is_ignore = 0
        user.headurl = handler.settings['default_head']
        handler.db.add(user)

        clog = CoeCreditLog()
        clog.username = user.username
        clog.op_type = credit_types['weixin_join'].name
        clog.op_desc = credit_types['weixin_join'].desc
        clog.credit_val = credit_types['weixin_join'].value
        clog.balance = user.credit
        clog.created = get_currtime()
        handler.db.add(clog)

        ui = CoeInvite()
        ui.username = user.username
        ui.invite_code = get_uuid()
        ui.invite_hit = 0
        ui.invite_total = 0
        ui.created = get_currtime()
        handler.db.add(ui)
        handler.db.commit()

    return '''感谢您关注印象加油站! 系统自动分配的印象昵称是 %s, 发送以下关键字可以快捷为您服务: \n
    0 : 帮助\n
    1 : 查询最新主题\n
    2 : 查询热门主题\n
    3 : 查询我收藏的主题\n
    4 : 查询我关注的用户主题\n
    5 : 我要发布主题''' % (user.nickname or 'anonymous')
