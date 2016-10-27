# -*- coding: utf-8 -*-
import os


THISPATH = os.path.dirname(os.path.realpath(__file__))
STFLIB = os.path.join(THISPATH, "stf_libs")
DEFAULT_ADB_SERVER = ('127.0.0.1', 5037)
PROJECTIONRATE = 1
MINICAPTIMEOUT = None
ORIENTATION_MAP = {0: 0, 1: 90, 2: 180, 3: 270}
DEBUG = True
RELEASELOCK_APK = os.path.join(THISPATH, "apks", "releaselock.apk")
RELEASELOCK_PACKAGE = "com.netease.releaselock"
ACCESSIBILITYSERVICE_APK = os.path.join(THISPATH, "apks", "AccessibilityService.apk")
ACCESSIBILITYSERVICE_PACKAGE = "com.netease.accessibility"
ACCESSIBILITYSERVICE_VERSION = 3.0
ROTATIONWATCHER_APK = os.path.join(THISPATH, "apks", "RotationWatcher.apk")
ROTATIONWATCHER_PACKAGE = "jp.co.cyberagent.stf.rotationwatcher"
