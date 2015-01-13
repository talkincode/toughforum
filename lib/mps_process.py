#coding=utf-8
from tornado.util import ObjectDict
from tornado.options import options
from lib.mpsai import AI
from lib import mpsmsg
from lib.mpsmsg import log
from lib.mpsmsg import (
    MSG_TYPE_TEXT, 
    MSG_TYPE_LOCATION, 
    MSG_TYPE_IMAGE, 
    MSG_TYPE_LINK, 
    MSG_TYPE_EVENT, 
    MSG_TYPE_MUSIC, 
    MSG_TYPE_NEWS
)


class MsgProcess():
    def __init__(self, msg, handler):
        self.msg = msg
        self.handler = handler

    def process(self):
        if self.msg.type == MSG_TYPE_TEXT:
            return mpsmsg.gen_reply(self.msg.touser, self.msg.fromuser, self.process_text())
        elif self.msg.type == MSG_TYPE_LOCATION:
            return mpsmsg.gen_reply(self.msg.touser, self.msg.fromuser, self.process_location())
        elif self.msg.type == MSG_TYPE_IMAGE:
            return mpsmsg.gen_reply(self.msg.touser, self.msg.fromuser, self.process_image())
        elif self.msg.type == MSG_TYPE_EVENT:
            return mpsmsg.gen_reply(self.msg.touser, self.msg.fromuser, self.process_event())
        elif self.msg.type == MSG_TYPE_LINK:
            return mpsmsg.gen_reply(self.msg.touser, self.msg.fromuser, self.process_link())
        else:
            log.info('message type unknown')

    def process_text(self):
        bot = AI(self.msg)
        result = bot.respond(self.msg.content, msg=self.msg, handler=self.handler)

        if options.debug:
            log.info('bot response %s', result)
        if isinstance(result, list):
            return ObjectDict(msg_type=MSG_TYPE_NEWS, response=result)
        else:
            return ObjectDict(msg_type=MSG_TYPE_TEXT, response=result)
 

    def process_event(self):
        bot = AI(self.msg)
        result = bot.respond('event:%s:%s' % (self.msg.event, self.msg.event_key), msg=self.msg, handler=self.handler)

        if options.debug:
            log.info('bot response %s', result)

        if isinstance(result, list):
            return ObjectDict(msg_type=MSG_TYPE_NEWS, response=result)
        else:
            return ObjectDict(msg_type=MSG_TYPE_TEXT, response=result)    


    def process_location(self):
        return self.process_nothing()

    def process_image(self):
        bot = AI(self.msg)
        result = bot.respond('image:message', msg=self.msg, handler=self.handler)

        if options.debug:
            log.info('bot response %s', result)
        if isinstance(result, list):
            return ObjectDict(msg_type=MSG_TYPE_NEWS, response=result)
        else:
            return ObjectDict(msg_type=MSG_TYPE_TEXT, response=result)    


    def process_link(self):
        return self.process_nothing()

    def process_nothing(self):
        return ObjectDict(msg_type=MSG_TYPE_TEXT, response='')
