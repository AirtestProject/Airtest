#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import time
import math
import numpy as np
from PIL import Image

from airtest.utils.logger import get_logger
from .error import TemplateInputError

LOGGING = get_logger(__name__)


def print_run_time(func):

    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        ret = func(self, *args, **kwargs)
        t = time.time() - start_time
        LOGGING.debug("%s() run time is %.2f s." % (func.__name__, t))
        if ret and isinstance(ret, dict):
            ret["time"] = t
        return ret

    return wrapper


def generate_result(middle_point, pypts, confi):
    """Format the result: 定义图像识别结果格式."""
    ret = dict(result=middle_point,
               rectangle=pypts,
               confidence=confi)
    return ret


def check_image_valid(im_source, im_search):
    """Check if the input images valid or not."""
    if im_source is not None and im_source.any() and im_search is not None and im_search.any():
        return True
    else:
        return False


def check_source_larger_than_search(im_source, im_search):
    """检查图像识别的输入."""
    # 图像格式, 确保输入图像为指定的矩阵格式:
    # 图像大小, 检查截图宽、高是否大于了截屏的宽、高:
    h_search, w_search = im_search.shape[:2]
    h_source, w_source = im_source.shape[:2]
    if h_search > h_source or w_search > w_source:
        raise TemplateInputError("error: in template match, found im_search bigger than im_source.")


def img_mat_rgb_2_gray(img_mat):
    """
    Turn img_mat into gray_scale, so that template match can figure the img data.
    "print(type(im_search[0][0])")  can check the pixel type.
    """
    assert isinstance(img_mat[0][0], np.ndarray), "input must be instance of np.ndarray"
    return cv2.cvtColor(img_mat, cv2.COLOR_BGR2GRAY)


def img_2_string(img):
    _, png = cv2.imencode('.png', img)
    return png.tostring()


def string_2_img(pngstr):
    nparr = np.frombuffer(pngstr, np.uint8)
    try:
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except cv2.error:
        # cv2.error: OpenCV(4.6.0) D:\a\opencv-python\opencv-python\opencv\modules\imgcodecs\src\loadsave.cpp:816: error: (-215:Assertion failed) !buf.empty() in function 'cv::imdecode_
        # If the image is empty, return None
        img = None
    return img


def pil_2_cv2(pil_image):
    open_cv_image = np.array(pil_image)
    # Convert RGB to BGR (method-1):
    open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
    # Convert RGB to BGR (method-2):
    # b, g, r = cv2.split(open_cv_image)
    # open_cv_image = cv2.merge([r, g, b])
    return open_cv_image


def cv2_2_pil(cv2_image):
    cv2_im = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_im = Image.fromarray(cv2_im)
    return pil_im


def compress_image(pil_img, path, quality, max_size=None):
    """
    Save the picture and compress

    :param pil_img: PIL image
    :param path: save path
    :param quality: the image quality, integer in range [1, 99]
    :param max_size: the maximum size of the picture, e.g 1200
    :return:
    """
    if max_size:
        # The picture will be saved in a size <= max_size*max_size
        pil_img.thumbnail((max_size, max_size), Image.LANCZOS)
    quality = int(round(quality))
    if quality <= 0 or quality >= 100:
        raise Exception("SNAPSHOT_QUALITY (" + str(quality) + ") should be an integer in the range [1,99]")
    pil_img.save(path, quality=quality, optimize=True)


def get_keypoint_from_matches(kp, matches, mode):
    res = []
    if mode == 'query':
        for match in matches:
            res.append(kp[match.queryIdx])
    elif mode == 'train':
        for match in matches:
            res.append(kp[match.trainIdx])

    return res


def keypoint_distance(kp1, kp2):
    """求两个keypoint的两点之间距离"""
    if isinstance(kp1, cv2.KeyPoint):
        kp1 = kp1.pt
    elif isinstance(kp1, (list, tuple)):
        kp1 = kp1
    else:
        raise ValueError('kp1需要时keypoint或直接是坐标, kp1={}'.format(kp1))

    if isinstance(kp2, cv2.KeyPoint):
        kp2 = kp2.pt
    elif isinstance(kp2, (list, tuple)):
        kp2 = kp2
    else:
        raise ValueError('kp2需要时keypoint或直接是坐标, kp1={}'.format(kp2))

    x = kp1[0] - kp2[0]
    y = kp1[1] - kp2[1]
    return math.sqrt((x ** 2) + (y ** 2))


def _mapping_angle_distance(distance, origin_angle, angle):
    """

    Args:
        distance: 距离
        origin_angle: 对应原点的角度
        angle: 旋转角度

    """
    _angle = origin_angle + angle
    _y = distance * math.cos((math.pi * _angle) / 180)
    _x = distance * math.sin((math.pi * _angle) / 180)
    return round(_x, 3), round(_y, 3)


def rectangle_transform(point, size, mapping_point, mapping_size, angle):
    """
    根据point,找出mapping_point映射的矩形顶点坐标

    Args:
        point: 坐标在矩形中的坐标
        size: 矩形的大小(h, w)
        mapping_point: 映射矩形的坐标
        mapping_size: 映射矩形的大小(h, w)
        angle: 旋转角度

    Returns:

    """
    h, w = size[0], size[1]
    _h, _w = mapping_size[0], mapping_size[1]

    h_scale = _h / h
    w_scale = _w / w

    tl = keypoint_distance((0, 0), point)  # 左上
    tr = keypoint_distance((w, 0), point)  # 右上
    bl = keypoint_distance((0, h), point)  # 左下
    br = keypoint_distance((w, h), point)  # 右下

    # x = np.float32([point[1], point[1], (h - point[1]), (h - point[1])])
    # y = np.float32([point[0], (w - point[0]), point[0], (w - point[0])])
    # A, B, C, D = cv2.phase(x, y, angleInDegrees=True)
    A = math.degrees(math.atan2(point[0], point[1]))
    B = math.degrees(math.atan2((w - point[0]), point[1]))
    C = math.degrees(math.atan2(point[0], (h - point[1])))
    D = math.degrees(math.atan2((w - point[0]), (h - point[1])))

    new_tl = _mapping_angle_distance(tl, A, angle=angle)
    new_tl = (-new_tl[0] * w_scale, -new_tl[1] * h_scale)
    new_tl = (mapping_point[0] + new_tl[0], mapping_point[1] + new_tl[1])

    new_tr = _mapping_angle_distance(tr, B, angle=angle)
    new_tr = (new_tr[0] * w_scale, -new_tr[1] * h_scale)
    new_tr = (mapping_point[0] + new_tr[0], mapping_point[1] + new_tr[1])

    new_bl = _mapping_angle_distance(bl, C, angle=angle)
    new_bl = (-new_bl[0] * w_scale, new_bl[1] * h_scale)
    new_bl = (mapping_point[0] + new_bl[0], mapping_point[1] + new_bl[1])

    new_br = _mapping_angle_distance(br, D, angle=angle)
    new_br = (new_br[0] * w_scale, new_br[1] * h_scale)
    new_br = (mapping_point[0] + new_br[0], mapping_point[1] + new_br[1])

    return [new_tl, new_tr, new_bl, new_br]


def get_middle_point(w_h_range):
    x, y = w_h_range[0], w_h_range[2]
    width = w_h_range[1] - w_h_range[0]
    height = w_h_range[3] - w_h_range[2]
    middle_point = (
        x + width / 2,
        y + height / 2
    )
    return middle_point
