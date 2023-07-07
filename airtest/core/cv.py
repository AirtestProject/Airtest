#!/usr/bin/env python
# -*- coding: utf-8 -*-

""""Airtest图像识别专用."""

import os
import sys
import time
import types
from six import PY3
from copy import deepcopy

from airtest import aircv
from airtest.aircv import cv2
from airtest.core.helper import G, logwrap
from airtest.core.settings import Settings as ST  # noqa
from airtest.core.error import TargetNotFoundError, InvalidMatchingMethodError
from airtest.utils.transform import TargetPos

from airtest.aircv.template_matching import TemplateMatching
from airtest.aircv.multiscale_template_matching import MultiScaleTemplateMatching,MultiScaleTemplateMatchingPre
from airtest.aircv.keypoint_matching import KAZEMatching, BRISKMatching, AKAZEMatching, ORBMatching
from airtest.aircv.keypoint_matching_contrib import SIFTMatching, SURFMatching, BRIEFMatching

MATCHING_METHODS = {
    "tpl": TemplateMatching,
    "mstpl": MultiScaleTemplateMatchingPre,
    "gmstpl": MultiScaleTemplateMatching,
    "kaze": KAZEMatching,
    "brisk": BRISKMatching,
    "akaze": AKAZEMatching,
    "orb": ORBMatching,
    "sift": SIFTMatching,
    "surf": SURFMatching,
    "brief": BRIEFMatching,
}


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
    G.LOGGING.info("Try finding: %s", query)
    start_time = time.time()
    while True:
        screen = G.DEVICE.snapshot(filename=None, quality=ST.SNAPSHOT_QUALITY)

        if screen is None:
            G.LOGGING.warning("Screen is None, may be locked")
        else:
            if threshold:
                query.threshold = threshold
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


@logwrap
def try_log_screen(screen=None, quality=None, max_size=None):
    """
    Save screenshot to file

    Args:
        screen: screenshot to be saved
        quality: The image quality, default is ST.SNAPSHOT_QUALITY
        max_size: the maximum size of the picture, e.g 1200

    Returns:
        {"screen": filename, "resolution": aircv.get_resolution(screen)}

    """
    if not ST.LOG_DIR or not ST.SAVE_IMAGE:
        return
    if not quality:
        quality = ST.SNAPSHOT_QUALITY
    if not max_size:
        max_size = ST.IMAGE_MAXSIZE
    if screen is None:
        screen = G.DEVICE.snapshot(quality=quality)
    filename = "%(time)d.jpg" % {'time': time.time() * 1000}
    filepath = os.path.join(ST.LOG_DIR, filename)
    if screen is not None:
        aircv.imwrite(filepath, screen, quality, max_size=max_size)
        return {"screen": filename, "resolution": aircv.get_resolution(screen)}
    return None


class Template(object):
    """
    picture as touch/swipe/wait/exists target and extra info for cv match
    filename: pic filename
    target_pos: ret which pos in the pic
    record_pos: pos in screen when recording
    resolution: screen resolution when recording
    rgb: 识别结果是否使用rgb三通道进行校验.
    scale_max: 多尺度模板匹配最大范围.
    scale_step: 多尺度模板匹配搜索步长.
    """

    def __init__(self, filename, threshold=None, target_pos=TargetPos.MID, record_pos=None, resolution=(), rgb=False, scale_max=800, scale_step=0.005):
        self.filename = filename
        self._filepath = None
        self.threshold = threshold or ST.THRESHOLD
        self.target_pos = target_pos
        self.record_pos = record_pos
        self.resolution = resolution
        self.rgb = rgb
        self.scale_max = scale_max
        self.scale_step = scale_step

    @property
    def filepath(self):
        if self._filepath:
            return self._filepath
        for dirname in G.BASEDIR:
            filepath = os.path.join(dirname, self.filename)
            if os.path.isfile(filepath):
                self._filepath = filepath
                return self._filepath
        return self.filename

    def __repr__(self):
        filepath = self.filepath if PY3 else self.filepath.encode(sys.getfilesystemencoding())
        return "Template(%s)" % filepath

    def match_in(self, screen):
        match_result = self._cv_match(screen)
        G.LOGGING.debug("match result: %s", match_result)
        if not match_result:
            return None
        focus_pos = TargetPos().getXY(match_result, self.target_pos)
        return focus_pos

    def match_all_in(self, screen):
        image = self._imread()
        image = self._resize_image(image, screen, ST.RESIZE_METHOD)
        return self._find_all_template(image, screen)

    @logwrap
    def _cv_match(self, screen):
        # in case image file not exist in current directory:
        ori_image = self._imread()
        image = self._resize_image(ori_image, screen, ST.RESIZE_METHOD)
        ret = None
        for method in ST.CVSTRATEGY:
            # get function definition and execute:
            func = MATCHING_METHODS.get(method, None)
            if func is None:
                raise InvalidMatchingMethodError("Undefined method in CVSTRATEGY: '%s', try 'kaze'/'brisk'/'akaze'/'orb'/'surf'/'sift'/'brief' instead." % method)
            else:
                if method in ["mstpl", "gmstpl"]:
                    ret = self._try_match(func, ori_image, screen, threshold=self.threshold, rgb=self.rgb, record_pos=self.record_pos,
                                            resolution=self.resolution, scale_max=self.scale_max, scale_step=self.scale_step)
                else:
                    ret = self._try_match(func, image, screen, threshold=self.threshold, rgb=self.rgb)
            if ret:
                break
        return ret

    @staticmethod
    def _try_match(func, *args, **kwargs):
        G.LOGGING.debug("try match with %s" % func.__name__)
        try:
            ret = func(*args, **kwargs).find_best_result()
        except aircv.NoModuleError as err:
            G.LOGGING.warning("'surf'/'sift'/'brief' is in opencv-contrib module. You can use 'tpl'/'kaze'/'brisk'/'akaze'/'orb' in CVSTRATEGY, or reinstall opencv with the contrib module.")
            return None
        except aircv.BaseError as err:
            G.LOGGING.debug(repr(err))
            return None
        else:
            return ret

    def _imread(self):
        return aircv.imread(self.filepath)

    def _find_all_template(self, image, screen):
        return TemplateMatching(image, screen, threshold=self.threshold, rgb=self.rgb).find_all_results()

    def _find_keypoint_result_in_predict_area(self, func, image, screen):
        if not self.record_pos:
            return None
        # calc predict area in screen
        image_wh, screen_resolution = aircv.get_resolution(image), aircv.get_resolution(screen)
        xmin, ymin, xmax, ymax = Predictor.get_predict_area(self.record_pos, image_wh, self.resolution, screen_resolution)
        # crop predict image from screen
        predict_area = aircv.crop_image(screen, (xmin, ymin, xmax, ymax))
        if not predict_area.any():
            return None
        # keypoint matching in predicted area:
        ret_in_area = func(image, predict_area, threshold=self.threshold, rgb=self.rgb)
        # calc cv ret if found
        if not ret_in_area:
            return None
        ret = deepcopy(ret_in_area)
        if "rectangle" in ret:
            for idx, item in enumerate(ret["rectangle"]):
                ret["rectangle"][idx] = (item[0] + xmin, item[1] + ymin)
        ret["result"] = (ret_in_area["result"][0] + xmin, ret_in_area["result"][1] + ymin)
        return ret

    def _resize_image(self, image, screen, resize_method):
        """模板匹配中，将输入的截图适配成 等待模板匹配的截图."""
        # 未记录录制分辨率，跳过
        if not self.resolution:
            return image
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

    DEVIATION = 100

    @staticmethod
    def count_record_pos(pos, resolution):
        """计算坐标对应的中点偏移值相对于分辨率的百分比."""
        _w, _h = resolution
        # 都按宽度缩放，针对G18的实验结论
        delta_x = (pos[0] - _w * 0.5) / _w
        delta_y = (pos[1] - _h * 0.5) / _w
        delta_x = round(delta_x, 3)
        delta_y = round(delta_y, 3)
        return delta_x, delta_y

    @classmethod
    def get_predict_point(cls, record_pos, screen_resolution):
        """预测缩放后的点击位置点."""
        delta_x, delta_y = record_pos
        _w, _h = screen_resolution
        target_x = delta_x * _w + _w * 0.5
        target_y = delta_y * _w + _h * 0.5
        return target_x, target_y

    @classmethod
    def get_predict_area(cls, record_pos, image_wh, image_resolution=(), screen_resolution=()):
        """Get predicted area in screen."""
        x, y = cls.get_predict_point(record_pos, screen_resolution)
        # The prediction area should depend on the image size:
        if image_resolution:
            predict_x_radius = int(image_wh[0] * screen_resolution[0] / (2 * image_resolution[0])) + cls.DEVIATION
            predict_y_radius = int(image_wh[1] * screen_resolution[1] / (2 * image_resolution[1])) + cls.DEVIATION
        else:
            predict_x_radius, predict_y_radius = int(image_wh[0] / 2) + cls.DEVIATION, int(image_wh[1] / 2) + cls.DEVIATION
        area = (x - predict_x_radius, y - predict_y_radius, x + predict_x_radius, y + predict_y_radius)
        return area
