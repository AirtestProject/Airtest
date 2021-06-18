# -*- coding: utf-8 -*-
import os
import re
import sys
import subprocess
from airtest.utils.compat import decode_path

THISPATH = decode_path(os.path.dirname(os.path.realpath(__file__)))
STATICPATH = os.path.join(THISPATH, "static")
DEFAULT_ADB_PATH = {
    "Windows": os.path.join(STATICPATH, "adb", "windows", "adb.exe"),
    "Darwin": os.path.join(STATICPATH, "adb", "mac", "adb"),
    "Linux": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-x86_64": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-armv7l": os.path.join(STATICPATH, "adb", "linux_arm", "adb"),
}
DEFAULT_ADB_SERVER = ('127.0.0.1', 5037)
SDK_VERISON_ANDROID7 = 24
# Android 10 SDK version
SDK_VERISON_ANDROID10 = 29
DEBUG = True
STFLIB = os.path.join(STATICPATH, "stf_libs")
ROTATIONWATCHER_APK = os.path.join(STATICPATH, "apks", "RotationWatcher.apk")
ROTATIONWATCHER_PACKAGE = "jp.co.cyberagent.stf.rotationwatcher"
YOSEMITE_APK = os.path.join(STATICPATH, "apks", "Yosemite.apk")
YOSEMITE_PACKAGE = 'com.netease.nie.yosemite'
YOSEMITE_IME_SERVICE = 'com.netease.nie.yosemite/.ime.ImeService'
MAXTOUCH_JAR = os.path.join(STATICPATH, "apks", "maxpresent.jar")
ROTATIONWATCHER_JAR = os.path.join(STATICPATH, "apks", "rotationwatcher.jar")
IP_PATTERN = re.compile(r'(\d+\.){3}\d+')


class CAP_METHOD(object):
    MINICAP = "MINICAP"
    ADBCAP = "ADBCAP"
    JAVACAP = "JAVACAP"


class TOUCH_METHOD(object):
    MINITOUCH = "MINITOUCH"
    MAXTOUCH = "MAXTOUCH"
    ADBTOUCH = "ADBTOUCH"


class IME_METHOD(object):
    ADBIME = "ADBIME"
    YOSEMITEIME = "YOSEMITEIME"


class ORI_METHOD(object):
    ADB = "ADBORI"
    MINICAP = "MINICAPORI"
