#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
import numpy as np
from typing import Union, Optional, Type, Any, Tuple, List
from baseImage.constant import Place
from baseImage import Image, Rect

from image_registration.matching import MatchTemplate, CudaMatchTemplae
from image_registration.matching.keypoint.base import BaseKeypoint


image_type = Union[str, bytes, np.ndarray, cv2.cuda.GpuMat, cv2.Mat, cv2.UMat, Image]
keypoint_type = Tuple[cv2.KeyPoint, ...]
matches_type = Tuple[Tuple[cv2.DMatch, ...], ...]
good_match_type = List[cv2.DMatch]


class ORB(BaseKeypoint):
    def __init__(self, threshold: Union[int, float] = 0.8, rgb: bool = True,
                 nfeatures: int = 50000 ,scaleFactor: Union[int, float] = 1.2, nlevels: int = 8,
                 edgeThreshold: int = 31, firstLevel: int = 0, WTA_K: int = 2,
                 scoreType: int = cv2.ORB_HARRIS_SCORE, patchSize: int = 31, fastThreshold: int = 20):
        self.descriptor = cv2.xfeatures2d.BEBLID
        ...

    @staticmethod
    def create_descriptor() -> cv2.xfeatures2d.BEBLID: ...

