#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
import numpy as np
from baseImage import Image, Rect, Point

from airtest.aircv.image_registration.matching import MatchTemplate
from airtest.aircv.image_registration.utils import generate_result, get_keypoint_from_matches, keypoint_origin_angle
from airtest.aircv.error import NoEnoughPointsError, PerspectiveTransformError, HomographyError, MatchResultError
from airtest.aircv.utils import print_run_time

from airtest.utils.logger import get_logger
LOGGING = get_logger(__name__)


class BaseKeypoint(object):
    FILTER_RATIO = 1
    METHOD_NAME = None
    Dtype = None
    Place = None
    template = MatchTemplate()

    def __init__(self, threshold=0.8, rgb=True, **kwargs):
        """
        初始化

        Args:
            threshold: 识别阈值(0~1)
            rgb: 是否使用rgb通道进行校验
        """
        self.threshold = threshold
        self.rgb = rgb
        self.detector = self.create_detector(**kwargs)
        self.matcher = self.create_matcher(**kwargs)

    def create_matcher(self, **kwargs):
        raise NotImplementedError

    def create_detector(self, **kwargs):
        raise NotImplementedError

    def _find_best_result(self, im_source, im_search, threshold=None, rgb=None):
        """
        通过特征点匹配,在im_source中找到最符合im_search的范围

        Args:
            im_source: 待匹配图像
            im_search: 图片模板
            threshold: 识别阈值(0~1)
            rgb: 是否使用rgb通道进行校验

        Returns:

        """
        threshold = threshold or self.threshold
        rgb = rgb or self.rgb

        im_source, im_search = self.input_image_check(im_source, im_search)
        if im_source.channels == 1:
            rgb = False
        kp_src, des_src = self.get_keypoint_and_descriptor(image=im_source)
        kp_sch, des_sch = self.get_keypoint_and_descriptor(image=im_search)

        # 在特征点集中,匹配最接近的特征点
        matches = self.match_keypoint(des_sch=des_sch, des_src=des_src)
        good = self.get_good_in_matches(matches=matches)
        filtered_good_point, angle, first_point = self.filter_good_point(good=good, kp_src=kp_src, kp_sch=kp_sch)
        rect, confidence = self.extract_good_points(im_source=im_source, im_search=im_search, kp_src=kp_src, kp_sch=kp_sch,
                                                    good=filtered_good_point, angle=angle, rgb=rgb)

        if not rect or confidence < threshold:
            return None

        best_match = generate_result(rect=rect, confi=confidence)
        LOGGING.debug("[%s] threshold=%s, result=%s" % (self.METHOD_NAME, self.threshold, best_match))
        return best_match

    @print_run_time
    def find_best_result(self, im_source, im_search, threshold=None, rgb=None):
        """
        通过特征点匹配,在im_source中找到最符合im_search的范围

        Args:
            im_source: 待匹配图像
            im_search: 图片模板
            threshold: 识别阈值(0~1)
            rgb: 是否使用rgb通道进行校验

        Returns:

        """
        ret = self.find_all_result(im_source=im_source, im_search=im_search, threshold=threshold, rgb=rgb, max_count=1)
        if ret:
            return ret[0]
        return None

    def find_all_result(self, im_source, im_search, threshold=None, rgb=None, max_count=10, max_iter_counts=20, distance_threshold=150):
        """
        通过特征点匹配,在im_source中找到全部符合im_search的范围

        Args:
            im_source: 待匹配图像
            im_search: 图片模板
            threshold: 识别阈值(0~1)
            rgb: 是否使用rgb通道进行校验
            max_count: 最多可以返回的匹配数量
            max_iter_counts: 最大的搜索次数,需要大于max_count
            distance_threshold: 距离阈值,特征点(first_point)大于该阈值后,不做后续筛选

        Returns:

        """
        threshold = self.threshold if threshold is None else threshold
        rgb = self.rgb if rgb is None else rgb

        im_source, im_search = self.input_image_check(im_source, im_search)
        result = []
        if im_source.channels == 1:
            rgb = False
        kp_src, des_src = self.get_keypoint_and_descriptor(image=im_source)
        kp_sch, des_sch = self.get_keypoint_and_descriptor(image=im_search)

        # 在特征点集中,匹配最接近的特征点
        matches = self.match_keypoint(des_sch=des_sch, des_src=des_src)
        good = self.get_good_in_matches(matches=matches)
        _max_iter_counts = 0

        while True:
            if len(good) == 0:
                break

            if len(result) == max_count:
                break

            if _max_iter_counts >= max_iter_counts:
                break

            _max_iter_counts += 1

            filtered_good_point, angle, first_point = self.filter_good_point(good=good, kp_src=kp_src, kp_sch=kp_sch)

            if first_point.distance > distance_threshold:
                break

            rect, confidence = None, 0
            try:
                rect, confidence = self.extract_good_points(im_source=im_source, im_search=im_search, kp_src=kp_src,
                                                            kp_sch=kp_sch, good=filtered_good_point, angle=angle, rgb=rgb)
            except PerspectiveTransformError:
                pass
            finally:
                if rect and confidence >= threshold:
                    # 移除改范围内的所有特征点 ??有可能因为透视变换的原因，删除了多余的特征点
                    for reverse_index in range((len(good) - 1), -1, -1):
                        point = kp_src[good[reverse_index].trainIdx].pt
                        if rect.contains(Point(point[0], point[1])):
                            good.pop(reverse_index)
                    result.append(generate_result(rect, confidence))
                else:
                    for match in filtered_good_point:
                        good.pop(good.index(match))
        return result

    def get_keypoint_and_descriptor(self, image: Image):
        """
        获取图像关键点(keypoint)与描述符(descriptor)

        Args:
            image: 待检测的灰度图像

        Returns:

        """
        if image.channels == 3:
            image = image.cvtColor(cv2.COLOR_BGR2GRAY).data
        else:
            image = image.data
        keypoint, descriptor = self.detector.detectAndCompute(image, None)

        if len(keypoint) < 2:
            raise NoEnoughPointsError('{} detect not enough feature points in input images'.format(self.METHOD_NAME))
        return keypoint, descriptor

    @staticmethod
    def filter_good_point(good, kp_src, kp_sch):
        """
        筛选最佳点

        Returns:

        """
        # 按照queryIdx排升序
        good = sorted(good, key=lambda x: x.queryIdx)
        # 筛选重复的queryidx
        queryidx_list = []
        # queryidx_list的索引对应的queryidx
        queryidx_index_list = []
        queryidx_index = 0
        queryidx_flag = True

        # first_good_point = good[0]  # 随便填一个用于对比
        while queryidx_flag:
            point = good[queryidx_index]
            _queryIdx = point.queryIdx
            queryidx_index_list.append(_queryIdx)
            # first_good_point = first_good_point if point.distance > first_good_point.distance else point
            point_list = [point]
            while True:
                queryidx_index += 1
                if queryidx_index == len(good):
                    queryidx_flag = False
                    break
                new_point = good[queryidx_index]
                new_queryidx = new_point.queryIdx
                if _queryIdx == new_queryidx:
                    point_list.append(new_point)
                else:
                    break
            queryidx_list.append(point_list)

        # 假设第一个点,及distance最小的点,为基准点
        distance_good = sorted(good, key=lambda x: x.distance)
        first_good_point = distance_good[0]

        first_good_point_train: cv2.KeyPoint = kp_src[first_good_point.trainIdx]
        first_good_point_query: cv2.KeyPoint = kp_sch[first_good_point.queryIdx]
        first_good_point_query_index = queryidx_index_list.index(first_good_point.queryIdx)
        first_good_point_angle = first_good_point_train.angle - first_good_point_query.angle

        # 计算模板图像上,该点与其他特征点的旋转角
        first_good_point_sch_origin_angle = []
        for i in kp_sch:
            _angle = keypoint_origin_angle(kp1=first_good_point_query, kp2=i)
            if _angle != 0:
                _angle = _angle - first_good_point_query.angle
            first_good_point_sch_origin_angle.append(_angle)

        # 计算目标图像中,该点与其他特征点的夹角
        good_point = []
        for i in queryidx_list:
            query_point = kp_sch[i[0].queryIdx]
            # 根据first_good_point的旋转,计算其他特征点旋转后的角度
            query_rotate_angle = query_point.angle + first_good_point_angle
            train_points = get_keypoint_from_matches(kp_src, i, 'train')
            train_points_angle = np.array([i.angle for i in train_points])
            if query_rotate_angle >= 360:
                query_rotate_angle -= 360
            angle_gap = np.abs(train_points_angle - query_rotate_angle)
            sort_angle_gap = np.argsort(angle_gap)
            good_point.append(i[sort_angle_gap[0]])

        # 计算各点以first_good_point为原点的旋转角
        ret, ret_keypoint_pt = [], []
        # ret_keypoint = []
        good_point_keypoint = get_keypoint_from_matches(kp_src, good_point, 'train')
        origin_angle_threshold = round(5 / 360, 2) * 100  # 允许的偏差值,x表示角度 round(x / 360, 2) * 100
        for i, keypoint in enumerate(good_point_keypoint):
            _angle = keypoint_origin_angle(kp1=first_good_point_train, kp2=keypoint)
            if _angle != 0:
                _angle = _angle - first_good_point_train.angle
            sch_origin_angle = first_good_point_sch_origin_angle[queryidx_index_list[i]]
            if round(abs(_angle - sch_origin_angle) / 360, 2) * 100 < origin_angle_threshold:
                if keypoint.pt not in ret_keypoint_pt:  # 去重
                    # ret_keypoint.append(keypoint)
                    ret_keypoint_pt.append(keypoint.pt)
                    ret.append(good_point[i])

        return ret, int(first_good_point_angle), first_good_point

    def match_keypoint(self, des_sch, des_src, k=10):
        """
        特征点匹配

        Args:
            des_src: 待匹配图像的描述符集
            des_sch: 图片模板的描述符集
            k(int): 获取多少匹配点

        Returns:
            List[List[cv2.DMatch]]: 包含最匹配的描述符
        """
        # k=2表示每个特征点取出2个最匹配的对应点
        matches = self.matcher.knnMatch(des_sch, des_src, k)
        return matches

    def get_good_in_matches(self, matches):
        """
        特征点过滤

        Args:
            matches: 特征点集

        Returns:
            List[cv2.DMatch]: 过滤后的描述符集
        """
        if not matches:
            return None
        good = []
        for match_index in range(len(matches)):
            match = matches[match_index]
            for DMatch_index in range(len(match)):
                if match[DMatch_index].distance <= self.FILTER_RATIO * match[-1].distance:
                    good.append(match[DMatch_index])
        return good

    def extract_good_points(self, im_source, im_search, kp_src, kp_sch, good, angle, rgb):
        """
        根据匹配点(good)数量,提取识别区域

        Args:
            im_source: 待匹配图像
            im_search: 图片模板
            kp_src: 关键点集
            kp_sch: 关键点集
            good: 描述符集
            angle: 旋转角度
            rgb: 是否使用rgb通道进行校验

        Returns:
            范围,和置信度
        """
        len_good = len(good)
        confidence, rect = None, None
        if len_good in [0, 1]:
            pass
        elif len_good == 2:
            # TODO: 待做
            pass
        elif len_good == 3:
            pass
            # self._get_warpAffine_image(im_source=im_source, im_search=im_search,
            #                            kp_sch=kp_sch, kp_src=kp_src, good=good, angle=angle)
        else:  # len > 4
            target_img, rect = self._get_warpPerspective_image(im_source=im_source, im_search=im_search,
                                                               kp_sch=kp_sch, kp_src=kp_src, good=good)
            if target_img:
                confidence = self._cal_confidence(im_source=im_search, im_search=target_img, rgb=rgb)

        return rect, confidence

    def _get_warpPerspective_image(self, im_source, im_search, kp_src, kp_sch, good):
        """
        使用透视变换,获取识别的目标图片

        Args:
            im_source: 待匹配图像
            im_search: 图片模板
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
        h, w = im_search.shape[:2]
        h_s, w_s = im_source.shape[:2]
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        try:
            dst: np.ndarray = cv2.perspectiveTransform(pts, M)
            pypts = [tuple(npt[0]) for npt in dst.tolist()]
            point_1 = np.array([pypts[0], pypts[3], pypts[1], pypts[2]], dtype=np.float32)
            point_2 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            matrix = cv2.getPerspectiveTransform(point_1, point_2)
            output = im_source.warpPerspective(matrix, size=(w, h))  # https://github.com/opencv/opencv/issues/11784
        except cv2.error as err:
            raise PerspectiveTransformError(err)

        # pypts四个值按照顺序分别是: 左上,左下,右下,右上
        x = [int(i[0]) for i in pypts]
        y = [int(i[1]) for i in pypts]
        x_min, x_max = min(x), max(x)
        y_min, y_max = min(y), max(y)
        # 挑选出目标矩形区域可能会有越界情况，越界时直接将其置为边界：
        # 超出左边界取0，超出右边界取w_s-1，超出下边界取0，超出上边界取h_s-1
        # 当x_min小于0时，取0。  x_max小于0时，取0。
        x_min, x_max = int(max(x_min, 0)), int(max(x_max, 0))
        # 当x_min大于w_s时，取值w_s-1。  x_max大于w_s-1时，取w_s-1。
        x_min, x_max = int(min(x_min, w_s - 1)), int(min(x_max, w_s - 1))
        # 当y_min小于0时，取0。  y_max小于0时，取0。
        y_min, y_max = int(max(y_min, 0)), int(max(y_max, 0))
        # 当y_min大于h_s时，取值h_s-1。  y_max大于h_s-1时，取h_s-1。
        y_min, y_max = int(min(y_min, h_s - 1)), int(min(y_max, h_s - 1))
        rect = Rect(x=x_min, y=y_min, width=(x_max - x_min), height=(y_max - y_min))
        return output, rect

    @staticmethod
    def _target_image_crop(img, rect):
        """
        截取目标图像

        Args:
            img: 图像
            rect: 图像范围

        Returns:
            裁剪后的图像
        """
        try:
            target_img = img.crop(rect)
        except OverflowError:
            raise MatchResultError(f"Target area({rect}) out of screen{img.size}")
        return target_img

    def _cal_confidence(self, im_source, im_search, rgb: bool):
        """
        将截图和识别结果缩放到大小一致,并计算可信度

        Args:
            im_source: 待匹配图像
            im_search: 图片模板
            crop_rect: 需要在im_source截取的区域
            rgb:是否使用rgb通道进行校验

        Returns:

        """
        h, w = im_search.size
        im_search = im_search.resize(w, h)
        if rgb:
            confidence = self.template.cal_rgb_confidence(im_source=im_source, im_search=im_search)
        else:
            confidence = self.template.cal_ccoeff_confidence(im_source=im_source, im_search=im_search)

        confidence = (1 + confidence) / 2
        return confidence

    def input_image_check(self, im_source, im_search):
        im_source = self._image_check(im_source)
        im_search = self._image_check(im_search)

        assert im_source.place == im_search.place, '输入图片类型必须相同, source={}, search={}'.format(im_source.place, im_search.place)
        assert im_source.dtype == im_search.dtype, '输入图片数据类型必须相同, source={}, search={}'.format(im_source.dtype, im_search.dtype)
        assert im_source.channels == im_search.channels, '输入图片通道必须相同, source={}, search={}'.format(im_source.channels, im_search.channels)
        return im_source, im_search

    def _image_check(self, data):
        if not isinstance(data, Image):
            data = Image(data, dtype=self.Dtype)

        if data.place not in self.Place:
            raise TypeError(f'{self.METHOD_NAME}方法,Image类型必须为(Place.Mat, Place.UMat, Place.Ndarray)')
        return data

    @staticmethod
    def _find_homography(sch_pts, src_pts):
        """
        多组特征点对时，求取单向性矩阵
        """
        try:
            M, mask = cv2.findHomography(sch_pts, src_pts, cv2.RANSAC, 5.0)
        except cv2.error:
            import traceback
            traceback.print_exc()
            raise HomographyError("OpenCV error in _find_homography()...")
        else:
            if mask is None:
                raise HomographyError("In _find_homography(), find no mask...")
            else:
                return M, mask
