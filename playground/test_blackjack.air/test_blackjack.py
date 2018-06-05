# -*- encoding=utf8 -*-
__author__ = "刘欣"

from airtest.core.api import *
import os

auto_setup(__file__)

PWD = os.path.dirname(__file__)
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

swipe(Template(r"tpl1523932626575.png", record_pos=(-0.266, 0.105), resolution=(1920, 1080)), vector=[0.0005, -0.4023])
assert_exists(Template(r"tpl1523933150565.png", record_pos=(-0.213, 0.103), resolution=(1920, 1080)), "Swipe succeed")

log("Test OK")

sleep(2)
stop_app(PKG)
