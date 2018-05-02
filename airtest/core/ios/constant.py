# -*- coding: utf-8 -*-
import os
import re
import sys
from airtest.utils.compat import decode_path

THISPATH = decode_path(os.path.dirname(os.path.realpath(__file__)))
STATICPATH = os.path.join(THISPATH, "static")

DEFAULT_ADB_SERVER = ('127.0.0.1', 8100)
DEBUG = True
MINICAPLIB = os.path.join(STATICPATH, "minicap")
IP_PATTERN = re.compile(r'(\d+\.){3}\d+')


class CAP_METHOD(object):
    MINICAP = "MINICAP"
    MINICAP_STREAM = "MINICAP_STREAM"
    WDACAP = "WDACAP"


# now touch and ime only support wda
class TOUCH_METHOD(object):
    WDATOUCH = "WDATOUCH"


class IME_METHOD(object):
    WDAIME = "WDAIME"
