# -*- coding: utf-8 -*-
from airtest.utils.resolution import cocos_min_strategy
import os
import cv2
from distutils.version import LooseVersion


class Settings(object):

    DEBUG = False
    LOG_DIR = None
    LOG_FILE = "log.txt"
    RESIZE_METHOD = staticmethod(cocos_min_strategy)
    # keypoint matching: kaze/brisk/akaze/orb, contrib: sift/surf/brief
    CVSTRATEGY = ["mstpl", "tpl", "sift", "brisk"]
    if LooseVersion('3.4.2') < LooseVersion(cv2.__version__) < LooseVersion('4.4.0'):
        CVSTRATEGY = ["mstpl", "tpl", "brisk"]
    KEYPOINT_MATCHING_PREDICTION = True
    THRESHOLD = 0.7  # [0, 1]
    THRESHOLD_STRICT = None  # dedicated parameter for assert_exists
    OPDELAY = 0.1
    FIND_TIMEOUT = 20
    FIND_TIMEOUT_TMP = 3
    PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "")  # for ``using`` other script
    SNAPSHOT_QUALITY = 10  # 1-100 https://pillow.readthedocs.io/en/5.1.x/handbook/image-file-formats.html#jpeg
    # Image compression size, e.g. 1200, means that the size of the screenshot does not exceed 1200*1200
    IMAGE_MAXSIZE = os.environ.get("IMAGE_MAXSIZE", None)
    SAVE_IMAGE = True
