#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
import numpy as np
from baseImage.constant import Place

from .base import BaseKeypoint
from typing import Union


class Kaze(BaseKeypoint):
    FLANN_INDEX_KDTREE = 0
    METHOD_NAME = 'Kaze'
    Dtype = np.uint8
    Place = (Place.Mat, Place.UMat, Place.Ndarray)

    def __init__(self, threshold: Union[int, float] = 0.8, rgb: bool = True):
        """
        初始化

        Args:
            threshold: 识别阈值(0~1)
            rgb: 是否使用rgb通道进行校验
        """
        super(Kaze, self).__init__(threshold=threshold, rgb=rgb)

    def create_matcher(self) -> cv2.DescriptorMatcher:
        """
        创建特征点匹配器

        Returns:
            cv2.FlannBasedMatcher
        """
        index_params = {'algorithm': self.FLANN_INDEX_KDTREE, 'tree': 5}
        # 指定递归遍历的次数. 值越高结果越准确，但是消耗的时间也越多
        search_params = {'checks': 50}
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
        return matcher

    def create_detector(self) -> cv2.KAZE:
        """
        创建Kaze特征点提取器

        Returns:
            cv2.KAZE
        """
        detector = cv2.KAZE_create()
        return detector
