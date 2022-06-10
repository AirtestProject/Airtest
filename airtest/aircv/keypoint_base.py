#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Detect keypoints with KAZE."""

import cv2
import time
import numpy as np
from distutils.version import LooseVersion

from airtest.utils.logger import get_logger

from .error import *  # noqa
from .utils import (generate_result, check_image_valid, print_run_time, get_keypoint_from_matches, rectangle_transform,
                    keypoint_distance, get_middle_point)
from .cal_confidence import cal_ccoeff_confidence, cal_rgb_confidence
LOGGING = get_logger(__name__)
CVRANSAC = (cv2.RANSAC, 5.0)
if LooseVersion(cv2.__version__) > LooseVersion('4.5.0'):
    CVRANSAC = (cv2.USAC_MAGSAC, 4.0, None, 2000, 0.99)


class KeypointMatching(object):
    """基于特征点的识别基类: KAZE."""

    # 日志中的方法名
    METHOD_NAME = "KAZE"
    # 参数: FILTER_RATIO为SIFT优秀特征点过滤比例值(0-1范围，建议值0.4-0.6)
    FILTER_RATIO = 0.59
    # 参数: SIFT识别时只找出一对相似特征点时的置信度(confidence)
    ONE_POINT_CONFI = 0.5

    def __init__(self, im_search, im_source, threshold=0.8, rgb=True):
        super(KeypointMatching, self).__init__()
        self.im_source = im_source
        self.im_search = im_search
        self.threshold = threshold
        self.rgb = rgb

    def mask_kaze(self):
        """基于kaze查找多个目标区域的方法."""
        # 求出特征点后，self.im_source中获得match的那些点进行聚类
        raise NotImplementedError

    @print_run_time
    def find_all_results(self, max_count=10, max_iter_counts=20, distance_threshold=150):
        if not check_image_valid(self.im_source, self.im_search):
            return None
        result = []

        self.init_detector()

        kp_sch, des_sch = self.get_keypoints_and_descriptors(self.im_search)
        kp_src, des_src = self.get_keypoints_and_descriptors(self.im_source)

        kp_src, kp_sch = list(kp_src), list(kp_sch)

        match_knn_count = max_count == 1 and 2 or max_count + 2

        matches = np.array(self.match_keypoints(des_sch, des_src, match_knn_count))
        kp_sch_point = np.array([(kp.pt[0], kp.pt[1], kp.angle) for kp in kp_sch])
        kp_src_matches_point = np.array([[(*kp_src[dMatch.trainIdx].pt, kp_src[dMatch.trainIdx].angle)
                                          if dMatch else np.nan for dMatch in match] for match in matches])
        _max_iter_counts = 0
        while True:
            if (np.count_nonzero(~np.isnan(kp_src_matches_point)) == 0) or \
                    (len(result) == max_count) or (_max_iter_counts >= max_iter_counts):
                break
            _max_iter_counts += 1

            filtered_good_point, angle, first_point = self.filter_good_point(matches=matches, kp_src=kp_src,
                                                                             kp_sch=kp_sch,
                                                                             kp_sch_point=kp_sch_point,
                                                                             kp_src_matches_point=kp_src_matches_point)
            if first_point.distance > distance_threshold:
                break
            pypts, w_h_range, confidence = None, None, 0

            try:
                pypts, w_h_range, confidence = self.extract_good_points(kp_src=kp_src, kp_sch=kp_sch,
                                                                        good=filtered_good_point, angle=angle)
            except PerspectiveTransformError:
                pass
            finally:
                if w_h_range and confidence >= self.threshold:
                    # 移除改范围内的所有特征点 ??有可能因为透视变换的原因，删除了多余的特征点
                    for index, match in enumerate(kp_src_matches_point):
                        x, y = match[:, 0], match[:, 1]
                        flag = np.argwhere((x < w_h_range[1]) & (x > w_h_range[0]) &
                                           (y < w_h_range[3]) & (y > w_h_range[2]))
                        for _index in flag:
                            kp_src_matches_point[index, _index, :] = np.nan
                            matches[index, _index] = np.nan
                    middle_point = get_middle_point(w_h_range)
                    result.append(generate_result(middle_point, pypts, confidence))
                else:
                    for match in filtered_good_point:
                        flags = np.argwhere(matches[match.queryIdx, :] == match)
                        for _index in flags:
                            kp_src_matches_point[match.queryIdx, _index, :] = np.nan
                            matches[match.queryIdx, _index] = np.nan

        return result

    def find_best_result(self, *args, **kwargs):
        ret = self.find_all_results(max_count=1, *args, **kwargs)

        if ret:
            best_match = ret[0]
            LOGGING.debug("[%s] threshold=%s, result=%s" % (self.METHOD_NAME, self.threshold, best_match))
            return best_match
        return None

    @staticmethod
    def filter_good_point(matches, kp_src, kp_sch, kp_sch_point, kp_src_matches_point):
        """ 筛选最佳点 """
        # 假设第一个点,及distance最小的点,为基准点
        sort_list = [sorted(match, key=lambda x: x is np.nan and float('inf') or x.distance)[0]
                     for match in matches]
        sort_list = [v for v in sort_list if v is not np.nan]

        first_good_point: cv2.DMatch = sorted(sort_list, key=lambda x: x.distance)[0]
        first_good_point_train: cv2.KeyPoint = kp_src[first_good_point.trainIdx]
        first_good_point_query: cv2.KeyPoint = kp_sch[first_good_point.queryIdx]
        first_good_point_angle = first_good_point_train.angle - first_good_point_query.angle

        def get_points_origin_angle(point_x, point_y, offset):
            points_origin_angle = np.arctan2(
                (point_y - offset.pt[1]),
                (point_x - offset.pt[0])
            ) * 180 / np.pi

            points_origin_angle = np.where(
                points_origin_angle == 0,
                points_origin_angle, points_origin_angle - offset.angle
            )
            points_origin_angle = np.where(
                points_origin_angle >= 0,
                points_origin_angle, points_origin_angle + 360
            )
            return points_origin_angle

        # 计算模板图像上,该点与其他特征点的旋转角
        first_good_point_sch_origin_angle = get_points_origin_angle(kp_sch_point[:, 0], kp_sch_point[:, 1],
                                                                    first_good_point_query)

        # 计算目标图像中,该点与其他特征点的夹角
        kp_sch_rotate_angle = kp_sch_point[:, 2] + first_good_point_angle
        kp_sch_rotate_angle = np.where(kp_sch_rotate_angle >= 360, kp_sch_rotate_angle - 360, kp_sch_rotate_angle)
        kp_sch_rotate_angle = kp_sch_rotate_angle.reshape(kp_sch_rotate_angle.shape + (1,))

        kp_src_angle = kp_src_matches_point[:, :, 2]
        good_point = np.array([matches[index][array[0]] for index, array in
                               enumerate(np.argsort(np.abs(kp_src_angle - kp_sch_rotate_angle)))])

        # 计算各点以first_good_point为原点的旋转角
        good_point_nan = (np.nan, np.nan)
        good_point_pt = np.array([good_point_nan if dMatch is np.nan else (*kp_src[dMatch.trainIdx].pt, )
                                 for dMatch in good_point])
        good_point_origin_angle = get_points_origin_angle(good_point_pt[:, 0], good_point_pt[:, 1],
                                                          first_good_point_train)
        threshold = round(5 / 360, 2) * 100
        point_bool = (np.abs(good_point_origin_angle - first_good_point_sch_origin_angle) / 360) * 100 < threshold
        _, index = np.unique(good_point_pt[point_bool], return_index=True, axis=0)
        good = good_point[point_bool]
        good = good[index]
        return good, int(first_good_point_angle), first_good_point

    def extract_good_points(self, kp_src, kp_sch, good, angle):
        """
        根据匹配点(good)数量,提取识别区域

        Args:
            kp_src: 关键点集
            kp_sch: 关键点集
            good: 描述符集
            angle: 旋转角度

        Returns:
            范围,和置信度
        """
        len_good = len(good)
        confidence, rect, target_img = 0, None, None

        if len_good == 0:
            pass
        if len_good < 4:
            target_img, pypts, w_h_range = self._handle_less_four_good_point(kp_sch=kp_sch, kp_src=kp_src, good=good,
                                                                             angle=angle)
        else:  # len > 4
            target_img, pypts, w_h_range = self._handle_many_good_points(kp_sch=kp_sch, kp_src=kp_src, good=good)

        if target_img is not None and target_img.any():
            confidence = self._cal_confidence(target_img)

        return pypts, w_h_range, confidence

    def _handle_less_four_good_point(self, kp_src, kp_sch, good, angle):
        sch_point = get_keypoint_from_matches(kp=kp_sch, matches=good, mode='query')
        src_point = get_keypoint_from_matches(kp=kp_src, matches=good, mode='train')

        scale = 0
        if len(good) == 1:
            scale = src_point[0].size / sch_point[0].size
        elif len(good) == 2:
            sch_distance = keypoint_distance(sch_point[0], sch_point[1])
            src_distance = keypoint_distance(src_point[0], src_point[1])
            try:
                scale = src_distance / sch_distance  # 计算缩放大小
            except ZeroDivisionError:
                if src_distance == sch_distance:
                    scale = 1
                else:
                    return None, None, None
        elif len(good) == 3:
            def _area(point_list):
                p1_2 = keypoint_distance(point_list[0], point_list[1])
                p1_3 = keypoint_distance(point_list[0], point_list[2])
                p2_3 = keypoint_distance(point_list[1], point_list[2])

                s = (p1_2 + p1_3 + p2_3) / 2
                area = (s * (s - p1_2) * (s - p1_3) * (s - p2_3)) ** 0.5
                return area

            sch_area = _area(sch_point)
            src_area = _area(src_point)

            try:
                scale = src_area / sch_area  # 计算缩放大小
            except ZeroDivisionError:
                if sch_area == src_area:
                    scale = 1
                else:
                    return None, None, None

        h, w = self.im_search.shape[:-1]
        _h, _w = h * scale, w * scale
        src = np.float32(rectangle_transform(point=sch_point[0].pt, size=(h, w), mapping_point=src_point[0].pt,
                                             mapping_size=(_h, _w), angle=angle))
        dst = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        output = self._perspective_transform(src=src, dst=dst)
        pypts, w_h_range = self._get_perspective_area_rect(src=src)
        return output, pypts, w_h_range

    def _handle_many_good_points(self, kp_src, kp_sch, good):
        """
        特征点匹配数量>=4时,使用单矩阵映射,获取识别的目标图片

        Args:
            kp_sch: 关键点集
            kp_src: 关键点集
            good: 描述符集

        Returns:
            透视变换后的图片
        """

        sch_pts, img_pts = np.float32([kp_sch[m.queryIdx].pt for m in good]).reshape(
            -1, 1, 2), np.float32([kp_src[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        # M是转化矩阵
        M, mask = self._find_homography(sch_pts, img_pts)
        # 计算四个角矩阵变换后的坐标，也就是在大图中的目标区域的顶点坐标:
        h, w = self.im_search.shape[:-1]
        h_s, w_s = self.im_source.shape[:-1]
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        try:
            dst: np.ndarray = cv2.perspectiveTransform(pts, M)
            # img = im_source.clone().data
            # img2 = cv2.polylines(img, [np.int32(dst)], True, 255, 3, cv2.LINE_AA)
            # Image(img).imshow('dst')
            pypts = [tuple(npt[0]) for npt in dst.tolist()]
            src = np.array([pypts[0], pypts[3], pypts[1], pypts[2]], dtype=np.float32)
            dst = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            output = self._perspective_transform(src=src, dst=dst)
        except cv2.error as err:
            raise PerspectiveTransformError(err)

        # img = im_source.clone()
        # cv2.polylines(img, [np.int32(dst)], True, 255, 3, cv2.LINE_AA)
        # Image(img).imshow()
        # cv2.waitKey(0)

        pypts, w_h_range = self._get_perspective_area_rect(src=src)
        return output, pypts, w_h_range

    def _get_perspective_area_rect(self, src):
        """
        根据矩形四个顶点坐标,获取在原图中的最大外接矩形

        Args:
            src: 目标图像中相应四边形顶点的坐标

        Returns:
            最大外接矩形
        """
        h, w = self.im_source.shape[:-1]

        x = [int(i[0]) for i in src]
        y = [int(i[1]) for i in src]
        x_min, x_max = min(x), max(x)
        y_min, y_max = min(y), max(y)

        def cal_rect_pts(dst):
            return [tuple(npt[0]) for npt in dst.astype(int).tolist()]

        # 挑选出目标矩形区域可能会有越界情况，越界时直接将其置为边界：
        # 超出左边界取0，超出右边界取w_s-1，超出下边界取0，超出上边界取h_s-1
        # 当x_min小于0时，取0。  x_max小于0时，取0。
        x_min, x_max = int(max(x_min, 0)), int(max(x_max, 0))
        # 当x_min大于w_s时，取值w_s-1。  x_max大于w_s-1时，取w_s-1。
        x_min, x_max = int(min(x_min, w - 1)), int(min(x_max, w - 1))
        # 当y_min小于0时，取0。  y_max小于0时，取0。
        y_min, y_max = int(max(y_min, 0)), int(max(y_max, 0))
        # 当y_min大于h_s时，取值h_s-1。  y_max大于h_s-1时，取h_s-1。
        y_min, y_max = int(min(y_min, h - 1)), int(min(y_max, h - 1))
        pts = np.float32([[x_min, y_min], [x_min, y_max], [
                         x_max, y_max], [x_max, y_min]]).reshape(-1, 1, 2)
        pypts = cal_rect_pts(pts)
        return pypts, [x_min, x_max, y_min, y_max, w, h]

    def _perspective_transform(self, src, dst, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0):
        """
        根据四对对应点计算透视变换, 并裁剪相应图片

        Args:
            src: 目标图像中相应四边形顶点的坐标 (左上,右上,左下,右下)
            dst: 源图像中四边形顶点的坐标 (左上,右上,左下,右下)

        Returns:
            透视变化后的图片
        """
        h, w = self.im_search.shape[:-1]
        matrix = cv2.getPerspectiveTransform(src=src, dst=dst)
        # warpPerspective https://github.com/opencv/opencv/issues/11784
        output = cv2.warpPerspective(self.im_source, matrix, (w, h), flags=flags, borderMode=borderMode,
                                     borderValue=borderValue)
        return output

    def show_match_image(self):
        """Show how the keypoints matches."""
        from random import random
        h_sch, w_sch = self.im_search.shape[:2]
        h_src, w_src = self.im_source.shape[:2]

        # first you have to do the matching
        self.find_best_result()
        # then initialize the result image:
        matching_info_img = np.zeros([max(h_sch, h_src), w_sch + w_src, 3], np.uint8)
        matching_info_img[:h_sch, :w_sch, :] = self.im_search
        matching_info_img[:h_src, w_sch:, :] = self.im_source
        # render the match image at last:
        for m in self.good:
            color = tuple([int(random() * 255) for _ in range(3)])
            cv2.line(matching_info_img, (int(self.kp_sch[m.queryIdx].pt[0]), int(self.kp_sch[m.queryIdx].pt[1])), (int(self.kp_src[m.trainIdx].pt[0] + w_sch), int(self.kp_src[m.trainIdx].pt[1])), color)

        return matching_info_img

    def _cal_confidence(self, resize_img):
        """计算confidence."""
        if self.rgb:
            confidence = cal_rgb_confidence(resize_img, self.im_search)
        else:
            confidence = cal_ccoeff_confidence(resize_img, self.im_search)
        # confidence修正
        confidence = (1 + confidence) / 2
        return confidence

    def init_detector(self):
        """Init keypoint detector object."""
        self.detector = cv2.KAZE_create()
        # create BFMatcher object:
        self.matcher = cv2.BFMatcher(cv2.NORM_L1)  # cv2.NORM_L1 cv2.NORM_L2 cv2.NORM_HAMMING(not useable)

    def get_keypoints_and_descriptors(self, image):
        """获取图像特征点和描述符."""
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, code=cv2.COLOR_BGR2GRAY)

        keypoints, descriptors = self.detector.detectAndCompute(image, None)
        if len(keypoints) < 2:
            raise NoMatchPointError("Not enough feature points in input images !")
        return keypoints, descriptors

    def match_keypoints(self, des_sch, des_src, k=2):
        """Match descriptors (特征值匹配)."""
        # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
        return self.matcher.knnMatch(des_sch, des_src, k=k)

    @staticmethod
    def _find_homography(sch_pts, src_pts):
        """多组特征点对时，求取单向性矩阵."""
        try:
            M, mask = cv2.findHomography(sch_pts, src_pts, *CVRANSAC)
        except cv2.error:
            # import traceback
            # traceback.print_exc()
            raise HomographyError("OpenCV error in _find_homography()...")
        else:
            if mask is None:
                raise HomographyError("In _find_homography(), find no transfomation matrix...")
            else:
                return M, mask

    def _target_error_check(self, w_h_range):
        """校验识别结果区域是否符合常理."""
        x_min, x_max, y_min, y_max, w, h = w_h_range
        tar_width, tar_height = x_max - x_min, y_max - y_min
        # 如果src_img中的矩形识别区域的宽和高的像素数＜5，则判定识别失效。认为提取区域待不可能小于5个像素。(截图一般不可能小于5像素)
        if tar_width < 5 or tar_height < 5:
            raise MatchResultCheckError("In src_image, Taget area: width or height < 5 pixel.")
        # 如果矩形识别区域的宽和高，与sch_img的宽高差距超过5倍(屏幕像素差不可能有5倍)，认定为识别错误。
        if tar_width < 0.2 * w or tar_width > 5 * w or tar_height < 0.2 * h or tar_height > 5 * h:
            raise MatchResultCheckError("Target area is 5 times bigger or 0.2 times smaller than sch_img.")