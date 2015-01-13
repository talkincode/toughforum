#!/usr/bin/env python3
#coding=utf-8

import sys
sys.path.insert(0,'..')
from tornado.util import ObjectDict
from tornweb.utils import  rtitle,encrypt
from db_models import CoePost,CoeNode

__name__ = 'post'

def test(data, msg=None, bot=None, handler=None):
    return data.strip() == '5'


def respond(data, msg=None, bot=None, handler=None):
    nodes = handler.db.query(CoeNode).filter(
        CoeNode.is_top == 1).order_by(CoeNode.created.asc()).limit(9)
    articles = []
    for node in nodes:
        if node.is_hide == 1:
            continue        
        article = ObjectDict()
        article.title = node.node_desc
        article.description = rtitle(node.node_intro,79)
        article.url = "%s/mps/post/new/%s?otoken=%s" % (
            handler.settings['server_base'],
            node.node_name,
            handler.encrypt_otoken(bot.id))
        article.picurl = ''
        articles.append(article)

    if len(articles)>1:
        articles[0].picurl = handler.settings['mps_default_bg']

    return articles