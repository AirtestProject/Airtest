# coding=utf-8
__author__ = 'lxn3032'


import re
import os


ADBKEYBOARD_IME_PATH = os.path.join(os.path.split(os.path.realpath(__file__))[0], "AdbKeyboard.apk")
ADBKEYBOARD_SERVICE = "com.android.adbkeyboard/.AdbIME"
YOSEMITE_IME_SERVICE = 'com.netease.nie.yosemite/.ime.ImeService'


class CustomIme(object):

    def __init__(self, android_device, apk_path, service_name):
        super(CustomIme, self).__init__()
        self.device = android_device
        self.adb = android_device.adb
        self.apk_path = apk_path
        self.service_name = service_name
        self.default_ime = self.adb.shell("settings get secure default_input_method").strip()
        self.ime_list = self._get_ime_list()

    def _get_ime_list(self):
        out = self.adb.shell("ime list -a")
        # m = re.findall("(.*?/.*?):.*?mId.*?flags.*?\s+", out, re.S)
        m = re.findall("mId=(.*?/.*?) ", out)
        return m

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()

    def start(self):
        if self.service_name not in self.ime_list:
            self.device.enable_accessibility_service()
            self.adb.cmd("install -r %s" % self.apk_path)
            self.device.disable_accessibility_service()
        if self.default_ime != self.service_name:
            self.adb.shell("ime enable %s" % self.service_name)
            self.adb.shell("ime set %s" % self.service_name)

    def end(self):
        if self.default_ime != self.service_name:
            self.adb.shell("ime disable %s" % self.service_name)
            self.adb.shell("ime set %s" % self.default_ime)


class AdbKeyboardIme(CustomIme):
    """支持中文输入"""
    def __init__(self, android_device):
        super(AdbKeyboardIme, self).__init__(android_device, ADBKEYBOARD_IME_PATH, ADBKEYBOARD_SERVICE)


class YosemiteIme(CustomIme):
    def __init__(self, android_device):
        super(YosemiteIme, self).__init__(android_device, '', YOSEMITE_IME_SERVICE)
