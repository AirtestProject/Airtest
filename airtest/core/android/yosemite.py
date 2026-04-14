import traceback
import warnings
from .constant import YOSEMITE_APK, YOSEMITE_PACKAGE
from airtest.utils.snippet import on_method_ready
from airtest.utils.apkparser import APK
from airtest.utils.logger import get_logger
LOGGING = get_logger(__name__)


class Yosemite(object):
    """Wrapper class of Yosemite.apk, used by javacap/recorder/yosemite_ime."""

    def __init__(self, adb):
        self.adb = adb

    def install_or_upgrade(self):
        """
        Install or update the Yosemite.apk file on the device

        Returns:
            None

        """
        self.adb.pm_update_app(YOSEMITE_APK, YOSEMITE_PACKAGE)

    @on_method_ready('install_or_upgrade')
    def get_ready(self):
        pass

    def uninstall(self):
        """
        Uninstall `Yosemite.apk` application from the device

        Returns:
            None

        """
        self.adb.uninstall_app(YOSEMITE_PACKAGE)
