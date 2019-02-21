# encoding=utf8

__author__ = "刘欣"

from airtest.core.api import *
from airtest.cli.parser import cli_setup


PKG = "org.cocos2d.blackjack"
APK = "blackjack-release-signed.apk"


if not cli_setup():
    auto_setup(__file__, logdir=True, devices=[
        "Android:///?cap_method=javacap&ori_method=adbori",
    ])

# install and start the app
wake()
home()

if PKG not in device().list_app():
    install(APK)

stop_app(PKG)
start_app(PKG)
sleep(2)

# next 3 sentences are generated with AirtestIDE
touch(Template(r"tpl1499240443959.png", record_pos=(0.22, -0.165), resolution=(2560, 1536)))
assert_exists(Template(r"tpl1499240472304.png", record_pos=(0.0, -0.094), resolution=(2560, 1536)), "请下注")
p = wait(Template(r"tpl1499240490986.png", record_pos=(-0.443, -0.273), resolution=(2560, 1536)))

# touch a position
touch(p)
sleep(2)

# stop the app
stop_app(PKG)
sleep(2)
snapshot(msg="app stopped")

print("test finished")

# generate html report
from airtest.report.report import simple_report
simple_report(__file__)
