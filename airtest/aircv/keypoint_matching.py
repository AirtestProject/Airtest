#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Detect keypoints with KAZE/AKAZE/BRISK/ORB.
No need for opencv-contrib module.
"""

import cv2

from .keypoint_base import KeypointMatching


class KAZEMatching(KeypointMatching):
    """KAZE Matching."""

    pass


class BRISKMatching(KeypointMatching):
    """BRISK Matching."""

    METHOD_NAME = "BRISK"  # 日志中的方法名

    def init_detector(self):
        """Init keypoint detector object."""
        self.detector = cv2.BRISK_create()
        # create BFMatcher object:
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)  # cv2.NORM_L1 cv2.NORM_L2 cv2.NORM_HAMMING(not useable)


class AKAZEMatching(KeypointMatching):
    """AKAZE Matching."""

    METHOD_NAME = "AKAZE"  # 日志中的方法名

    def init_detector(self):
        """Init keypoint detector object."""
        self.detector = cv2.AKAZE_create()
        # create BFMatcher object:
        self.matcher = cv2.BFMatcher(cv2.NORM_L1)  # cv2.NORM_L1 cv2.NORM_L2 cv2.NORM_HAMMING(not useable)


class ORBMatching(KeypointMatching):
    """ORB Matching."""

    METHOD_NAME = "ORB"  # 日志中的方法名

    def init_detector(self):
        """Init keypoint detector object."""
        self.detector = cv2.ORB_create()
        # create BFMatcher object:
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)  # cv2.NORM_L1 cv2.NORM_L2 cv2.NORM_HAMMING(not useable)
