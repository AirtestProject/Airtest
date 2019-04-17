# -*- coding: utf-8 -*-
from airtest.utils.resolution import cocos_min_strategy
import os


class Settings(object):

    DEBUG = False
    LOG_DIR = None
    LOG_FILE = "log.txt"
    RESIZE_METHOD = staticmethod(cocos_min_strategy)
    CVSTRATEGY = ["surf", "tpl", "brisk"]  # keypoint matching: kaze/brisk/akaze/orb, contrib: sift/surf/brief
    KEYPOINT_MATCHING_PREDICTION = True
    THRESHOLD = 0.7  # [0, 1]
    THRESHOLD_STRICT = 0.7  # [0, 1]
    OPDELAY = 0.1
    FIND_TIMEOUT = 20
    FIND_TIMEOUT_TMP = 3
    PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "")  # for ``using`` other script
