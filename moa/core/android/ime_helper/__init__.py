# coding=utf-8
__author__ = 'lxn3032'


import re
import os


IME_PATH = os.path.join(os.path.split(os.path.realpath(__file__))[0], "Utf7Ime.apk")


class UiautomatorIme(object):
    def __init__(self, adb):
        super(UiautomatorIme, self).__init__()
        self.adb = adb
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
        if "jp.jun_nama.test.utf7ime/.Utf7ImeService" not in self.ime_list:
            self.adb.cmd("install -r " + IME_PATH)
        self.adb.shell("ime enable jp.jun_nama.test.utf7ime/.Utf7ImeService")
        self.adb.shell("ime set jp.jun_nama.test.utf7ime/.Utf7ImeService")

    def end(self):
        self.adb.shell("ime disable jp.jun_nama.test.utf7ime/.Utf7ImeService")
        self.adb.shell("ime set " + self.default_ime)
