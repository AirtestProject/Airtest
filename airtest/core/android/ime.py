# coding=utf-8
import re
import six

__author__ = 'lxn3032'

YOSEMITE_IME_SERVICE = 'com.netease.nie.yosemite/.ime.ImeService'


def ensure_unicode(value):
    if six.PY3:
        if type(value) is not str:
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                value = value.decode('gbk')
    else:
        if type(value) is not unicode:
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                value = value.decode('gbk')
    return value


class CustomIme(object):

    def __init__(self, adb, apk_path, service_name):
        super(CustomIme, self).__init__()
        self.adb = adb
        self.apk_path = apk_path
        self.service_name = service_name
        self.started = False

    def _get_ime_list(self):
        out = self.adb.shell("ime list -a")
        m = re.findall("mId=(.*?/.*?) ", out)
        return m

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()

    def start(self):
        self.default_ime = self.adb.shell("settings get secure default_input_method").strip()
        self.ime_list = self._get_ime_list()
        if self.service_name not in self.ime_list:
            if self.apk_path:
                self.device.install_app(self.apk_path)
        if self.default_ime != self.service_name:
            self.adb.shell("ime enable %s" % self.service_name)
            self.adb.shell("ime set %s" % self.service_name)
        self.started = True

    def end(self):
        if self.default_ime != self.service_name:
            self.adb.shell("ime disable %s" % self.service_name)
            self.adb.shell("ime set %s" % self.default_ime)
        self.started = False

    def text(self, value):
        raise NotImplementedError


class YosemiteIme(CustomIme):
    def __init__(self, android_device):
        super(YosemiteIme, self).__init__(android_device, None, YOSEMITE_IME_SERVICE)

    def text(self, value):
        if not self.started:
            self.start()
        # 更多的输入用法请见 https://github.com/macacajs/android-unicode#use-in-adb-shell
        value = ensure_unicode(value)
        self.adb.shell(u"am broadcast -a ADB_INPUT_TEXT --es msg '{}'".format(value))
