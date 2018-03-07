#!/usr/bin/env python
# -*- coding: utf-8 -*-

""""Airtest图像识别专用."""
import os
import sys
import time
import types
from airtest import aircv
from airtest.aircv import cv2
from airtest.core.error import TargetNotFoundError
from airtest.core.helper import G, logwrap, log_in_func
from airtest.core.settings import Settings as ST
from airtest.utils.transform import TargetPos
from airtest.utils.compat import PY3
from copy import deepcopy


@logwrap
def loop_find(query, timeout=ST.FIND_TIMEOUT, threshold=None, interval=0.5, intervalfunc=None):
    """
    Search for image template in the screen until timeout

    Args:
        query: image template to be found in screenshot
        timeout: time interval how long to look for the image template
        threshold: default is None
        interval: sleep interval before next attempt to find the image template
        intervalfunc: function that is executed after unsuccessful attempt to find the image template

    Raises:
        TargetNotFoundError: when image template is not found in screenshot

    Returns:
        TargetNotFoundError if image template not found, otherwise returns the position where the image template has
        been found in screenshot

    """
    G.LOGGING.info("Try finding:\n%s", query)
    start_time = time.time()
    while True:
        screen = G.DEVICE.snapshot(filename=None)

        if screen is None:
            G.LOGGING.warning("Screen is None, may be locked")
        else:
            match_pos = query.match_in(screen)
            if match_pos:
                try_log_screen(screen)
                return match_pos

        if intervalfunc is not None:
            intervalfunc()

        # 超时则raise，未超时则进行下次循环:
        if (time.time() - start_time) > timeout:
            try_log_screen(screen)
            raise TargetNotFoundError('Picture %s not found in screen' % query)
        else:
            time.sleep(interval)


def try_log_screen(screen=None):
    """
    Save screenshot to file

    Args:
        screen: screenshot to be saved

    Returns:
        None

    """
    if not ST.LOG_DIR:
        return
    if screen is None:
        screen = G.DEVICE.snapshot()
    filename = "%(time)d.jpg" % {'time': time.time() * 1000}
    filepath = os.path.join(ST.LOG_DIR, filename)
    aircv.imwrite(filepath, screen)
    log_in_func({"screen": filename})


class Template(object):
    """
    picture as touch/swipe/wait/exists target and extra info for cv match
    filename: pic filename
    target_pos: ret which pos in the pic
    record_pos: pos in screen when recording
    resolution: screen resolution when recording
    rgb: 识别结果是否使用rgb三通道进行校验.
    """

    def __init__(self, filename, threshold=None, target_pos=TargetPos.MID, record_pos=None, resolution=(), rgb=False):
        self.filename = filename
        self.filepath = os.path.join(G.BASEDIR, filename) if G.BASEDIR else filename
        self.threshold = threshold or ST.THRESHOLD
        self.target_pos = target_pos
        self.record_pos = record_pos
        self.resolution = resolution
        self.rgb = rgb

    def __repr__(self):
        filepath = self.filepath if PY3 else self.filepath.encode(sys.getfilesystemencoding())
        return "Template(%s)" % filepath

    def match_in(self, screen):
        match_result = self._cv_match(screen)
        G.LOGGING.debug("match result: %s", match_result)
        log_in_func({"cv": match_result})
        if not match_result:
            return None
        focus_pos = TargetPos().getXY(match_result, self.target_pos)
        return focus_pos

    def match_all_in(self, screen):
        image = self._imread()
        image = self._resize_image(image, screen, ST.RESIZE_METHOD)
        return self._find_all_template(image, screen)

    def _cv_match(self, screen):
        # in case image file not exist in current directory:
        image = self._imread()
        image = self._resize_image(image, screen, ST.RESIZE_METHOD)
        ret = None
        for method in ST.CVSTRATEGY:
            if method == "tpl":
                ret = self._try_match(self._find_template, image, screen)
            elif method == "sift":
                ret = self._try_match(self._find_sift_in_predict_area, image, screen)
                if not ret:
                    ret = self._try_match(self._find_sift, image, screen)
            else:
                G.LOGGING.warning("Undefined method in CV_STRATEGY: %s", method)
            if ret:
                break
        return ret

    @staticmethod
    def _try_match(method, *args, **kwargs):
        G.LOGGING.debug("try match with %s" % method.__name__)
        try:
            ret = method(*args, **kwargs)
        except aircv.BaseError as err:
            G.LOGGING.debug(repr(err))
            return None
        else:
            return ret

    def _imread(self):
        return aircv.imread(self.filepath)

    def _find_all_template(self, image, screen):
        return aircv.find_all_template(screen, image, threshold=self.threshold, rgb=self.rgb)

    def _find_template(self, image, screen):
        return aircv.find_template(screen, image, threshold=self.threshold, rgb=self.rgb)

    def _find_sift(self, image, screen):
        return aircv.find_sift(screen, image, threshold=self.threshold, rgb=self.rgb)

    def _find_sift_in_predict_area(self, image, screen):
        if not self.record_pos:
            return None
        # calc predict area in screen
        screen_resolution = aircv.get_resolution(screen)
        xmin, ymin, xmax, ymax = Predictor.get_predict_area(self.record_pos, screen_resolution)
        # crop predict image from screen
        predict_area = aircv.crop_image(screen, (xmin, ymin, xmax, ymax))
        # aircv.show(predict_area)
        # find sift in that image
        ret_in_area = aircv.find_sift(predict_area, image, threshold=self.threshold, rgb=self.rgb)
        # calc cv ret if found
        if not ret_in_area:
            return None
        ret = deepcopy(ret_in_area)
        ret["result"] = (ret_in_area["result"][0] + xmin, ret_in_area["result"][1] + ymin)
        return ret

    def _resize_image(self, image, screen, resize_method):
        """模板匹配中，将输入的截图适配成 等待模板匹配的截图."""
        screen_resolution = aircv.get_resolution(screen)
        # 如果分辨率一致，则不需要进行im_search的适配:
        if tuple(self.resolution) == tuple(screen_resolution) or resize_method is None:
            return image
        if isinstance(resize_method, types.MethodType):
            resize_method = resize_method.__func__
        # 分辨率不一致则进行适配，默认使用cocos_min_strategy:
        h, w = image.shape[:2]
        w_re, h_re = resize_method(w, h, self.resolution, screen_resolution)
        # 确保w_re和h_re > 0, 至少有1个像素:
        w_re, h_re = max(1, w_re), max(1, h_re)
        # 调试代码: 输出调试信息.
        G.LOGGING.debug("resize: (%s, %s)->(%s, %s), resolution: %s=>%s" % (
                        w, h, w_re, h_re, self.resolution, screen_resolution))
        # 进行图片缩放:
        image = cv2.resize(image, (w_re, h_re))
        return image


class Predictor(object):
    """
    this class predicts the press_point and the area to search im_search.
    """

    RADIUS_X = 250
    RADIUS_Y = 250

    @staticmethod
    def count_record_pos(pos, resolution):
        """计算坐标对应的中点偏移值相对于分辨率的百分比"""
        _w, _h = resolution
        # 都按宽度缩放，针对G18的实验结论
        delta_x = (pos[0] - _w * 0.5) / _w
        delta_y = (pos[1] - _h * 0.5) / _w
        delta_x = round(delta_x, 3)
        delta_y = round(delta_y, 3)
        return delta_x, delta_y

    @classmethod
    def get_predict_point(cls, record_pos, screen_resolution):
        """预测缩放后的点击位置点"""
        delta_x, delta_y = record_pos
        _w, _h = screen_resolution
        target_x = delta_x * _w + _w * 0.5
        target_y = delta_y * _w + _h * 0.5
        return target_x, target_y

    @classmethod
    def get_predict_area(cls, record_pos, screen_resolution):
        x, y = cls.get_predict_point(record_pos, screen_resolution)
        area = (x - cls.RADIUS_X, y - cls.RADIUS_Y, x + cls.RADIUS_X, y + cls.RADIUS_Y)
        return area
