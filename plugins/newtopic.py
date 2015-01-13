#!/usr/bin/env python3
#coding=utf-8
import sys
sys.path.insert(0,'..')
from tornado.util import ObjectDict
from tornweb.utils import  rtitle,encrypt
from db_models import CoePost


__name__ = 'newtopic'

def test(data, msg=None, bot=None, handler=None):
    return data.strip() == '1'
    

def respond(data, msg=None, bot=None, handler=None):
    post_query = handler.db.query(CoePost).order_by(CoePost.created.desc()).limit(9)
    _ignores = handler.get_user_post_ignores(msg.fromuser)
    _blocks = handler.get_user_blocks(msg.fromuser)
    articles = []
    for post in post_query:
        if post.is_ignore == 1:
            continue   
        if post.post_id in _ignores:
            continue
        if post.username in _blocks:
            continue                 
        article = ObjectDict()
        article.title = post.topic
        article.description = rtitle(post.content,79)
        article.url = "%s/mps/post/%s?otoken=%s" % (handler.settings['server_base'],
                 post.post_id,handler.encrypt_otoken(bot.id))        
        article.picurl = handler.get_1img_from_content(post.content)
        articles.append(article)

    return articles