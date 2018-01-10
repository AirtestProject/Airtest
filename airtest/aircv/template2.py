# coding=utf-8
"""
Template matching with higher level parameters like: focus/ignore.
"""
import cv2
import numpy as np
from airtest.utils.logger import get_logger
from .utils import generate_result, check_source_larger_than_search
from .template import find_template, _get_target_rectangle

LOGGING = get_logger(__name__)


def find_template2(im_search, im_source, ignore=None, focus=None, threshold=0.8, rgb=False):
    """带有mask的跨分辨率template图像匹配, 带有ignore-focus区域. find_all未启用."""
    if ignore:
        # 在截图中含有ignore区域时,在得到初步结果后需要进行可信度的更新:
        # 需要根据ignore区域生成匹配时的mask图像,注意需要进行跨分辨率的resize:
        # # 先生成原始im_search的mask，下面再进行resize
        origin_mask_img = _generate_mask_img(im_search, rect_list=ignore)
        ignore_mask = _resize_im_search(query, _get_resolution(source), target_img=origin_mask_img)
        # 根据缩放后的im_search、缩放后的mask图像，在im_source中获取初步识别区域的图像:
        result = template_with_mask(im_source, img_sch, ignore_mask)
        if result:
            target_img = _get_image_target_area(im_source, result["rectangle"])  # 截图在截屏中的目标区域
        else:
            return None

        if focus:
            # 截图既包含ignore, 又包含focus: 则在初始结果中进行focus区域的可信度计算:
            confidence = _cal_confi_only_in_focus(target_img, query, _get_resolution(source), resize_strategy)
        else:
            # 截图包含ignore区域，但是不包含focus,在初始结果内进行focus区域以外的图像进行可信度计算:
            confidence = _cal_confi_outside_ignore(target_img, query, _get_resolution(source), resize_strategy)
    else:
        # 没有ignore区域，但是有focus区域，先找到img_sch的最优匹配，然后计算focus区域可信度
        result = find_template(im_source, im_search, threshold=0, rgb=rgb)
        if not result:
            return None
        if focus:
            target_img = _get_image_target_area(im_source, result)
            confidence = _cal_confi_only_in_focus(target_img, query, _get_resolution(source), resize_strategy)
        else:
            # 既没有focus，也没有ignore，默认为基础的template匹配
            confidence = result.get("confidence", 0)

    # 校验可信度:
    if confidence < threshold:
        return None
    else:
        # 本方法中一直求取的是最佳解，因此此处result一定有效
        result['confidence'] = confidence
        return result


def template_with_mask(im_source, img_sch, ignore_mask):
    """mask-template方法. img_sch已进行缩放."""
    # 第一步：校验图像输入
    check_source_larger_than_search(im_source, img_sch, check_size_flag=True)

    # 第二步：进行匹配# template-TM_CCORR_NORMED 方法的结果矩阵:
    h, w = img_sch.shape[:2]
    data = np.zeros((h, w, 3), dtype=np.uint8)
    res = cv2.matchTemplate(im_source, img_sch, cv2.TM_CCORR_NORMED, data, ignore_mask)

    # 第三步: 直接获取最佳结果:  (暂时不支持find_all参数.)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    # 求取识别位置: 目标中心 + 目标区域:
    middle_point, rectangle = _get_target_rectangle(max_loc, w, h)
    confidence = max_val  # 注意这里是TM_CCORR_NORMED方法求出的值
    best_result = generate_result(middle_point, rectangle, confidence)

    return best_result


def _generate_mask_img(img_search, rect_list):
    """根据ignore区域生成mask图像."""
    # 建立与im_search同大小的空白图片模板
    h, w = img_search.shape[:-1]
    mask_img = np.zeros((h, w, 3), dtype=np.uint8)

    # 将全部区域涂白作为背景:
    cv2.rectangle(mask_img, (0, 0), (w, h), [255, 255, 255], -1)
    # 将ignore区域涂黑:
    for rect in rect_list:
        cv2.rectangle(mask_img, (rect[0], rect[1]), (rect[2], rect[3]), [0, 0, 0], -1)

    return mask_img


def _get_image_target_area(im_source, rectangle):
    """根据识别结果,提取出来识别区域."""
    # 获取截图起始位置: rectangle (left_top_pos, left_bottom_pos, right_bottom_pos, right_top_pos)
    (x_min, y_min), (x_max, y_max) = rectangle[0], rectangle[2]
    return im_source[y_min:y_max, x_min:x_max]


def _cal_confi_only_in_focus(target_img, query, src_resolution, resize_strategy):
    """将focus中的rect逐个进行可信度计算，再按面积加权平均."""
    # 提取参数:
    im_search = query.imread()
    focus_list = query.focus
    sch_resolution = query.resolution
    rgb = query.rgb

    # 注意:这里的focus小区域坐标均相对于原始的im_search，所以传入参数必须是原始大小的im_search
    # 第一步: 分别取出focus的区块，然后依次进行simple_tpl，求出可信度,并记录下面积
    area_list, confidence_list = [], []
    for focus_rect in focus_list:
        # focus_rect:[x_min,y_min,x_max,y_max], 截取focus小区块后，进行resize
        focus_area = im_search[focus_rect[1]:focus_rect[3], focus_rect[0]:focus_rect[2]]
        focus_area = _resize_im_search(query, src_resolution, target_img=focus_area)
        # 因为是加权概念-按比例,因此面积可以都使用resize前的
        area = (focus_rect[2] - focus_rect[0]) * (focus_rect[3] - focus_rect[1])
        # 计算focus单个区块的可信度:
        ret = find_template(target_img, focus_area, threshold=0, rgb=query.rgb)
        if ret:
            confidence = ret.get("confidence", 0)
        else:
            confidence = 0
        # 记录各个foux_area的相应数据
        area_list.append(area)
        # confidence_list.append(confidence)
        confidence_list.append((confidence + 1) / 2)

    # 第二步: 计算加权可信度
    return cal_average_confidence(confidence_list, area_list)


def cal_average_confidence(confidenceList, areaList):
    """根据areaList中的面积加权，计算confidenceList的加权平均confidence."""
    whole_area, whole_area_confi = 0, 0
    for i in range(len(areaList)):
        whole_area += areaList[i]
        whole_area_confi += areaList[i] * confidenceList[i]
    return whole_area_confi / whole_area


def _cal_confi_outside_ignore(target_img, query, src_resolution, resize_strategy):
    """将原始im_search分成细分块，将ignore区域外的细分块逐个进行可信度计算."""
    # 提取参数:
    im_search = query.imread()
    ignore_list = query.ignore
    sch_resolution = query.resolution
    rgb = query.rgb

    # 第一步: 获取细分块
    atom_rect_list = _generate_arom_rect_list(im_search, ignore_list)

    # 第二步: 计算各个细分块的面积和可信度
    area_list, confidence_list = [], []
    for atom_rect in atom_rect_list:
        # 不在ignore区域内的细分块，就执行可信度求取
        if not _atomrect_in_rectlist(atom_rect, ignore_list):
            # 如果发现atom_rect的宽度/高度为0，那么就直接跳过此区域的计算：
            if atom_rect[0] == atom_rect[2] or atom_rect[1] == atom_rect[3]:
                continue
            # atom_rect: [x_min,y_min,x_max,y_max], 截取ignore外小区块后，进行resize
            ignore_area = im_search[atom_rect[1]:atom_rect[3], atom_rect[0]:atom_rect[2]]
            ignore_area = _resize_im_search(query, src_resolution, target_img=ignore_area)
            # 因为是加权概念-按比例,因此面积可以都使用resize前的
            area = (atom_rect[2] - atom_rect[0]) * (atom_rect[3] - atom_rect[1])
            # 记录各个ignore_area的相应数据
            area_list.append(area)
            ret = find_template(target_img, ignore_area, threshold=0, rgb=query.rgb)
            if ret:
                confidence = ret.get("confidence", 0)
            else:
                confidence = 0
            # confidence_list.append(confidence)
            confidence_list.append((confidence + 1) / 2)

    # 第三步: 计算加权可信度
    return cal_average_confidence(confidence_list, area_list)


def _generate_arom_rect_list(im_search, rect_list):
    """通过rect_list得到当前所有的原子矩形."""
    h, w = im_search.shape[:2]
    x_list, y_list = [0], [0]

    def append_rule(element, ele_list):
        if element not in ele_list:
            ele_list.append(element)
        return ele_list

    for rect in rect_list:
        x_list = append_rule(rect[0], x_list)
        x_list = append_rule(rect[2], x_list)
        y_list = append_rule(rect[1], y_list)
        y_list = append_rule(rect[3], y_list)
    x_list.append(w - 1)
    y_list.append(h - 1)
    x_list, y_list = sorted(x_list), sorted(y_list)
    # 生成atom_rect_list:
    rect_num_x, rect_num_y = len(x_list) - 1, len(y_list) - 1
    atom_rect_list = []
    for j in range(rect_num_y):
        for i in range(rect_num_x):
            # 注意：此处rect的边界可能是有重叠的，暂不用考虑这个次要点
            atom_rect = [x_list[i], y_list[j], x_list[i + 1], y_list[j + 1]]
            atom_rect_list.append(atom_rect)

    return atom_rect_list


def _atomrect_in_rectlist(atom, rect_list):
    """判定细分块是否在mask区域内，从而确定是否需要计算可信度."""
    is_in_rect_list = False
    for rect in rect_list:
        if atom[0] >= rect[0] and atom[1] >= rect[1] and atom[2] <= rect[2] and atom[3] <= rect[3]:
            is_in_rect_list = True
            break
    return is_in_rect_list
