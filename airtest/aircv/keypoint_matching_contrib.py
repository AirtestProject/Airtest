#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Detect keypoints with BRIEF/SIFT/SURF.
Need opencv-contrib module.
"""

import cv2

from .error import *  # noqa
from .keypoint_base import KeypointMatching


def check_cv_version_is_new():
    """opencv版本是3.0或4.0以上, API接口与2.0的不同."""
    if cv2.__version__.startswith("3.") or cv2.__version__.startswith("4."):
        return True
    else:
        return False


class BRIEFMatching(KeypointMatching):
    """FastFeature Matching."""

    METHOD_NAME = "BRIEF"  # 日志中的方法名

    def init_detector(self):
        """Init keypoint detector object."""
        # BRIEF is a feature descriptor, recommand CenSurE as a fast detector:
        if check_cv_version_is_new():
            # OpenCV3/4, star/brief is in contrib module, you need to compile it seperately.
            try:
                self.star_detector = cv2.xfeatures2d.StarDetector_create()
                self.brief_extractor = cv2.xfeatures2d.BriefDescriptorExtractor_create()
            except:
                import traceback
                traceback.print_exc()
                print("to use %s, you should build contrib with opencv3.0" % self.METHOD_NAME)
                raise NoModuleError("There is no %s module in your OpenCV environment !" % self.METHOD_NAME)
        else:
            # OpenCV2.x
            self.star_detector = cv2.FeatureDetector_create("STAR")
            self.brief_extractor = cv2.DescriptorExtractor_create("BRIEF")

        # create BFMatcher object:
        self.matcher = cv2.BFMatcher(cv2.NORM_L1)  # cv2.NORM_L1 cv2.NORM_L2 cv2.NORM_HAMMING(not useable)

    def get_keypoints_and_descriptors(self, image):
        """获取图像特征点和描述符."""
        # find the keypoints with STAR
        kp = self.star_detector.detect(image, None)
        # compute the descriptors with BRIEF
        keypoints, descriptors = self.brief_extractor.compute(image, kp)
        return keypoints, descriptors

    def match_keypoints(self, des_sch, des_src):
        """Match descriptors (特征值匹配)."""
        # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
        return self.matcher.knnMatch(des_sch, des_src, k=2)


class SIFTMatching(KeypointMatching):
    """SIFT Matching."""

    METHOD_NAME = "SIFT"  # 日志中的方法名

    # SIFT识别特征点匹配，参数设置:
    FLANN_INDEX_KDTREE = 0

    def init_detector(self):
        """Init keypoint detector object."""
        if check_cv_version_is_new():
            try:
                # opencv3 >= 3.4.12 or opencv4 >=4.5.0, sift is in main repository
                self.detector = cv2.SIFT_create(edgeThreshold=10)
            except AttributeError:
                try:
                    self.detector = cv2.xfeatures2d.SIFT_create(edgeThreshold=10)
                except:
                    raise NoModuleError(
                        "There is no %s module in your OpenCV environment, need contrib module!" % self.METHOD_NAME)
        else:
            # OpenCV2.x
            self.detector = cv2.SIFT(edgeThreshold=10)

        # # create FlnnMatcher object:
        self.matcher = cv2.FlannBasedMatcher({'algorithm': self.FLANN_INDEX_KDTREE, 'trees': 5}, dict(checks=50))

    def get_keypoints_and_descriptors(self, image):
        """获取图像特征点和描述符."""
        keypoints, descriptors = self.detector.detectAndCompute(image, None)
        return keypoints, descriptors

    def match_keypoints(self, des_sch, des_src):
        """Match descriptors (特征值匹配)."""
        # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
        return self.matcher.knnMatch(des_sch, des_src, k=2)


class SURFMatching(KeypointMatching):
    """SURF Matching."""

    METHOD_NAME = "SURF"  # 日志中的方法名

    # 是否检测方向不变性:0检测/1不检测
    UPRIGHT = 0
    # SURF算子的Hessian Threshold
    HESSIAN_THRESHOLD = 400
    # SURF识别特征点匹配方法设置:
    FLANN_INDEX_KDTREE = 0

    def init_detector(self):
        """Init keypoint detector object."""
        # BRIEF is a feature descriptor, recommand CenSurE as a fast detector:
        if check_cv_version_is_new():
            # OpenCV3/4, surf is in contrib module, you need to compile it seperately.
            try:
                self.detector = cv2.xfeatures2d.SURF_create(self.HESSIAN_THRESHOLD, upright=self.UPRIGHT)
            except:
                raise NoModuleError("There is no %s module in your OpenCV environment, need contribmodule!" % self.METHOD_NAME)
        else:
            # OpenCV2.x
            self.detector = cv2.SURF(self.HESSIAN_THRESHOLD, upright=self.UPRIGHT)

        # # create FlnnMatcher object:
        self.matcher = cv2.FlannBasedMatcher({'algorithm': self.FLANN_INDEX_KDTREE, 'trees': 5}, dict(checks=50))

    def get_keypoints_and_descriptors(self, image):
        """获取图像特征点和描述符."""
        keypoints, descriptors = self.detector.detectAndCompute(image, None)
        return keypoints, descriptors

    def match_keypoints(self, des_sch, des_src):
        """Match descriptors (特征值匹配)."""
        # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
        return self.matcher.knnMatch(des_sch, des_src, k=2)
