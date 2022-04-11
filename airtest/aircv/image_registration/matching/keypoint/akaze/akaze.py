#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
import numpy as np
from baseImage.constant import Place

from airtest.aircv.image_registration.matching.keypoint.base import BaseKeypoint


class AKAZE(BaseKeypoint):
    METHOD_NAME = 'AKAZE'
    Dtype = np.uint8
    Place = (Place.Mat, Place.UMat, Place.Ndarray)

    def create_matcher(self, **kwargs) -> cv2.DescriptorMatcher:
        """
        创建特征点匹配器

        Returns:
            cv2.FlannBasedMatcher
        """
        matcher = cv2.BFMatcher_create(cv2.NORM_L1)
        return matcher

    def create_detector(self, **kwargs) -> cv2.SIFT:
        descriptor_type = kwargs.get('descriptor_type', cv2.AKAZE_DESCRIPTOR_MLDB)
        descriptor_size = kwargs.get('descriptor_size', 0)
        descriptor_channels = kwargs.get('descriptor_channels', 3)
        threshold = kwargs.get('_threshold', 0.001)
        diffusivity = kwargs.get('diffusivity', cv2.KAZE_DIFF_PM_G2)
        nOctaveLayers = kwargs.get('nOctaveLayers', 4)
        nOctaves = kwargs.get('nOctaves', 4)

        detector = cv2.AKAZE_create(descriptor_type=descriptor_type, descriptor_size=descriptor_size,
                                    descriptor_channels=descriptor_channels, threshold=threshold,
                                    diffusivity=diffusivity, nOctaves=nOctaves, nOctaveLayers=nOctaveLayers,)
        return detector
