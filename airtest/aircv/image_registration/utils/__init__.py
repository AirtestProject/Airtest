#! usr/bin/python
# -*- coding:utf-8 -*-
import math
import cv2
from baseImage import Rect


def generate_result(rect, confi):
    """Format the result: 定义图像识别结果格式."""
    ret = dict(result=_get_rect_middle_point(rect),
               rectangle=_get_rect_target_rectangle(rect),
               confidence=confi)
    return ret


def _get_rect_middle_point(rect: Rect):
    middle = rect.middle
    return middle.x, middle.y


def _get_rect_target_rectangle(rect: Rect):
    """根据左上角点和宽高求出目标区域."""
    left_top_pos = (rect.tl.x, rect.tl.y)
    w, h = rect.width, rect.height

    x_min, y_min = left_top_pos
    # 中心位置的坐标:
    x_middle, y_middle = int(x_min + w / 2), int(y_min + h / 2)
    # 左下(min,max)->右下(max,max)->右上(max,min)
    left_bottom_pos, right_bottom_pos = (x_min, y_min + h), (x_min + w, y_min + h)
    right_top_pos = (x_min + w, y_min)
    # 点击位置:
    middle_point = (x_middle, y_middle)
    # 识别目标区域: 点序:左上->左下->右下->右上, 左上(min,min)右下(max,max)
    rectangle = (left_top_pos, left_bottom_pos, right_bottom_pos, right_top_pos)

    return middle_point, rectangle


def keypoint_distance(kp1: cv2.KeyPoint, kp2: cv2.KeyPoint):
    """求两个keypoint的两点之间距离"""
    x = kp1.pt[0] - kp2.pt[0]
    y = kp1.pt[1] - kp2.pt[1]
    return math.sqrt((x ** 2) + (y ** 2))


def keypoint_angle(kp1: cv2.KeyPoint, kp2: cv2.KeyPoint):
    """求两个keypoint的夹角 """
    k = [
        (kp1.angle - 180) if kp1.angle >= 180 else kp1.angle,
        (kp2.angle - 180) if kp2.angle >= 180 else kp2.angle
    ]
    if k[0] == k[1]:
        return 0
    else:
        return abs(k[0] - k[1])


def get_keypoint_from_matches(kp, matches, mode):
    res = []
    if mode == 'query':
        for match in matches:
            res.append(kp[match.queryIdx])
    elif mode == 'train':
        for match in matches:
            res.append(kp[match.trainIdx])
    return res


def keypoint_origin_angle(kp1: cv2.KeyPoint, kp2: cv2.KeyPoint):
    """
    以kp1为原点,计算kp2的旋转角度
    """
    origin_point = kp1.pt
    train_point = kp2.pt

    point = (abs(origin_point[0] - train_point[0]), abs(origin_point[1] - train_point[1]))

    x_quadrant = (1, 4)
    y_quadrant = (3, 4)
    if origin_point[0] > train_point[0]:
        x_quadrant = (2, 3)

    if origin_point[1] > train_point[1]:
        y_quadrant = (1, 2)
    point_quadrant = list(set(x_quadrant).intersection(set(y_quadrant)))[0]

    x, y = point[::-1]
    angle = math.degrees(math.atan2(x, y))
    if point_quadrant == 4:
        angle = angle
    elif point_quadrant == 3:
        angle = 180 - angle
    elif point_quadrant == 2:
        angle = 180 + angle
    elif point_quadrant == 1:
        angle = 360 - angle

    return angle
