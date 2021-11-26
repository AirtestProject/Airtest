#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import numpy as np

from .error import *  # noqa
from .utils import generate_result, check_image_valid
from .cal_confidence import cal_ccoeff_confidence, cal_rgb_confidence

# SIFT识别特征点匹配，参数设置:
FLANN_INDEX_KDTREE = 0
FLANN = cv2.FlannBasedMatcher({'algorithm': FLANN_INDEX_KDTREE, 'trees': 5}, dict(checks=50))
# SIFT参数: FILTER_RATIO为SIFT优秀特征点过滤比例值(0-1范围，建议值0.4-0.6)
FILTER_RATIO = 0.59
# SIFT参数: SIFT识别时只找出一对相似特征点时的置信度(confidence)
ONE_POINT_CONFI = 0.5


def find_sift(im_source, im_search, threshold=0.8, rgb=True, good_ratio=FILTER_RATIO):
    """基于sift进行图像识别，只筛选出最优区域."""
    # 第一步：检验图像是否正常：
    if not check_image_valid(im_source, im_search):
        return None

    # 第二步：获取特征点集并匹配出特征点对: 返回值 good, pypts, kp_sch, kp_src
    kp_sch, kp_src, good = _get_key_points(im_source, im_search, good_ratio)

    # 第三步：根据匹配点对(good),提取出来识别区域:
    if len(good) == 0:
        # 匹配点对为0,无法提取识别区域：
        return None
    elif len(good) == 1:
        # 匹配点对为1，可信度赋予设定值，并直接返回:
        return _handle_one_good_points(kp_src, good, threshold) if ONE_POINT_CONFI >= threshold else None
    elif len(good) == 2:
        # 匹配点对为2，根据点对求出目标区域，据此算出可信度：
        origin_result = _handle_two_good_points(im_source, im_search, kp_src, kp_sch, good)
        if isinstance(origin_result, dict):
            return origin_result if ONE_POINT_CONFI >= threshold else None
        else:
            middle_point, pypts, w_h_range = _handle_two_good_points(im_source, im_search, kp_src, kp_sch, good)
    elif len(good) == 3:
        # 匹配点对为3，取出点对，求出目标区域，据此算出可信度：
        origin_result = _handle_three_good_points(im_source, im_search, kp_src, kp_sch, good)
        if isinstance(origin_result, dict):
            return origin_result if ONE_POINT_CONFI >= threshold else None
        else:
            middle_point, pypts, w_h_range = _handle_three_good_points(im_source, im_search, kp_src, kp_sch, good)
    else:
        # 匹配点对 >= 4个，使用单矩阵映射求出目标区域，据此算出可信度：
        middle_point, pypts, w_h_range = _many_good_pts(im_source, im_search, kp_sch, kp_src, good)

    # 第四步：根据识别区域，求出结果可信度，并将结果进行返回:
    # 对识别结果进行合理性校验: 小于5个像素的，或者缩放超过5倍的，一律视为不合法直接raise.
    _target_error_check(w_h_range)
    # 将截图和识别结果缩放到大小一致,准备计算可信度
    x_min, x_max, y_min, y_max, w, h = w_h_range
    target_img = im_source[y_min:y_max, x_min:x_max]
    resize_img = cv2.resize(target_img, (w, h))
    confidence = _cal_sift_confidence(im_search, resize_img, rgb=rgb)

    best_match = generate_result(middle_point, pypts, confidence)
    print("[aircv][sift] threshold=%s, result=%s" % (threshold, best_match))
    return best_match if confidence >= threshold else None


def mask_sift(im_source, im_search, threshold=0.8, rgb=True, good_ratio=FILTER_RATIO):
    """基于sift查找多个目标区域的方法."""
    # 求出特征点后，im_source中获得match的那些点进行聚类
    raise NotImplementedError


def find_all_sift(im_source, im_search, threshold=0.8, rgb=True, good_ratio=FILTER_RATIO):
    """基于sift查找多个目标区域的方法."""
    # 求出特征点后，im_source中获得match的那些点进行聚类
    raise NotImplementedError


def _init_sift():
    """Make sure that there is SIFT module in OpenCV."""
    if cv2.__version__.startswith("3."):
        # OpenCV3.x, sift is in contrib module, you need to compile it seperately.
        try:
            sift = cv2.xfeatures2d.SIFT_create(edgeThreshold=10)
        except:
            print("to use SIFT, you should build contrib with opencv3.0")
            raise NoSIFTModuleError("There is no SIFT module in your OpenCV environment !")
    else:
        # OpenCV2.x, just use it.
        sift = cv2.SIFT(edgeThreshold=10)

    return sift


def _get_key_points(im_source, im_search, good_ratio):
    """根据传入图像,计算图像所有的特征点,并得到匹配特征点对."""
    # 准备工作: 初始化sift算子
    sift = _init_sift()
    # 第一步：获取特征点集，并匹配出特征点对: 返回值 good, pypts, kp_sch, kp_src
    kp_sch, des_sch = sift.detectAndCompute(im_search, None)
    kp_src, des_src = sift.detectAndCompute(im_source, None)
    # When apply knnmatch , make sure that number of features in both test and
    #       query image is greater than or equal to number of nearest neighbors in knn match.
    if len(kp_sch) < 2 or len(kp_src) < 2:
        raise NoSiftMatchPointError("Not enough feature points in input images !")

    # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
    matches = FLANN.knnMatch(des_sch, des_src, k=2)
    good = []
    # good为特征点初选结果，剔除掉前两名匹配太接近的特征点，不是独特优秀的特征点直接筛除(多目标识别情况直接不适用)
    for m, n in matches:
        if m.distance < good_ratio * n.distance:
            good.append(m)
    # good点需要去除重复的部分，（设定源图像不能有重复点）去重时将src图像中的重复点找出即可
    # 去重策略：允许搜索图像对源图像的特征点映射一对多，不允许多对一重复（即不能源图像上一个点对应搜索图像的多个点）
    good_diff, diff_good_point = [], [[]]
    for m in good:
        diff_point = [int(kp_src[m.trainIdx].pt[0]), int(kp_src[m.trainIdx].pt[1])]
        if diff_point not in diff_good_point:
            good_diff.append(m)
            diff_good_point.append(diff_point)
    good = good_diff

    return kp_sch, kp_src, good


def _handle_one_good_points(kp_src, good, threshold):
    """sift匹配中只有一对匹配的特征点对的情况."""
    # 识别中心即为该匹配点位置:
    middle_point = int(kp_src[good[0].trainIdx].pt[0]), int(kp_src[good[0].trainIdx].pt[1])
    confidence = ONE_POINT_CONFI
    # 单个特征点对,识别区域无效化:
    pypts = [middle_point for i in range(4)]
    result = generate_result(middle_point, pypts, confidence)

    return None if confidence < threshold else result


def _handle_two_good_points(im_source, im_search, kp_src, kp_sch, good):
    """处理两对特征点的情况."""
    pts_sch1 = int(kp_sch[good[0].queryIdx].pt[0]), int(kp_sch[good[0].queryIdx].pt[1])
    pts_sch2 = int(kp_sch[good[1].queryIdx].pt[0]), int(kp_sch[good[1].queryIdx].pt[1])
    pts_src1 = int(kp_src[good[0].trainIdx].pt[0]), int(kp_src[good[0].trainIdx].pt[1])
    pts_src2 = int(kp_src[good[1].trainIdx].pt[0]), int(kp_src[good[1].trainIdx].pt[1])

    return _two_good_points(pts_sch1, pts_sch2, pts_src1, pts_src2, im_search, im_source)


def _handle_three_good_points(im_source, im_search, kp_src, kp_sch, good):
    """处理三对特征点的情况."""
    # 拿出sch和src的两个点(点1)和(点2点3的中点)，
    # 然后根据两个点原则进行后处理(注意ke_sch和kp_src以及queryIdx和trainIdx):
    pts_sch1 = int(kp_sch[good[0].queryIdx].pt[0]), int(kp_sch[good[0].queryIdx].pt[1])
    pts_sch2 = int((kp_sch[good[1].queryIdx].pt[0] + kp_sch[good[2].queryIdx].pt[0]) / 2), int(
        (kp_sch[good[1].queryIdx].pt[1] + kp_sch[good[2].queryIdx].pt[1]) / 2)
    pts_src1 = int(kp_src[good[0].trainIdx].pt[0]), int(kp_src[good[0].trainIdx].pt[1])
    pts_src2 = int((kp_src[good[1].trainIdx].pt[0] + kp_src[good[2].trainIdx].pt[0]) / 2), int(
        (kp_src[good[1].trainIdx].pt[1] + kp_src[good[2].trainIdx].pt[1]) / 2)
    return _two_good_points(pts_sch1, pts_sch2, pts_src1, pts_src2, im_search, im_source)


def _many_good_pts(im_source, im_search, kp_sch, kp_src, good):
    """特征点匹配点对数目>=4个，可使用单矩阵映射,求出识别的目标区域."""
    sch_pts, img_pts = np.float32([kp_sch[m.queryIdx].pt for m in good]).reshape(
        -1, 1, 2), np.float32([kp_src[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    # M是转化矩阵
    M, mask = _find_homography(sch_pts, img_pts)
    matches_mask = mask.ravel().tolist()
    # 从good中间筛选出更精确的点(假设good中大部分点为正确的，由ratio=0.7保障)
    selected = [v for k, v in enumerate(good) if matches_mask[k]]

    # 针对所有的selected点再次计算出更精确的转化矩阵M来
    sch_pts, img_pts = np.float32([kp_sch[m.queryIdx].pt for m in selected]).reshape(
        -1, 1, 2), np.float32([kp_src[m.trainIdx].pt for m in selected]).reshape(-1, 1, 2)
    M, mask = _find_homography(sch_pts, img_pts)
    # 计算四个角矩阵变换后的坐标，也就是在大图中的目标区域的顶点坐标:
    h, w = im_search.shape[:2]
    h_s, w_s = im_source.shape[:2]
    pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
    dst = cv2.perspectiveTransform(pts, M)

    # trans numpy arrary to python list: [(a, b), (a1, b1), ...]
    def cal_rect_pts(dst):
        return [tuple(npt[0]) for npt in dst.astype(int).tolist()]

    pypts = cal_rect_pts(dst)
    # 注意：虽然4个角点有可能越出source图边界，但是(根据精确化映射单映射矩阵M线性机制)中点不会越出边界
    lt, br = pypts[0], pypts[2]
    middle_point = int((lt[0] + br[0]) / 2), int((lt[1] + br[1]) / 2)
    # 考虑到算出的目标矩阵有可能是翻转的情况，必须进行一次处理，确保映射后的“左上角”在图片中也是左上角点：
    x_min, x_max = min(lt[0], br[0]), max(lt[0], br[0])
    y_min, y_max = min(lt[1], br[1]), max(lt[1], br[1])
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
    # 目标区域的角点，按左上、左下、右下、右上点序：(x_min,y_min)(x_min,y_max)(x_max,y_max)(x_max,y_min)
    pts = np.float32([[x_min, y_min], [x_min, y_max], [
                     x_max, y_max], [x_max, y_min]]).reshape(-1, 1, 2)
    pypts = cal_rect_pts(pts)

    return middle_point, pypts, [x_min, x_max, y_min, y_max, w, h]


def _two_good_points(pts_sch1, pts_sch2, pts_src1, pts_src2, im_search, im_source):
    """返回两对匹配特征点情形下的识别结果."""
    # 先算出中心点(在im_source中的坐标)：
    middle_point = [int((pts_src1[0] + pts_src2[0]) / 2), int((pts_src1[1] + pts_src2[1]) / 2)]
    pypts = []
    # 如果特征点同x轴或同y轴(无论src还是sch中)，均不能计算出目标矩形区域来，此时返回值同good=1情形
    if pts_sch1[0] == pts_sch2[0] or pts_sch1[1] == pts_sch2[1] or pts_src1[0] == pts_src2[0] or pts_src1[1] == pts_src2[1]:
        confidence = ONE_POINT_CONFI
        one_match = generate_result(middle_point, pypts, confidence)
        return one_match
    # 计算x,y轴的缩放比例：x_scale、y_scale，从middle点扩张出目标区域:(注意整数计算要转成浮点数结果!)
    h, w = im_search.shape[:2]
    h_s, w_s = im_source.shape[:2]
    x_scale = abs(1.0 * (pts_src2[0] - pts_src1[0]) / (pts_sch2[0] - pts_sch1[0]))
    y_scale = abs(1.0 * (pts_src2[1] - pts_src1[1]) / (pts_sch2[1] - pts_sch1[1]))
    # 得到scale后需要对middle_point进行校正，并非特征点中点，而是映射矩阵的中点。
    sch_middle_point = int((pts_sch1[0] + pts_sch2[0]) / 2), int((pts_sch1[1] + pts_sch2[1]) / 2)
    middle_point[0] = middle_point[0] - int((sch_middle_point[0] - w / 2) * x_scale)
    middle_point[1] = middle_point[1] - int((sch_middle_point[1] - h / 2) * y_scale)
    middle_point[0] = max(middle_point[0], 0)  # 超出左边界取0  (图像左上角坐标为0,0)
    middle_point[0] = min(middle_point[0], w_s - 1)  # 超出右边界取w_s-1
    middle_point[1] = max(middle_point[1], 0)  # 超出上边界取0
    middle_point[1] = min(middle_point[1], h_s - 1)  # 超出下边界取h_s-1

    # 计算出来rectangle角点的顺序：左上角->左下角->右下角->右上角， 注意：暂不考虑图片转动
    # 超出左边界取0, 超出右边界取w_s-1, 超出下边界取0, 超出上边界取h_s-1
    x_min, x_max = int(max(middle_point[0] - (w * x_scale) / 2, 0)), int(
        min(middle_point[0] + (w * x_scale) / 2, w_s - 1))
    y_min, y_max = int(max(middle_point[1] - (h * y_scale) / 2, 0)), int(
        min(middle_point[1] + (h * y_scale) / 2, h_s - 1))
    # 目标矩形的角点按左上、左下、右下、右上的点序：(x_min,y_min)(x_min,y_max)(x_max,y_max)(x_max,y_min)
    pts = np.float32([[x_min, y_min], [x_min, y_max], [x_max, y_max], [x_max, y_min]]).reshape(-1, 1, 2)
    for npt in pts.astype(int).tolist():
        pypts.append(tuple(npt[0]))

    return middle_point, pypts, [x_min, x_max, y_min, y_max, w, h]


def _find_homography(sch_pts, src_pts):
    """多组特征点对时，求取单向性矩阵."""
    try:
        M, mask = cv2.findHomography(sch_pts, src_pts, cv2.RANSAC, 5.0)
    except Exception:
        import traceback
        traceback.print_exc()
        raise HomographyError("OpenCV error in _find_homography()...")
    else:
        if mask is None:
            raise HomographyError("In _find_homography(), find no mask...")
        else:
            return M, mask


def _target_error_check(w_h_range):
    """校验识别结果区域是否符合常理."""
    x_min, x_max, y_min, y_max, w, h = w_h_range
    tar_width, tar_height = x_max - x_min, y_max - y_min
    # 如果src_img中的矩形识别区域的宽和高的像素数＜5，则判定识别失效。认为提取区域待不可能小于5个像素。(截图一般不可能小于5像素)
    if tar_width < 5 or tar_height < 5:
        raise SiftResultCheckError("In src_image, Taget area: width or height < 5 pixel.")
    # 如果矩形识别区域的宽和高，与sch_img的宽高差距超过5倍(屏幕像素差不可能有5倍)，认定为识别错误。
    if tar_width < 0.2 * w or tar_width > 5 * w or tar_height < 0.2 * h or tar_height > 5 * h:
        raise SiftResultCheckError("Target area is 5 times bigger or 0.2 times smaller than sch_img.")


def _cal_sift_confidence(im_search, resize_img, rgb=False):
    if rgb:
        confidence = cal_rgb_confidence(resize_img, im_search)
    else:
        confidence = cal_ccoeff_confidence(resize_img, im_search)
    # sift的confidence要放水
    confidence = (1 + confidence) / 2
    return confidence
