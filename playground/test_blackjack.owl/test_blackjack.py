#encoding=utf8

__author__ = "刘欣"

import os
PWD = os.path.dirname(__file__)
PKG = "org.cocos2d.blackjack"
APK = os.path.join(PWD, "blackjack-release-signed.apk")
install(APK)
amstop(PKG)
wake()
amstart(PKG)
sleep(2)
touch(MoaPic(r"tpl1499240443959.png", record_pos=(0.22, -0.165), resolution=(2560, 1536)))

assert_exists(MoaPic(r"tpl1499240472304.png", "请下注", record_pos=(0.0, -0.094), resolution=(2560, 1536)))


p = wait(MoaPic(r"tpl1499240490986.png", record_pos=(-0.443, -0.273), resolution=(2560, 1536)))

touch(p)
sleep(2)
amstop(PKG)
