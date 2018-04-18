#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import cv2
import numpy as np
from .error import FileNotExistError
from six import PY3


def imread(filename):
    """根据图片路径，将图片读取为cv2的图片处理格式."""
    if not os.path.isfile(filename):
        raise FileNotExistError("File not exist: %s" % filename)
    if PY3:
        stream = open(filename, "rb")
        bytes = bytearray(stream.read())
        numpyarray = np.asarray(bytes, dtype=np.uint8)
        img = cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)
    else:
        filename = filename.encode(sys.getfilesystemencoding())
        img = cv2.imread(filename, 1)
    return img


def imwrite(filename, img):
    """写出图片到本地路径"""
    if not PY3:
        filename = filename.encode(sys.getfilesystemencoding())
    cv2.imwrite(filename, img)


def show(img, title="show_img", test_flag=False):
    """在可缩放窗口里显示图片."""
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.imshow(title, img)
    if not test_flag:
        cv2.waitKey(0)
    cv2.destroyAllWindows()


def show_origin_size(img, title="image", test_flag=False):
    """原始尺寸窗口中显示图片."""
    cv2.imshow(title, img)
    if not test_flag:
        cv2.waitKey(0)
    cv2.destroyAllWindows()


def rotate(img, angle=90, clockwise=True):
    """
        函数使图片可顺时针或逆时针旋转90、180、270度.
        默认clockwise=True：顺时针旋转
    """

    def count_clock_rotate(img):
        # 逆时针旋转90°
        rows, cols = img.shape[:2]
        rotate_img = np.zeros((cols, rows))
        rotate_img = cv2.transpose(img)
        rotate_img = cv2.flip(rotate_img, 0)
        return rotate_img

    # 将角度旋转转化为逆时针旋转90°的次数:
    counter_rotate_time = (4 - angle / 90) % 4 if clockwise else (angle / 90) % 4
    for i in range(counter_rotate_time):
        img = count_clock_rotate(img)

    return img


def crop_image(img, rect):
    """
        区域截图，同时返回截取结果 和 截取偏移;
        Crop image , rect = [x_min, y_min, x_max ,y_max].
        (airtest中有用到)
    """

    if isinstance(rect, (list, tuple)):
        height, width = img.shape[:2]
        # 获取在图像中的实际有效区域：
        x_min, y_min, x_max, y_max = [int(i) for i in rect]
        x_min, y_min = max(0, x_min), max(0, y_min)
        x_min, y_min = min(width - 1, x_min), min(height - 1, y_min)
        x_max, y_max = max(0, x_max), max(0, y_max)
        x_max, y_max = min(width - 1, x_max), min(height - 1, y_max)

        # 返回剪切的有效图像+左上角的偏移坐标：
        img_crop = img[y_min:y_max, x_min:x_max]
        return img_crop
    else:
        raise Exception("to crop a image, rect should be a list like: [x_min, y_min, x_max, y_max].")


def mark_point(img, point):
    """ 调试用的: 标记一个点 """
    x, y = point
    # cv2.rectangle(img, (x, y), (x+10, y+10), 255, 1, lineType=cv2.CV_AA)
    radius = 20
    cv2.circle(img, (x, y), radius, 255, thickness=2)
    cv2.line(img, (x-radius, y), (x+radius, y), 100)  # x line
    cv2.line(img, (x, y-radius), (x, y+radius), 100)  # y line
    return img


def mask_image(img, mask, color=(255, 255, 255), linewidth=-1):
    """
        将screen的mask矩形区域刷成白色gbr(255, 255, 255).
        其中mask区域为: [x_min, y_min, x_max, y_max].
        color: 顺序分别的blue-green-red通道.
        linewidth: 为-1时则完全填充填充，为正整数时为线框宽度.
    """
    # 将划线边界外扩，保证线内区域不被线所遮挡:
    offset = int(linewidth / 2)
    return cv2.rectangle(img, (mask[0] - offset, mask[1] - offset), (mask[2] + linewidth, mask[3] + linewidth), color, linewidth)


def get_resolution(img):
    h, w = img.shape[:2]
    return w, h
