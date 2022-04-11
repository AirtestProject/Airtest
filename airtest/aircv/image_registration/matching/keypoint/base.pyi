#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
import numpy as np
from typing import Union, Optional, Type, Any, Tuple, List
from baseImage.constant import Place
from baseImage import Image, Rect


from airtest.aircv import MatchTemplate


image_type = Union[str, bytes, np.ndarray, cv2.cuda.GpuMat, cv2.Mat, cv2.UMat, Image]
keypoint_type = Tuple[cv2.KeyPoint, ...]
matches_type = Tuple[Tuple[cv2.DMatch, ...], ...]
good_match_type = List[cv2.DMatch]

class BaseKeypoint(object):
    FILTER_RATIO: int = 0.59
    METHOD_NAME: str
    Dtype: Union[Type[np.uint8], Type[np.int8], Type[np.uint16], Type[np.int16], Type[np.int32], Type[np.float32], Type[np.float64]]
    Place: Place
    template: Union[MatchTemplate, CudaMatchTemplae]

    def __init__(self, threshold: Union[int, float] = 0.8, rgb: bool = True, **kwargs):
        self.detector = cv2.DescriptorMatcher
        self.matcher = cv2.Feature2D
        self.threshold: Union[int, float] = 0.8
        self.rgb: bool = True
        ...

    def create_matcher(self, **kwargs) -> cv2.DescriptorMatcher: ...

    def create_detector(self, **kwargs) -> cv2.Feature2D: ...

    def find_best_result(self, im_source: image_type, im_search: image_type, threshold: Union[int, float] = None, rgb: bool = None) -> Optional[Rect]: ...

    def find_all_result(self, im_source: image_type, im_search: image_type, threshold: Union[int, float] = None, rgb: bool = None, max_count: int = 10, max_iter_counts: int = 20, distance_threshold: int = 150): ...

    def get_keypoint_and_descriptor(self, image: Image) -> Tuple[keypoint_type, np.ndarray]: ...

    def filter_good_point(self, good: good_match_type, kp_src: keypoint_type, kp_sch: keypoint_type) -> Tuple[good_match_type, float, cv2.DMatch]: ...

    def get_rect_from_good_matches(self, im_source: Image, im_search: Image, kp_src: keypoint_type,
                                   des_src: np.ndarray, kp_sch:keypoint_type, des_sch: np.ndarray) -> \
            Tuple[Optional[Rect], matches_type, good_match_type]: ...

    def match_keypoint(self, des_sch: np.ndarray, des_src: np.ndarray, k: int = 2) -> matches_type: ...

    def get_good_in_matches(self, matches: matches_type) -> good_match_type: ...

    def extract_good_points(self, im_source: Image, im_search: Image, kp_src: keypoint_type, kp_sch: keypoint_type, good: good_match_type, angle: float, rgb: bool) -> Union[Optional[Rect], Union[None, int, float]]: ...

    def _get_warpPerspective_image(self, im_source: Image, im_search: Image, kp_src: keypoint_type, kp_sch: keypoint_type, good: good_match_type) -> Tuple[Image, Rect]: ...

    def _target_image_crop(self, img: Image, rect: Rect) -> Image: ...

    def _cal_confidence(self, im_source: Image, im_search: Image, rgb: bool) -> Union[int, float]: ...

    def input_image_check(self, im_source: image_type, im_search: image_type) -> Tuple[Image, Image]: ...

    def _image_check(self, data: Union[str, bytes, np.ndarray, cv2.cuda.GpuMat, cv2.Mat, cv2.UMat, Image]) -> Image: ...

    @staticmethod
    def _find_homography(sch_pts: np.ndarray, src_pts: np.ndarray) -> Optional[Tuple[np.ndarray, np.ndarray]]: ...