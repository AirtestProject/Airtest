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
        self._install_apk_upgrade(YOSEMITE_APK, YOSEMITE_PACKAGE)

    def _install_apk_upgrade(self, apk_path, package):
        """
        Install or update the `.apk` file on the device

        Args:
            apk_path: full path `.apk` file
            package: package name

        Returns:
            None

        """
        apk_version = int(APK(apk_path).androidversion_code)
        installed_version = self.adb.get_package_version(package)
        LOGGING.info("local version code is {}, installed version code is {}".format(apk_version, installed_version))
        if installed_version is None or apk_version > int(installed_version):
            self.adb.install_app(apk_path, replace=True)

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
