# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""多尺度模板匹配.

对用户提供的调节参数:
    1. threshod: 筛选阈值，默认为0.8
    2. rgb: 彩色三通道,进行彩色权识别.
    3. scale_max: 多尺度模板匹配最大范围，增大可适应更小UI
    4. scale_step: 多尺度模板匹配搜索比例步长，减小可适应更小UI
"""

import cv2
import time

from airtest.utils.logger import get_logger
from .utils import generate_result, check_source_larger_than_search, img_mat_rgb_2_gray
from .cal_confidence import cal_rgb_confidence

LOGGING = get_logger(__name__)


def print_run_time(func):

    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        ret = func(self, *args, **kwargs)
        LOGGING.debug("%s() run time is %.2f s." %
                      (func.__name__, time.time() - start_time))
        return ret

    return wrapper


class MultiScaleTemplateMatching(object):
    """多尺度模板匹配."""

    METHOD_NAME = "Template"
    MAX_RESULT_COUNT = 10

    def __init__(self, im_search, im_source, threshold=0.8, rgb=True, resolution=(), scale_max=800, scale_step=0.01):
        super(MultiScaleTemplateMatching, self).__init__()
        self.im_source = im_source
        self.im_search = im_search
        self.threshold = threshold
        self.rgb = rgb
        self.resolution = resolution
        self.scale_max = scale_max
        self.scale_step = scale_step

    def find_all_results(self):
        raise NotImplementedError

    @print_run_time
    def find_best_result(self):
        """函数功能：找到最优结果."""
        # 第一步：校验图像输入
        check_source_larger_than_search(self.im_source, self.im_search)

        # 第二步：计算模板匹配的结果矩阵res
        s_gray, i_gray = img_mat_rgb_2_gray(
            self.im_search), img_mat_rgb_2_gray(self.im_source)
        r_min, r_max = self._get_ratio(
            self.im_source, self.im_search, self.resolution)
        max_val, max_loc, w, h, r = self.multi_scale_search(
            i_gray, s_gray, ratio_min=max(r_min, self.scale_step), ratio_max=min(r_max, 0.99), step=self.scale_step, threshold=self.threshold)
        confidence = self._get_confidence_from_matrix(
            max_loc, max_val, w, h)
        if confidence < self.threshold:
            max_val, max_loc, w, h, r = self.multi_scale_search(
                i_gray, s_gray, ratio_min=0.01, ratio_max=1.0, src_max=self.scale_max, step=self.scale_step, threshold=self.threshold)
            confidence = self._get_confidence_from_matrix(
                max_loc, max_val, w, h)

        # 求取识别位置: 目标中心 + 目标区域:
        middle_point, rectangle = self._get_target_rectangle(max_loc, w, h)
        best_match = generate_result(middle_point, rectangle, confidence)
        LOGGING.debug("[%s] threshold=%s, result=%s" %
                      (self.METHOD_NAME, self.threshold, best_match))

        return best_match if confidence >= self.threshold else None

    def _get_confidence_from_matrix(self, max_loc, max_val, w, h):
        """根据结果矩阵求出confidence."""
        # 求取可信度:
        if self.rgb:
            # 如果有颜色校验,对目标区域进行BGR三通道校验:
            img_crop = self.im_source[max_loc[1]:max_loc[1] + h, max_loc[0]: max_loc[0] + w]
            confidence = cal_rgb_confidence(img_crop, self.im_search)
        else:
            confidence = max_val

        return confidence

    def _get_target_rectangle(self, left_top_pos, w, h):
        """根据左上角点和宽高求出目标区域."""
        x_min, y_min = left_top_pos
        # 中心位置的坐标:
        x_middle, y_middle = int(x_min + w / 2), int(y_min + h / 2)
        # 左下(min,max)->右下(max,max)->右上(max,min)
        left_bottom_pos, right_bottom_pos = (
            x_min, y_min + h), (x_min + w, y_min + h)
        right_top_pos = (x_min + w, y_min)
        # 点击位置:
        middle_point = (x_middle, y_middle)
        # 识别目标区域: 点序:左上->左下->右下->右上, 左上(min,min)右下(max,max)
        rectangle = (left_top_pos, left_bottom_pos,
                     right_bottom_pos, right_top_pos)

        return middle_point, rectangle

    def _get_ratio(self, src, templ, resolution):
        """获取缩放比的上下限."""
        H, W = src.shape[0], src.shape[1]
        th, tw = templ.shape[0], templ.shape[1]
        if resolution == ():
            r_min = r_max = max(th/H, tw/W)
            return r_min, r_max
        else:
            w, h = resolution
            rmin = min(H/h, W/w) # 新旧模板比下限
            rmax = max(H/h, W/w) # 新旧模板比上限
            ratio = max(th/H, tw/W) # 小图大图比
            r_min = ratio*rmin
            r_max = ratio*rmax
            return r_min, r_max 

    @staticmethod
    def _resize_by_ratio(src, templ, ratio=1.0, max_tr_ratio=0.2):
        """根据模板相对屏幕的长边 按比例缩放屏幕"""
        th, tw = templ.shape[0], templ.shape[1]
        h, w = src.shape[0], src.shape[1]
        tr = sr = 1.0
        if th/h >= tw/w:
            if ratio <max_tr_ratio:
                tr = (h*ratio)/th
            else:
                tr = (h*max_tr_ratio)/th
                sr = (th*tr/ratio)/h
        else:
            if ratio < max_tr_ratio:
                tr = (w*ratio)/tw
            else:
                tr = (w*max_tr_ratio)/tw
                sr = (tw*tr/ratio)/w
        if tr <= 1:
            templ = cv2.resize(templ, (max(int(tw*tr), 1), max(int(th*tr), 1)))
        if sr <= 1:
            src = cv2.resize(src, (int(w*sr), int(h*sr)))
        return src, templ, tr, sr

    @staticmethod
    def _org_size(max_loc, w, h, tr, sr):
        """获取原始比例的框"""
        max_loc = (int(max_loc[0]/sr), int(max_loc[1]/sr))
        w, h = int(w/sr), int(h/sr)
        return max_loc, w, h

    def multi_scale_search(self, org_src, org_templ, templ_min=10, src_max=800, ratio_min=0.01, ratio_max=1.0, step=0.01, threshold=0.9):
        """多尺度模板匹配"""
        gr = src_max/max(org_src.shape)
        if gr < 1.0:
            org_src = cv2.resize(org_src.copy(), (int(
                org_src.shape[1]*gr), int(org_src.shape[0]*gr)))
        mmax_val = 0
        max_info = None
        ratio_min, ratio_max = max(ratio_min, step), max(ratio_max, step)
        r = ratio_min
        while r <= ratio_max:
            src, templ, tr, sr = self._resize_by_ratio(
                org_src.copy(), org_templ.copy(), r)
            if min(templ.shape) > templ_min:
                result = cv2.matchTemplate(src, templ, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                h, w = templ.shape
                if mmax_val < max_val:
                    mmax_val = max_val
                    max_info = (r, max_val, max_loc, w, h, tr, sr)
                # print((r, max_val, max_loc, w, h, tr, sr))
                if max_val >= threshold:
                    break
            r += step
        r, max_val, max_loc, w, h, tr, sr = max_info
        max_loc, w, h = self._org_size(max_loc, w, h, tr, sr)
        if gr < 1.0:
            max_loc, w, h = (
                int(max_loc[0]/gr), int(max_loc[1]/gr)), int(w/gr), int(h/gr)
        return max_val, max_loc, w, h, r
