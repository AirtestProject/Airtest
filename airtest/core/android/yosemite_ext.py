import re

from .constant import YOSEMITE_APK, YOSEMITE_PACKAGE
from airtest.core.android.yosemite import Yosemite
from airtest.core.error import AirtestError
from airtest.utils.snippet import on_method_ready, escape_special_char
from airtest.utils.logger import get_logger
LOGGING = get_logger(__name__)


class YosemiteExt(Yosemite):

    def __init__(self, adb):
        super(YosemiteExt, self).__init__(adb)
        self._path = ""

    @property
    def path(self):
        if not self._path:
            self._path = self.adb.path_app(YOSEMITE_PACKAGE)
        return self._path

    @on_method_ready('install_or_upgrade')
    def device_op(self, op_name, op_args=""):
        """
        Perform device operations

        Args:
            op_name: operation name
            op_args: operation args

        Returns:
            None

        """
        return self.adb.shell(f"app_process -Djava.class.path={self.path} / com.netease.nie.yosemite.control.Control --DEVICE_OP {op_name} {op_args}")

    def get_clipboard(self):
        """
        Get clipboard content

        Returns:
            clipboard content

        """
        text = self.device_op("clipboard_get")
        if text:
            return text.strip()
        return ""

    def set_clipboard(self, text):
        """
        Set clipboard content

        Args:
            text: text to be set

        Returns:
            None

        """
        text = escape_special_char(text)

        try:
            ret = self.device_op("clipboard", f'--TEXT {text}')
        except Exception as e:
            raise AirtestError("set clipboard failed, %s" % repr(e))
        else:
            if ret and "Exception" in ret:
                raise AirtestError("set clipboard failed: %s" % ret)

    def change_lang(self, lang):
        """
        Change language

        Args:
            lang: language to be set

        Returns:
            None

        """
        lang_list = ['zh', 'en', 'fr', 'de', 'it', 'ja', 'ko', ]
        self.device_op("changeLanguge", f"--LANGUAGE_OP {lang}")
