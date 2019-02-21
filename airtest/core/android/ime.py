# coding=utf-8
import re
from airtest.core.android.yosemite import Yosemite
from airtest.core.error import AdbError
from .constant import YOSEMITE_IME_SERVICE
from six import text_type


def ensure_unicode(value):
    """
    Decode UTF-8 values

    Args:
        value: value to be decoded

    Returns:
        decoded valued

    """
    if type(value) is not text_type:
        try:
            value = value.decode('utf-8')
        except UnicodeDecodeError:
            value = value.decode('gbk')
    return value


class CustomIme(object):
    """
    Input Methods Class Object
    """

    def __init__(self, adb, apk_path, service_name):
        super(CustomIme, self).__init__()
        self.adb = adb
        self.apk_path = apk_path
        self.service_name = service_name
        self.started = False

    def _get_ime_list(self):
        """
        Return all the input methods on the device

        Returns:
            list of all input methods on the device

        """
        out = self.adb.shell("ime list -a")
        m = re.findall("mId=(.*?/.*?) ", out)
        return m

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()

    def start(self):
        """
        Enable input method

        Returns:
            None

        """
        try:
            self.default_ime = self.adb.shell("settings get secure default_input_method").strip()
        except AdbError:
            # settings cmd not found for older phones, e.g. Xiaomi 2A
            # /system/bin/sh: settings: not found
            self.default_ime = None
        self.ime_list = self._get_ime_list()
        if self.service_name not in self.ime_list:
            if self.apk_path:
                self.device.install_app(self.apk_path)
        if self.default_ime != self.service_name:
            self.adb.shell("ime enable %s" % self.service_name)
            self.adb.shell("ime set %s" % self.service_name)
        self.started = True

    def end(self):
        """
        Disable input method

        Returns:
            None

        """
        if self.default_ime and self.default_ime != self.service_name:
            self.adb.shell("ime disable %s" % self.service_name)
            self.adb.shell("ime set %s" % self.default_ime)
        self.started = False

    def text(self, value):
        raise NotImplementedError


class YosemiteIme(CustomIme):
    """
    Yosemite Input Method Class Object
    """

    def __init__(self, adb):
        super(YosemiteIme, self).__init__(adb, None, YOSEMITE_IME_SERVICE)
        self.yosemite = Yosemite(adb)

    def start(self):
        self.yosemite.get_ready()
        super(YosemiteIme, self).start()

    def text(self, value):
        """
        Input text with Yosemite input method

        Args:
            value: text to be inputted

        Returns:
            output form `adb shell` command

        """
        if not self.started:
            self.start()
        # 更多的输入用法请见 https://github.com/macacajs/android-unicode#use-in-adb-shell
        value = ensure_unicode(value)
        self.adb.shell(u"am broadcast -a ADB_INPUT_TEXT --es msg '{}'".format(value))

    def code(self, code):
        """
        Sending editor action

        Args:
            code: editor action code, e.g., 2 = IME_ACTION_GO, 3 = IME_ACTION_SEARCH
                Editor Action Code Ref: http://developer.android.com/reference/android/view/inputmethod/EditorInfo.html

        Returns:
            output form `adb shell` command

        """
        if not self.started:
            self.start()
        self.adb.shell("am broadcast -a ADB_EDITOR_CODE --ei code {}".format(str(code)))
