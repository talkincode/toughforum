#!/usr/bin/env python3
#coding=utf-8

__name__ = 'unsubscribe'


def test(data, msg=None, bot=None, handler=None):
    return data.strip().startswith('event:unsubscribe')


def respond(data, msg=None, bot=None, handler=None):
    return "bye"