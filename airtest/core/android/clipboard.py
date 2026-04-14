import re
from time import sleep
from airtest.utils.snippet import escape_special_char
from airtest.core.android.constant import CLIPPER_APK, CLIPPER_PACKAGE, YOSEMITE_APK, YOSEMITE_PACKAGE,SDK_VERSION_ANDROID10, CLIPBOARD_METHOD
from airtest.utils.logger import get_logger

LOGGING = get_logger(__name__)

class Clipboard(object):
    """
    Base class for clipboard implementations.
    Subclass this and implement get_clipboard/set_clipboard for each backend.
    """
    def __init__(self, adb):
        self.adb = adb

    def get_clipboard(self):
        raise NotImplementedError

    def set_clipboard(self, text):
        raise NotImplementedError

    
# Clipper: android clipboard access via broadcast intent
# https://github.com/amirshams8/clipper
class ClipperClipboard(Clipboard):
    def __init__(self, adb):
        super(ClipperClipboard, self).__init__(adb)
        self.adb.pm_update_app(CLIPPER_APK, CLIPPER_PACKAGE)

        # background execution is sufficient for Android 9 and below.
        if self.is_supported_background() == True:
            self.shell("am start -n ca.zgrs.clipper/.Main")
            sleep(0.25)
            self.close_clipper()

    def get_clipboard(self):
        if self.is_supported_background() == False:
            # clipboard access requires foreground app 
            self.shell("am start -n ca.zgrs.clipper/.Main")
            sleep(0.25)
        
        #text type : str 
        #text example: Broadcasting: Intent { act=clipper.get flg=0x400000 cmp=ca.zgrs.clipper/.ClipperReceiver }Broadcast completed: result=-1, data="hello"
        clipboard_data = self.shell(f"am broadcast -a clipper.get -n ca.zgrs.clipper/.ClipperReceiver") 
        if self.is_supported_background() == False:
            self.close_clipper()

        text = re.search(r'data="(.*?)"',clipboard_data)
        if text:
            return text.group(1)
        return ""
    
    def set_clipboard(self, text):
        text = escape_special_char(text)
        self.shell(f"am broadcast -a clipper.set -e text \"{text}\" -n ca.zgrs.clipper/.ClipperReceiver")

    def close_clipper(self):
        #focused type : str
        #focused example : mFocusedApp=ActivityRecord{55b302a u0 ca.zgrs.clipper/.Main t2016}
        focused = self.shell("dumpsys window | grep -E 'mFocusedApp'")
        if CLIPPER_PACKAGE in focused:
            self.shell("input keyevent KEYCODE_BACK")

    def is_supported_background(self):
        supported_background = self.adb.sdk_version < SDK_VERSION_ANDROID10
        return supported_background
    
    def shell(self, cmd):
        return self.adb.shell(cmd)

class YosemiteClipboard(Clipboard):
    def __init__(self, adb):
        super(YosemiteClipboard, self).__init__(adb)
        self.adb.pm_update_app(YOSEMITE_APK, YOSEMITE_PACKAGE)

    def get_clipboard(self):
        #text type : str
        #text example : hello
        text = self.adb.shell(f"app_process -Djava.class.path={self.adb.path_app(YOSEMITE_PACKAGE)} / com.netease.nie.yosemite.control.Control --DEVICE_OP clipboard_get")
        if text:
            return text.strip()
        return ""
    
    def set_clipboard(self, text):
        text = escape_special_char(text)
        self.adb.shell(f"app_process -Djava.class.path={self.adb.path_app(YOSEMITE_PACKAGE)} / com.netease.nie.yosemite.control.Control --DEVICE_OP clipboard --TEXT \"{text}\"")


# maps ime_method to clipboard implementation
CLIPBOARD_MAP = {
    CLIPBOARD_METHOD.CLIPPER: ClipperClipboard,
    CLIPBOARD_METHOD.YOSEMITE: YosemiteClipboard,
}

