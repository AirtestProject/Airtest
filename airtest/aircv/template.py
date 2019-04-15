# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""模板匹配.

对用户提供的调节参数:
    1. threshod: 筛选阈值，默认为0.8
    2. rgb: 彩色三通道,进行彩色权识别.
"""


import cv2
from airtest.utils.logger import get_logger
from .utils import generate_result, check_source_larger_than_search, img_mat_rgb_2_gray
from .cal_confidence import cal_rgb_confidence
LOGGING = get_logger(__name__)


def find_template(im_source, im_search, threshold=0.8, rgb=False):
    """函数功能：找到最优结果."""
    # 第一步：校验图像输入
    check_source_larger_than_search(im_source, im_search)
    # 第二步：计算模板匹配的结果矩阵res
    res = _get_template_result_matrix(im_source, im_search)
    # 第三步：依次获取匹配结果
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    h, w = im_search.shape[:2]
    # 求取可信度:
    confidence = _get_confidence_from_matrix(im_source, im_search, max_loc, max_val, w, h, rgb)
    # 求取识别位置: 目标中心 + 目标区域:
    middle_point, rectangle = _get_target_rectangle(max_loc, w, h)
    best_match = generate_result(middle_point, rectangle, confidence)
    LOGGING.debug("threshold=%s, result=%s" % (threshold, best_match))
    return best_match if confidence >= threshold else None


def find_all_template(im_source, im_search, threshold=0.8, rgb=False, max_count=10):
    """根据输入图片和参数设置,返回所有的图像识别结果."""
    # 第一步：校验图像输入
    check_source_larger_than_search(im_source, im_search)

    # 第二步：计算模板匹配的结果矩阵res
    res = _get_template_result_matrix(im_source, im_search)

    # 第三步：依次获取匹配结果
    result = []
    h, w = im_search.shape[:2]

    while True:
        # 本次循环中,取出当前结果矩阵中的最优值
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # 求取可信度:
        confidence = _get_confidence_from_matrix(im_source, im_search, max_loc, max_val, w, h, rgb)

        if confidence < threshold or len(result) > max_count:
            break

        # 求取识别位置: 目标中心 + 目标区域:
        middle_point, rectangle = _get_target_rectangle(max_loc, w, h)
        one_good_match = generate_result(middle_point, rectangle, confidence)

        result.append(one_good_match)

        # 屏蔽已经取出的最优结果,进入下轮循环继续寻找:
        # cv2.floodFill(res, None, max_loc, (-1000,), max(max_val, 0), flags=cv2.FLOODFILL_FIXED_RANGE)
        cv2.rectangle(res, (int(max_loc[0] - w / 2), int(max_loc[1] - h / 2)), (int(max_loc[0] + w / 2), int(max_loc[1] + h / 2)), (0, 0, 0), -1)

    return result if result else None


def _get_confidence_from_matrix(im_source, im_search, max_loc, max_val, w, h, rgb):
    """根据结果矩阵求出confidence."""
    # 求取可信度:
    if rgb:
        # 如果有颜色校验,对目标区域进行BGR三通道校验:
        img_crop = im_source[max_loc[1]:max_loc[1] + h, max_loc[0]: max_loc[0] + w]
        confidence = cal_rgb_confidence(img_crop, im_search)
    else:
        confidence = max_val

    return confidence


def _get_template_result_matrix(im_source, im_search):
    """求取模板匹配的结果矩阵."""
    # 灰度识别: cv2.matchTemplate( )只能处理灰度图片参数
    s_gray, i_gray = img_mat_rgb_2_gray(im_search), img_mat_rgb_2_gray(im_source)
    return cv2.matchTemplate(i_gray, s_gray, cv2.TM_CCOEFF_NORMED)


def _get_target_rectangle(left_top_pos, w, h):
    """根据左上角点和宽高求出目标区域."""
    x_min, y_min = left_top_pos
    # 中心位置的坐标:
    x_middle, y_middle = int(x_min + w / 2), int(y_min + h / 2)
    # 左下(min,max)->右下(max,max)->右上(max,min)
    left_bottom_pos, right_bottom_pos = (x_min, y_min + h), (x_min + w, y_min + h)
    right_top_pos = (x_min + w, y_min)
    # 点击位置:
    middle_point = (x_middle, y_middle)
    # 识别目标区域: 点序:左上->左下->右下->右上, 左上(min,min)右下(max,max)
    rectangle = (left_top_pos, left_bottom_pos, right_bottom_pos, right_top_pos)

    return middle_point, rectangle
