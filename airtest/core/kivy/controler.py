# coding=utf-8

__author__ = 'zxfn4514'

class Controler(object):

    def __init__(self, _agent):
        self.agent = _agent

    def snapshot(self, width=None, filename=None):
        if width:
            _str = self.agent.getScreen(width) 
        else:
            _str = self.agent.getScreen()
        return _str

    def list_app(self):
        return self.agent.listApp()

    def wake(self):
        self.agent.wakeUp()

    def keyevent(self, keyname):
        self.agent.keyevent(keyname)

    def home(self):
        return self.agent.keyevent("HOME")

    def touch(self, pos, duration=0.01):
        return self.agent.click(pos[0], pos[1])

    def swipe(self, p1, p2, duration=5):
        return self.agent.swipe(p1[0], p1[1], p2[0], p2[1], duration)

    def text(self, text):
        return self.agent.text(text)

    def start_app(self, package): 
        return self.agent.startApp(package)

    def stop_app(self):
        self.agent.finishApp()

    def get_display_info(self):
        display_info = {}
        dim = self.agent.getPortSize()
        display_info['width'] = dim[0]
        display_info['height'] = dim[1]
        display_info['orientation'] = self.agent.getOrientation()
        return display_info
