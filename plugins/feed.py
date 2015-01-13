#!/usr/bin/env python3
#coding=utf-8
import feedparser
from tornado.util import ObjectDict

__name__ = 'feed'


def test(data, msg=None, bot=None, handler=None):
    return data.strip()=='6'



def respond(data, msg=None, bot=None, handler=None):
    _url = 'http://blog.yinxiang.com/feed'
    parser = feedparser.parse(_url)
    articles = []
    i = 0
    for entry in parser.entries:
        if i > 8:
            break
        article = ObjectDict()
        article.title = entry.title
        article.description = entry.description[0:100]
        article.url = entry.link
        article.picurl = ''
        articles.append(article)
        i += 1
    return articles
