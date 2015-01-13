#coding=utf-8
import sys
sys.path.insert(0,"..")
import logging
import plugins
from plugins import superbot

"""  微信公众平台消息自动处理扩展 """

log = logging.getLogger("plugins")

class AI(object):
    _plugin_modules = []
    _plugin_loaded = False

    def __init__(self, msg=None):
        if msg:
            self.id = msg.fromuser

    @classmethod
    def load_plugins(cls):
        """
        加载所有插件
        """
        if cls._plugin_loaded:
            return
        for name in plugins.__all__:
            try:
                __import__('plugins.%s' % name)
                cls.add_plugin(getattr(plugins, name))
                logging.info('Plugin %s loaded success.' % name)
            except:
                logging.exception('Fail to load plugin %s' % name)
        cls._plugin_loaded = True

    @classmethod
    def add_plugin(cls, plugin):
        if not hasattr(plugin, 'test'):
            logging.error('Plugin %s has no method named test, ignore it')
            return False
        if not hasattr(plugin, 'respond'):
            logging.error('Plugin %s has no method named respond, ignore it')
            return False
        cls._plugin_modules.append(plugin)
        return True

    def respond(self, data, msg=None, handler=None):
        """
        调用插件进行消息处理，传入参数：
        @data 消息字符串内容
        @msg 原始消息对象
        @db 传入数据库会话，如果有数据库读写
        """
        response = None
        for plugin in self._plugin_modules:
            try:
                if plugin.test(data, msg, self, handler):
                    logging.info('Plugin %s is match' % plugin.__name__)
                    response = plugin.respond(data, msg, self, handler)
            except:
                logging.exception('Plugin %s failed to respond.' %
                                  plugin.__name__)
                continue
            if response:
                break

        return response or superbot.respond(data, msg, self, handler) or ''

#第一次导入此模块时进行初始化加载
AI.load_plugins()

if __name__ == '__main__':
    bot = AI()
    print(bot.respond('t'))
