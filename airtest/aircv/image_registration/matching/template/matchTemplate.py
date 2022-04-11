#! usr/bin/python
# -*- coding:utf-8 -*-
""" opencv matchTemplate"""
import warnings
import cv2
import numpy as np
from baseImage import Image, Rect
from baseImage.constant import Place

from airtest.aircv.error import MatchResultError, NoModuleError
from airtest.aircv.image_registration.utils import generate_result
from airtest.aircv.utils import print_run_time
from typing import Union


from airtest.utils.logger import get_logger
LOGGING = get_logger(__name__)


class MatchTemplate(object):
    METHOD_NAME = 'tpl'
    Dtype = np.uint8
    Place = (Place.Mat, Place.Ndarray)

    def __init__(self, threshold: Union[int, float] = 0.8, rgb: bool = True):
        """
        初始化

        Args:
            threshold: 识别阈值(0~1)
            rgb: 是否使用rgb通道进行校验
        """
        assert 0 <= threshold <= 1, 'threshold 取值在0到1直接'

        self.threshold = threshold
        self.rgb = rgb
        self.matcher = cv2.matchTemplate

    @print_run_time
    def find_best_result(self, im_source, im_search, threshold=None, rgb=None):
        """
        模板匹配, 返回匹配度最高且大于阈值的范围

        Args:
            im_source: 待匹配图像
            im_search: 图片模板
            threshold: 识别阈值(0~1)
            rgb: 是否使用rgb通道进行校验

        Returns:
            generate_result
        """
        threshold = threshold or self.threshold
        rgb = rgb or self.rgb

        im_source, im_search = self.input_image_check(im_source, im_search)
        if im_source.channels == 1:
            rgb = False

        result = self._get_template_result_matrix(im_source=im_source, im_search=im_search)
        # 找到最佳匹配项
        min_val, max_val, min_loc, max_loc = self.minMaxLoc(result.data)
        h, w = im_search.size
        # 求可信度
        crop_rect = Rect(max_loc[0], max_loc[1], w, h)

        confidence = self.cal_confidence(im_source, im_search, crop_rect, max_val, rgb)
        # 如果可信度小于threshold,则返回None
        if confidence < (threshold or self.threshold):
            return None
        x, y = max_loc
        rect = Rect(x=x, y=y, width=w, height=h)
        best_match = generate_result(rect, confidence)
        LOGGING.debug("[%s] threshold=%s, result=%s" % (self.METHOD_NAME, self.threshold, best_match))
        return best_match

    @print_run_time
    def find_all_results(self, im_source: Image, im_search: Image, threshold=None, rgb=None, max_count=10):
        """
        模板匹配, 返回匹配度大于阈值的范围, 且最大数量不超过max_count

        Args:
            im_source: 待匹配图像
            im_search: 图片模板
            threshold:: 识别阈值(0~1)
            rgb: 是否使用rgb通道进行校验
            max_count: 最多匹配数量

        Returns:

        """
        threshold = threshold or self.threshold
        rgb = rgb or self.rgb

        im_source, im_search = self.input_image_check(im_source, im_search)
        if im_source.channels == 1:
            rgb = False

        result = self._get_template_result_matrix(im_source=im_source, im_search=im_search)
        results = []
        # 找到最佳匹配项
        h, w = im_search.size
        while True:
            min_val, max_val, min_loc, max_loc = self.minMaxLoc(result.data)
            img_crop = im_source.crop(Rect(max_loc[0], max_loc[1], w, h))
            confidence = self._get_confidence_from_matrix(img_crop, im_search, max_val=max_val, rgb=rgb)
            x, y = max_loc
            rect = Rect(x, y, w, h)

            if (confidence < (threshold or self.threshold)) or len(results) >= max_count:
                break
            results.append(generate_result(rect, confidence))
            result.rectangle(rect=Rect(int(max_loc[0] - w / 2), int(max_loc[1] - h / 2), w, h), color=(0, 0, 0), thickness=-1)

        return results if results else None

    def _get_template_result_matrix(self, im_source: Image, im_search: Image) -> Image:
        """求取模板匹配的结果矩阵."""
        if im_source.channels == 3:
            i_gray = im_source.cvtColor(cv2.COLOR_BGR2GRAY).data
            s_gray = im_search.cvtColor(cv2.COLOR_BGR2GRAY).data
        else:
            i_gray = im_source.data
            s_gray = im_search.data

        result = self.match(i_gray, s_gray)
        result = Image(data=result, dtype=np.float32, clone=False, place=3)
        return result

    def input_image_check(self, im_source, im_search):
        im_source = self._image_check(im_source)
        im_search = self._image_check(im_search)

        assert im_source.place == im_search.place, '输入图片类型必须相同, source={}, search={}'.format(im_source.place, im_search.place)
        assert im_source.dtype == im_search.dtype, '输入图片数据类型必须相同, source={}, search={}'.format(im_source.dtype, im_search.dtype)
        assert im_source.channels == im_search.channels, '输入图片通道必须相同, source={}, search={}'.format(im_source.channels, im_search.channels)

        if im_source.place == Place.UMat:
            warnings.warn('Umat has error,will clone new image with np.ndarray '
                          '(https://github.com/opencv/opencv/issues/21788)')
            im_source = Image(im_source, place=Place.Mat, dtype=im_source.dtype)
            im_search = Image(im_search, place=Place.Mat, dtype=im_search.dtype)

        return im_source, im_search

    def _image_check(self, data: Union[str, bytes, np.ndarray, cv2.cuda.GpuMat, cv2.Mat, cv2.UMat, Image]):
        if not isinstance(data, Image):
            data = Image(data, dtype=self.Dtype)

        if data.place not in self.Place:
            raise TypeError('Image类型必须为(Place.Mat, Place.UMat, Place.Ndarray)')
        return data

    @staticmethod
    def minMaxLoc(result: np.ndarray):
        return cv2.minMaxLoc(result)

    def match(self, img1, img2):
        return self.matcher(img1, img2, cv2.TM_CCOEFF_NORMED)

    def cal_confidence(self, im_source: Image, im_search: Image, crop_rect: Rect, max_val: int, rgb: bool) -> float:
        """
        将截图和识别结果缩放到大小一致,并计算可信度

        Args:
            im_source: 待匹配图像
            im_search: 图片模板
            crop_rect: 需要在im_source截取的区域
            max_val: matchTemplate得到的最大值
            rgb: 是否使用rgb通道进行校验

        Returns:
            float: 可信度(0~1)
        """
        try:
            target_img = im_source.crop(crop_rect)
        except OverflowError:
            raise MatchResultError(f"Target area({crop_rect}) out of screen{im_source.size}")
        confidence = self._get_confidence_from_matrix(target_img, im_search, max_val, rgb)
        return confidence

    def cal_rgb_confidence(self, im_source: Image, im_search: Image) -> float:
        """
        计算两张图片图片rgb三通道的置信度

        Args:
            im_source: 待匹配图像
            im_search: 图片模板

        Returns:
            float: 最小置信度
        """
        im_search = im_search.copyMakeBorder(10, 10, 10, 10, cv2.BORDER_REPLICATE)
        img_src_hsv = im_source.cvtColor(cv2.COLOR_BGR2HSV)
        img_sch_hsv = im_search.cvtColor(cv2.COLOR_BGR2HSV)

        src_split = img_src_hsv.split()
        sch_split = img_sch_hsv.split()

        # 计算BGR三通道的confidence，存入bgr_confidence:
        bgr_confidence = [0, 0, 0]
        for i in range(3):
            res_temp = self.match(sch_split[i], src_split[i])
            min_val, max_val, min_loc, max_loc = self.minMaxLoc(res_temp)
            bgr_confidence[i] = max_val

        return min(bgr_confidence)

    def cal_ccoeff_confidence(self, im_source: Image, im_search: Image):
        if im_source.channels == 3:
            img_src_gray = im_source.cvtColor(cv2.COLOR_BGR2GRAY).data
        else:
            img_src_gray = im_source.data

        if im_search.channels == 3:
            img_sch_gray = im_search.cvtColor(cv2.COLOR_BGR2GRAY).data
        else:
            img_sch_gray = im_search.data

        res_temp = self.match(img_sch_gray, img_src_gray)
        min_val, max_val, min_loc, max_loc = self.minMaxLoc(res_temp)
        return max_val

    def _get_confidence_from_matrix(self, img_crop, im_search, max_val, rgb):
        """根据结果矩阵求出confidence."""
        # 求取可信度:
        if rgb:
            # 如果有颜色校验,对目标区域进行BGR三通道校验:
            confidence = self.cal_rgb_confidence(img_crop, im_search)
        else:
            confidence = max_val
        return confidence


class CudaMatchTemplae(MatchTemplate):
    METHOD_NAME = 'tpl'
    Dtype = np.uint8
    Place = Place.GpuMat

    def __init__(self, threshold: Union[int, float] = 0.8, rgb: bool = True):
        super(CudaMatchTemplae, self).__init__(threshold=threshold, rgb=rgb)
        try:
            self.matcher = cv2.cuda.createTemplateMatching(cv2.CV_8U, cv2.TM_CCOEFF_NORMED)
        except AttributeError:
            raise NoModuleError('create CUDA TemplateMatching Error')

    @staticmethod
    def minMaxLoc(result: cv2.cuda.GpuMat):
        return cv2.cuda.minMaxLoc(result)

    def match(self, img1, img2):
        return self.matcher.match(img1, img2)
