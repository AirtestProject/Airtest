# -*- coding: utf-8 -*-
from airtest.utils.resolution import cocos_min_strategy


class Settings(object):

    DEBUG = False
    LOG_DIR = None
    LOG_FILE = "log.txt"
    RESIZE_METHOD = staticmethod(cocos_min_strategy)
    CVSTRATEGY = ["tpl", "sift"]
    THRESHOLD = 0.6  # [0, 1]
    THRESHOLD_STRICT = 0.7  # [0, 1]
    OPDELAY = 0.1
    FIND_TIMEOUT = 20
    FIND_TIMEOUT_TMP = 3
