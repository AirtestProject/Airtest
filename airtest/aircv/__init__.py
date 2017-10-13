#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Target Recognition cross resolution:
    ## based on OpenCV:
    ## template()
    ## sift()
    work under py2 and py3.


Declaration:
    ## Supply some support tools for aircv.

Some snippets of opencv2:
    ## Resize image
    ref: <http://docs.opencv.org/modules/imgproc/doc/geometric_transformations.html#void resize(InputArray src, OutputArray dst, Size dsize, double fx, double fy, int interpolation)>

        # half width and height
        small = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)

        # 金字塔--只能 1/4 地缩小(宽缩1/2，高缩1/2.)
        crop_img_resize=cv2.pyrDown(crop_img,(h,w))

        # to fixed Size
        small = cv2.resize(image, (100, 50))

    ## Constant
        1: cv2.IMREAD_COLOR
        0: cv2.IMREAD_GRAYSCALE
        -1: cv2.IMREAD_UNCHANGED

    ## Show image
        cv2.imshow('image title',img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    ## Generate a blank image
        size = (height, width, channels) = (512, 256, 3)
        img = np.zeros(size, np.uint8)

    ## Sort points
        pts = [(0, 7), (3, 5), (2, 6)]

        sorted(pts, key=lambda p: p[0]) # sort by point x row, expect [(0, 7), (2, 6), (3, 5)]

    ## Crop image
        croped = img[y0:y1, x0:x1]

"""

import sys
import cv2
import numpy as np

from .utils import cv2_2_pil

# from .sift import find_sift, find_sift_in_pre
from .sift import find_sift
from .template import find_template, find_all_template
# from .focus_ignore_template import template_focus_ignore_after_resize, tpl_focus_ignore_after_resize_with_pre

from .error import Error

__version__ = "0.1.7"
__project_url__ = "https://github.com/netease/aircv"


DEBUG = False

if sys.version_info >= (3, 0, 0):
    PY3 = True
else:
    PY3 = False


def imread(filename):
    '''根据图片路径，将图片读取为cv2的图片处理格式.'''
    if not PY3:
        filename = filename.decode('utf-8').encode(sys.getfilesystemencoding())
    else:
        pass
    img = cv2.imread(filename, 1)
    if img is None:
        raise RuntimeError("file: '%s' not exists" % filename)
    return img


def imwrite(filename, img):
    '''写出图片到本地路径'''
    if not PY3:
        if isinstance(filename, unicode):
            # filename = filename.encode(sys.getfilesystemencoding())
            filename = filename.decode('utf-8').encode(sys.getfilesystemencoding())
        else:
            filename = filename.encode(sys.getfilesystemencoding())

    cv2.imwrite(filename, img)


def show(img, title="show_img", test_flag=False):
    '''在可缩放窗口里显示图片.'''
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
    '''
        函数使图片可顺时针或逆时针旋转90、180、270度.
        默认clockwise=True：顺时针旋转
    '''

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


def crop(img, rect=(0, 0, 0, 0)):
    '''Crop image: rect=[x_min, y_min, x_max ,y_max]，单位为像素.'''
    if isinstance(rect, (list, tuple)):
        height, width = img.shape[:2]
        # # 将rect列表中的0、1转换成0.0、1.0
        # rect = [float(i) if i == 0 or i == 1 else i for i in rect]
        all_int = [1 for i in rect if isinstance(i, int)]
        all_float = [1 for i in rect if isinstance(i, float)]
        if 1 in all_float:  # rect含有float数据，就立刻使用比例进行转换：
            rect = [int(width * rect[0]), int(height * rect[1]), int(width * rect[2]), int(height * rect[3])]
        else:
            pass
        # 获取在图像中的实际有效区域：
        x_min, y_min, x_max, y_max = rect[0], rect[1], rect[2], rect[3]
        x_min, y_min = max(0, x_min), max(0, y_min)
        x_min, y_min = min(width - 1, x_min), min(height - 1, y_min)
        x_max, y_max = max(0, x_max), max(0, y_max)
        x_max, y_max = min(width - 1, x_max), min(height - 1, y_max)
        # 返回剪切的有效图像：
        img_crop = img[y_min:y_max, x_min:x_max]

        return img_crop


def crop_image(img, rect=(0, 0, 0, 0)):
    '''
        区域截图，同时返回截取结果 和 截取偏移;
        Crop image , rect = [x_min, y_min, x_max ,y_max].
        (airtest中有用到)
    '''
    if img is None:
        raise NoneImageError("Image to crop is None !")

    if isinstance(rect, (list, tuple)):
        height, width = img.shape[:2]
        # 获取在图像中的实际有效区域：
        x_min, y_min, x_max, y_max = rect[0], rect[1], rect[2], rect[3]
        x_min, y_min = max(0, x_min), max(0, y_min)
        x_min, y_min = min(width - 1, x_min), min(height - 1, y_min)
        x_max, y_max = max(0, x_max), max(0, y_max)
        x_max, y_max = min(width - 1, x_max), min(height - 1, y_max)

        # 返回剪切的有效图像+左上角的偏移坐标：
        img_crop = img[y_min:y_max, x_min:x_max]
        left_up_pos = (x_min, y_min)
        return img_crop, left_up_pos
    elif rect is None:
        # 如果图片截取rect为None，就返回原图，但是左上角坐标为[0, 0]
        return img, [0, 0]
    else:
        raise Exception("to crop a image, rect should be a list like: [x_min, x_max, y_min, y_max].")


def mark_point(img, point=None):
    ''' 调试用的: 标记一个点 '''
    if point:
        x, y = point
        # cv2.rectangle(img, (x, y), (x+10, y+10), 255, 1, lineType=cv2.CV_AA)
        radius = 20
        cv2.circle(img, (x, y), radius, 255, thickness=2)
        cv2.line(img, (x-radius, y), (x+radius, y), 100)  # x line
        cv2.line(img, (x, y-radius), (x, y+radius), 100)  # y line
    return img


def mask_image(screen, mask=None, color=(255,255,255), linewidth=-1):
    """
        将screen的mask矩形区域刷成白色gbr(255, 255, 255).
        其中mask区域为: [x_min, y_min, x_max, y_max].
        color: 顺序分别的blue-green-red通道.
        linewidth: 为-1时则完全填充填充，为正整数时为线框宽度.
    """
    if mask:
        # 将划线边界外扩，保证线内区域不被线所遮挡:
        offset = int(linewidth / 2)
        return cv2.rectangle(screen, (mask[0] - offset, mask[1] - offset), (mask[2] + linewidth, mask[3] + linewidth), color, linewidth)
        # return cv2.rectangle(screen, (mask[0], mask[1]), (mask[2], mask[3]), color, linewidth)
    else:
        return screen
