# coding=utf-8
__author__ = 'lxn3032'


import re
import os


UIAUTOMATOR_IME_PATH = os.path.join(os.path.split(os.path.realpath(__file__))[0], "Utf7Ime.apk")
UIAUTOMATOR_SERVICE = "jp.jun_nama.test.utf7ime/.Utf7ImeService"
ADBKEYBOARD_IME_PATH = os.path.join(os.path.split(os.path.realpath(__file__))[0], "AdbKeyboard.apk")
ADBKEYBOARD_SERVICE = "com.android.adbkeyboard/.AdbIME"


class CustomIme(object):

    def __init__(self, adb, apk_path, service_name):
        super(CustomIme, self).__init__()
        self.adb = adb
        self.apk_path = apk_path
        self.service_name = service_name
        self.default_ime = self.adb.shell("settings get secure default_input_method")
        self.ime_list = self._get_ime_list()

    def _get_ime_list(self):
        out = self.adb.shell("ime list -a")
        m = re.findall("(.*?/.*?):.*?mId.*?flags.*?\s+", out, re.S)
        return m

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()

    def start(self):
        if self.service_name not in self.ime_list:
            self.adb.cmd("install -r %s" % self.apk_path)
        self.adb.shell("ime enable %s" % self.service_name)
        self.adb.shell("ime set %s" % self.service_name)

    def end(self):
        self.adb.shell("ime disable %s" % self.service_name)
        self.adb.shell("ime set %s" % self.default_ime)    


class UiautomatorIme(CustomIme):
    """没有弹框"""
    def __init__(self, adb):
        super(UiautomatorIme, self).__init__(adb, UIAUTOMATOR_IME_PATH, UIAUTOMATOR_SERVICE)


class AdbKeyboardIme(CustomIme):
    """支持中文输入"""
    def __init__(self, arg):
        super(AdbKeyboardIme, self).__init__(adb, ADBKEYBOARD_IME_PATH, ADBKEYBOARD_SERVICE)
