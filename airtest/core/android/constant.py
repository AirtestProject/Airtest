# -*- coding: utf-8 -*-
import os


THISPATH = os.path.dirname(os.path.realpath(__file__))
STFLIB = os.path.join(THISPATH, "stf_libs")
DEFAULT_ADB_SERVER = ('127.0.0.1', 5037)
PROJECTIONRATE = 1
MINICAPTIMEOUT = None
ORIENTATION_MAP = {0: 0, 1: 90, 2: 180, 3: 270}
DEBUG = True
ROTATIONWATCHER_APK = os.path.join(THISPATH, "apks", "RotationWatcher.apk")
ROTATIONWATCHER_PACKAGE = "jp.co.cyberagent.stf.rotationwatcher"
YOSEMITE_APK = os.path.join(THISPATH, "apks", "Yosemite.apk")
YOSEMITE_PACKAGE = 'com.netease.nie.yosemite'
