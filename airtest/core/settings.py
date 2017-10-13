# -*- coding: utf-8 -*-
from airtest.core.utils import cocos_min_strategy


class Settings(object):

    DEBUG = False
    LOG_DIR = "."
    LOG_FILE = "log.txt"
    SCREEN_DIR = "img_record"
    RESIZE_METHOD = staticmethod(cocos_min_strategy)
    SRC_RESOLUTION = []  # to be move to DEVICE
    CVSTRATEGY = ["tpl", "sift"]
    PREDICTION = False  # use prediction in sift
    FIND_INSIDE = None  # [0, 1] 4 elements-list
    FIND_OUTSIDE = None  # [0, 1] 4 elements-list
    THRESHOLD = 0.6  # [0, 1]
    THRESHOLD_STRICT = 0.7  # [0, 1]
    OPDELAY = 0.1
    FIND_TIMEOUT = 20
    FIND_TIMEOUT_TMP = 3
