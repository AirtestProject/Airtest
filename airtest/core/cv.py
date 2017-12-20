#!/usr/bin/env python
# -*- coding: utf-8 -*-

""""Airtest图像识别专用."""
import os
import time
from airtest import aircv
from airtest.aircv.match import cv_match, cv_match_all
from airtest.core.error import TargetNotFoundError
from airtest.core.helper import G, logwrap, log_in_func
from airtest.core.settings import Settings as ST
from airtest.utils.transform import TargetPos


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
                _try_save_screen(screen)
                return match_pos

        if intervalfunc is not None:
            intervalfunc()

        # 超时则raise，未超时则进行下次循环:
        if (time.time() - start_time) > timeout:
            _try_save_screen(screen)
            raise TargetNotFoundError('Picture %s not found in screen' % query)
        else:
            time.sleep(interval)


def _try_save_screen(screen):
    """
    Save screenshot to file

    Args:
        screen: screenshot to be saved

    Returns:
        None

    """
    if not ST.LOG_DIR:
        return
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
    ignore: [ [x_min, y_min, x_max, y_max], ... ]  识别时，忽略掉ignore包含的矩形区域 (mask_tpl)
    focus: [ [x_min, y_min, x_max, y_max], ... ]  识别时，只识别focus包含的矩形区域 (可信度为面积加权平均)
    rgb: 识别结果是否使用rgb三通道进行校验.
    """

    def __init__(self, filename, threshold=None, target_pos=TargetPos.MID, record_pos=None, resolution=(), ignore=None, focus=None, rgb=False):
        self.filename = filename
        self.filepath = os.path.join(G.BASEDIR, filename) if G.BASEDIR else filename
        self.threshold = threshold or ST.THRESHOLD
        self.target_pos = target_pos
        self.record_pos = record_pos
        self.resolution = resolution
        self.ignore = ignore
        self.focus = focus
        self.rgb = rgb
        self._resize_method = ST.RESIZE_METHOD

    def __repr__(self):
        return "Template(%s)" % self.filepath

    def imread(self):
        """获取搜索图像(cv2格式)."""
        return aircv.imread(self.filepath)

    def match_in(self, source):
        match_result = cv_match(source, self, strategies=ST.CVSTRATEGY)
        G.LOGGING.debug("match result: %s", match_result)
        log_in_func({"cv": match_result})
        if not match_result:
            return None
        focus_pos = TargetPos().getXY(match_result, self.target_pos)
        return focus_pos

    def _cv_match(self, source):
        pass

    def _find_all_with_template(self, screen):
        pass

    def _find_with_template(self, screen):
        pass

    def _find_with_sift(self, screen):
        pass

    def _img_after_predict(self):
        pass

    def _img_after_resize(self):
        pass

    def _img_after_focus(self):
        pass

    def _img_after_ignore(self):
        pass
