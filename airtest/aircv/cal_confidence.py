#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""These functions calculate the similarity of two images of the same size."""


import cv2
from .utils import img_mat_rgb_2_gray


def cal_ccoeff_confidence(im_source, im_search, threshold, rgb=False, sift=False):
    """求取两张图片的可信度，使用TM_CCOEFF_NORMED方法."""
    if rgb:
        # 三通道求取方法:
        confidence = cal_rgb_confidence(im_source, im_search, threshold, sift=sift)
    else:
        im_source, im_search = img_mat_rgb_2_gray(im_source), img_mat_rgb_2_gray(im_search)
        res = cv2.matchTemplate(im_source, im_search, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if sift is False:
            confidence = max_val
        else:
            confidence = (max_val + 1) / 2  # sift需要放水

    return confidence


def cal_rgb_confidence(img_src_rgb, img_sch_rgb, threshold, sift=False):
    """同大小彩图计算相似度."""
    # BGR三通道心理学权重:
    weight = (0.114, 0.587, 0.299)
    src_bgr, sch_bgr = cv2.split(img_src_rgb), cv2.split(img_sch_rgb)

    # 计算BGR三通道的confidence，存入bgr_confidence:
    bgr_confidence = [0, 0, 0]
    for i in range(3):
        res_temp = cv2.matchTemplate(src_bgr[i], sch_bgr[i], cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res_temp)
        if sift is False:
            bgr_confidence[i] = max_val
        else:
            bgr_confidence[i] = (max_val + 1) / 2  # sift需要放水

    # 只要任何一通道的可信度低于阈值,均视为识别失败,返回可信度为0:
    if min(bgr_confidence) < threshold:
        confidence = 0
    else:
        confidence = bgr_confidence[0] * weight[0] + bgr_confidence[1] * weight[1] + bgr_confidence[2] * weight[2]

    return confidence
