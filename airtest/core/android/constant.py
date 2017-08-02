# -*- coding: utf-8 -*-
import os


THISPATH = os.path.dirname(os.path.realpath(__file__))
DEFAULT_ADB_SERVER = ('127.0.0.1', 5037)
SDK_VERISON_NEW = 24
DEBUG = True
STFLIB = os.path.join(THISPATH, "stf_libs")
ROTATIONWATCHER_APK = os.path.join(THISPATH, "apks", "RotationWatcher.apk")
ROTATIONWATCHER_PACKAGE = "jp.co.cyberagent.stf.rotationwatcher"
YOSEMITE_APK = os.path.join(THISPATH, "apks", "Yosemite.apk")
YOSEMITE_PACKAGE = 'com.netease.nie.yosemite'
