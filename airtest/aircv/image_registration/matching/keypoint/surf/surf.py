#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
import numpy as np
from baseImage.constant import Place

from airtest.aircv.image_registration.matching.keypoint.base import BaseKeypoint
from airtest.aircv.error import NoModuleError


class SURF(BaseKeypoint):
    FLANN_INDEX_KDTREE = 0
    METHOD_NAME = "SURF"
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
        hessianThreshold = kwargs.get('hessianThreshold', 400)
        nOctaves = kwargs.get('nOctaves', 4)
        nOctaveLayers = kwargs.get('nOctaveLayers', 3)
        extended = kwargs.get('extended', True)
        upright = kwargs.get('upright', False)

        try:
            detector = cv2.xfeatures2d.SURF_create(hessianThreshold=hessianThreshold, nOctaves=nOctaves, nOctaveLayers=nOctaveLayers,
                                                   extended=extended, upright=upright)
        except cv2.error as err:
            raise NoModuleError(err)

        return detector
