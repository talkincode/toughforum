#!/usr/bin/env python3
#coding=utf-8
import re
from tornado.util import ObjectDict

__name__ = 'help'

def test(data, msg=None, bot=None, handler=None):
    return data.strip() == '0'


def respond(data, msg=None, bot=None, handler=None):
    return '''发送以下关键字可以快捷为您服务: \n
    0 : 帮助\n
    1 : 查询最新主题\n
    2 : 查询热门主题\n
    3 : 查询我收藏的主题\n
    4 : 查询我关注的用户主题\n
    5 : 我要发布主题'''

if __name__ == 'help':
    import doctest
    doctest.testmod()
