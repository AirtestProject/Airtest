from airtest.core.cv import Template

import os


THISDIR = os.path.dirname(__file__)
DIR = lambda x: os.path.join(THISDIR, x)
APK = DIR("../playground/test_blackjack.air/blackjack-release-signed.apk")
PKG = "org.cocos2d.blackjack"
OWL = DIR("../playground/test_blackjack.air")
IMG = os.path.join(OWL, "tpl1499240443959.png")
TPL = Template(IMG, record_pos=(0.22, -0.165), resolution=(2560, 1536))
TPL2 = Template(os.path.join(OWL, "tpl1499240472304.png"), record_pos=(0.0, -0.094), resolution=(2560, 1536))


def try_remove(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
