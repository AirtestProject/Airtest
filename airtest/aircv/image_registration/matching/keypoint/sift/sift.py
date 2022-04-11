#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
import numpy as np
from baseImage.constant import Place

from airtest.aircv.image_registration.matching.keypoint.base import BaseKeypoint
from airtest.aircv.error import NoModuleError


class SIFT(BaseKeypoint):
    FLANN_INDEX_KDTREE = 0
    METHOD_NAME = 'SIFT'
    Dtype = np.uint8
    Place = (Place.Mat, Place.UMat, Place.Ndarray)

    def create_matcher(self, **kwargs) -> cv2.DescriptorMatcher:
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

    def create_detector(self, **kwargs) -> cv2.SIFT:
        nfeatures = kwargs.get('nfeatures', 0)
        nOctaveLayers = kwargs.get('nOctaveLayers', 3)
        contrastThreshold = kwargs.get('contrastThreshold', 0.04)
        edgeThreshold = kwargs.get('edgeThreshold', 10)
        sigma = kwargs.get('sigma', 1.6)

        try:
            detector = cv2.SIFT_create(nfeatures=nfeatures, nOctaveLayers=nOctaveLayers, contrastThreshold=contrastThreshold,
                                       edgeThreshold=edgeThreshold, sigma=sigma)
        except cv2.error as err:
            raise NoModuleError(err)

        return detector
