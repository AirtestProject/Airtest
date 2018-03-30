#encoding=utf8

__author__ = "刘欣"

import os
from time import sleep
from airtest.core.api import (Template, assert_exists, device, install,
                              start_app, stop_app, touch, wake)

PWD = args.script
PKG = "org.cocos2d.blackjack"
APK = os.path.join(PWD, "blackjack-release-signed.apk")
if PKG not in device().list_app():
    install(APK)
stop_app(PKG)
wake()
start_app(PKG)
sleep(2)
touch(Template(r"tpl1499240443959.png", record_pos=(0.22, -0.165), resolution=(2560, 1536)))

assert_exists(Template(r"tpl1499240472304.png", record_pos=(0.0, -0.094), resolution=(2560, 1536)), "请下注")

p = wait(Template(r"tpl1499240490986.png", record_pos=(-0.443, -0.273), resolution=(2560, 1536)))

touch(p)
sleep(2)
stop_app(PKG)
