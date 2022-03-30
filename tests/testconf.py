from airtest.core.cv import Template

import os
import shutil
import socket


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
        if os.path.isfile(filepath):
            os.remove(filepath)
        else:
            shutil.rmtree(filepath)


def is_port_open(ip, port):
    """
    测试端口是否可用
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except:
        return False
    finally:
        s.close()
