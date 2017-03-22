#!/usr/bin/env python
# -*- coding: utf-8 -*-

""""Airtest图像识别专用."""
import os
import cv2
import numpy as np
import traceback
import time
import aircv
from aircv.error import *  # noqa
from aircv.template import find_all_template, find_template, _get_target_rectangle
from aircv.sift import find_sift
from aircv.utils import checkImageParamInput, generate_result

from airtest.core.error import *  # noqa
from airtest.core.helper import G, MoaPic, MoaScreen, MoaText, log_in_func, logwrap, get_platform, platform
from airtest.core.settings import Settings as ST
from airtest.core.utils import TargetPos


@logwrap
@platform(on=["Android", "Windows", "IOS"])
def device_snapshot(filename="screen.png", windows_hwnd=None):
    """设备截屏."""
    filename = "%(time)d.jpg" % {'time': time.time() * 1000}
    G.RECENT_CAPTURE_PATH = os.path.join(ST.LOG_DIR, ST.SCREEN_DIR, filename)
    # write filepath into log:
    if ST.SCREEN_DIR:
        log_in_func({"screen": os.path.join(ST.SCREEN_DIR, filename)})
    # device snapshot: default not save
    if windows_hwnd:
        screen = G.DEVICE.snapshot_by_hwnd(filename=None, hwnd_to_snap=windows_hwnd)
    else:
        screen = G.DEVICE._snapshot_impl(filename=None)
    # 使用screen更新RECENT_CAPTURE
    G.RECENT_CAPTURE = screen
    return screen


@logwrap
def loop_find(query, timeout=ST.FIND_TIMEOUT, interval=0.5, intervalfunc=None, threshold=None, find_all=False):
    """keep looking for pic until timeout, execute intervalfunc if pic not found."""
    G.LOGGING.info("Try finding:\n%s", query)

    # 优先用指定版threshold(如assert_exists)，其次用脚本中传来的threshold
    query.threshold = threshold or query.threshold
    # 优先使用指定的find_all参数，比如find_all()指定find_all=True
    query.find_all = find_all or query.find_all

    start_time = time.time()
    while True:
        # 获取截图所在的设备操作位置: (注意截屏保存的时机.)
        source = _get_source(query)

        if source.screen is None:
            ret = None
        else:
            ret = _get_img_match_result(source, query)

        if ret:
            aircv.imwrite(G.RECENT_CAPTURE_PATH, source.screen)
            return ret

        if intervalfunc is not None:
            aircv.imwrite(G.RECENT_CAPTURE_PATH, source.screen)
            intervalfunc()
        for name, func in G.WATCHER.items():
            G.LOGGING.info("exec watcher %s", name)
            func()

        # 超时则raise，未超时则进行下次循环:
        if (time.time() - start_time) > timeout:
            aircv.imwrite(G.RECENT_CAPTURE_PATH, source.screen)
            raise MoaNotFoundError('Picture %s not found in screen' % query)
        else:
            time.sleep(interval)
            continue


def no_resize(w_a, h_a, resolution_a, resolution_b, design_resolution):
    """无缩放策略."""
    return w_a, h_a


def cocos_min_strategy(w, h, sch_resolution, src_resolution, design_resolution):
    """图像缩放规则: COCOS中的MIN策略."""
    # 输入参数: w-h待缩放图像的宽高，sch_resolution为待缩放图像的来源分辨率
    #           src_resolution 待适配屏幕的分辨率  design_resolution 软件的设计分辨率
    # 需要分别算出对设计分辨率的缩放比，进而算出src\sch有效缩放比。
    if design_resolution == []:
        design_resolution = ST.DESIGN_RESOLUTION
    scale_sch = min(1.0 * sch_resolution[0] / design_resolution[0], 1.0 * sch_resolution[1] / design_resolution[1])
    scale_src = min(1.0 * src_resolution[0] / design_resolution[0], 1.0 * src_resolution[1] / design_resolution[1])
    scale = scale_src / scale_sch
    h_re, w_re = int(h * scale), int(w * scale)
    return w_re, h_re


def _get_search_img(query):
    """获取搜索图像(cv2格式)."""
    if not isinstance(query, MoaPic):
        query = MoaPic(query)

    return aircv.imread(query.filepath)


def _get_device_screen(windows_hwnd=None):
    """获取设备屏幕图像."""
    if G.KEEP_CAPTURE and (G.RECENT_CAPTURE is not None):
        screen = G.RECENT_CAPTURE
    else:
        screen = device_snapshot(windows_hwnd=windows_hwnd)

    return screen


def _get_source(query):
    """求取图像匹配的截屏数据类."""
    # 第一步: 获取截屏
    if not query.whole_screen and get_platform() == "Windows" and G.DEVICE.handle:
        # win平非全屏识别、且指定句柄的情况:使用hwnd获取有效图像
        screen = _get_device_screen(windows_hwnd=G.DEVICE.handle)
        # 获取窗口相对于屏幕坐标系的坐标(用于操作坐标的转换)
        wnd_pos = G.DEVICE.get_wnd_pos_by_hwnd(G.DEVICE.handle)
    else:
        wnd_pos = None  # 没有所谓的窗口偏移，设为None
        # 其他情况：手机回放或者windows全屏回放时，使用之前的截屏方法( 截屏offset为0 )
        screen = _get_device_screen()
        # 暂时只在全屏截取时才启用find_outside，主要关照IDE调试脚本情形
        screen = aircv.mask_image(screen, query.find_outside)

    # 检查截屏:
    if not screen.any():
        G.LOGGING.warning("Bad screen capture, check if screen is clocked !")
        screen, img_src, offset = None, None, None
    else:
        # 调试状态下，展示图像识别时的截屏图片：
        if ST.DEBUG and screen is not None:
            aircv.show(screen)

        # 第二步: 封装截屏 (将offset和screen和wnd_pos都封装进去？？)——现在还没有封装哦~
        img_src, offset = aircv.crop_image(screen, query.find_inside)

    src_resolution = ST.SRC_RESOLUTION or G.DEVICE.getCurrentScreenResolution()

    return MoaScreen(screen=screen, img_src=img_src, offset=offset, wnd_pos=wnd_pos, src_resolution=src_resolution)


def _get_img_match_result(source, query):
    """求取目标操作位置."""
    # 第一步: 图像识别
    try:
        cv_ret = _cv_match(source, query)
    except aircv.Error:
        cv_ret = None
    except Exception as err:
        traceback.print_exc()
        cv_ret = None

    G.LOGGING.debug("match result: %s", cv_ret)
    # 将识别结果写入log文件:
    log_in_func({"cv": cv_ret})

    # 第二步: 矫正识别区域结果，并处理偏移target_pos，并求取实际操作位置
    offset, wnd_pos = getattr(source, "offset"), getattr(source, "wnd_pos")
    ret_pos = _calibrate_ret(cv_ret, query, offset, wnd_pos)

    return ret_pos


def _cv_match(source, query):
    """调用功能函数，执行图像匹配."""
    ret = None
    if query.ignore or query.focus:
        # 带有mask的模板匹配方法:
        G.LOGGING.debug("method: template match (with ignore & focus rects)")
        ret_in_pre = mask_template_in_predicted_area(source, query)
        ret = ret_in_pre or mask_template_after_resize(source, query)
    else:
        # 根据cv_strategy配置进行匹配:
        for method in ST.CVSTRATEGY:
            if method == "tpl":
                # 普通的模板匹配: (默认pre，其次全屏)
                G.LOGGING.debug("method: template match")
                ret_in_pre = template_in_predicted_area(source, query)
                ret = ret_in_pre or template_after_resize(source, query)
            elif method == "sift":
                # sift匹配，默认pre，其次全屏
                G.LOGGING.debug("method: sift match")
                ret_in_pre = find_sift_in_predicted_area(source, query)
                if not ret_in_pre:
                    img_src, img_sch = source.img_src, _get_search_img(query)
                    ret_in_pre = aircv.find_sift(img_src, img_sch, threshold=query.threshold, rgb=query.rgb)
            else:
                G.LOGGING.warning("skip method in %s  CV_STRATEGY", method)

            # 使用某个识别方法找到后，就直接返回，不再继续循环下去:
            if ret:
                return ret

    return ret


def _calibrate_ret(ret, query, offset=None, wnd_pos=None):
    """进行识别结果进行整体偏移矫正,以及target_pos的矫正,返回点击位置."""
    def cal_ret(one_ret, offset, wnd_pos):
        if offset:
            one_ret = _refresh_result_pos(one_ret, offset)
        if wnd_pos:
            _log_in_func({"wnd_pos": wnd_pos})
            one_ret = _refresh_result_pos(one_ret, wnd_pos)
        # 返回识别区域校正后的结果:
        return one_ret

    if not ret:
        # 没找到结果，直接返回None,以便_loop_find执行未找到的逻辑
        return None
    elif isinstance(ret, list):
        # 如果是find_all模式，则找到的是一个结果列表，处理后返回ret_pos_list
        ret_pos_list = []
        for one_ret in ret:  # 对结果列表中的每一个结果都进行一次结果偏移的处理
            one_ret = cal_ret(one_ret, offset, wnd_pos)
            # 这个是脚本语句的target_pos的点击偏移处理:
            ret_pos = TargetPos().getXY(one_ret, query.target_pos)
            ret_pos_list.append(ret_pos)
        return ret_pos_list
    else:
        # 非find_all模式，返回的是一个dict，则正常返回即可
        ret = cal_ret(ret, offset, wnd_pos)
        ret_pos = TargetPos().getXY(ret, query.target_pos)
        return ret_pos


def template_in_predicted_area(source, query):
    '''带区域预测的模板匹配.'''
    # 第一步：定位im_source中的预测区域:
    img_src, left_top_pos = _get_predicted_area(source, query)
    source.img_src = img_src  # 更新待识别图像为预测区域的图像

    # 第二步：在预测区域内，进行跨分辨率识别，调用find_template_after_resize:
    pre_result = template_after_resize(source, query)

    # 第三步：对结果进行位置校正:
    return _refresh_result_pos(pre_result, left_top_pos) if pre_result else None


def template_after_resize(source, query):
    '''跨分辨率template图像匹配.'''
    # 第一步：先对im_search进行跨分辨率适配resize
    img_sch = _resize_im_search(query, source.src_resolution)

    # 第二步：图像识别得到结果(可选择寻找结果集合)
    if query.find_all:
        return find_all_template(source.img_src, img_sch, threshold=query.threshold, rgb=query.rgb)
    else:
        return find_template(source.img_src, img_sch, threshold=query.threshold, rgb=query.rgb)


def find_sift_in_predicted_area(source, query):
    '''在预测区域内进行sift查找.'''
    # 提取截图
    im_search = _get_search_img(query)
    # 第一步：定位im_source中的预测区域:
    img_src, left_top_pos = _get_predicted_area(source, query)

    # 第二步：在预测区域内进行基于sift的识别，调用find_sift:
    if not img_src.any():
        pre_result = None
    else:
        pre_result = find_sift(img_src, im_search, threshold=query.threshold, rgb=query.rgb)

    # 第三步：对结果进行位置校正:
    return _refresh_result_pos(pre_result, left_top_pos) if pre_result else None


def _resize_im_search(query, src_resolution, target_img=None):
    """模板匹配中，将输入的截图适配成 等待模板匹配的截图."""
    # 提取参数:
    if target_img is not None:
        im_search = target_img
    else:
        im_search = _get_search_img(query)
    sch_resolution = query.resolution
    # src_resolution = source.src_resolution
    design_resolution = ST.DESIGN_RESOLUTION

    # 如果分辨率一致，则不需要进行im_search的适配:
    if tuple(sch_resolution) == tuple(src_resolution):
        return im_search
    else:
        # 分辨率不一致则进行适配，默认使用cocos_min_strategy:
        h, w = im_search.shape[:2]
        resize_strategy = ST.RESIZE_METHOD or cocos_min_strategy
        w_re, h_re = resize_strategy(w, h, sch_resolution, src_resolution, design_resolution)

        # 调试代码: 输出调试信息.
        G.LOGGING.debug("cross resolution: (%s, %s)=>(%s, %s),  resize: %s=>%s" % (w, h, w_re, h_re, sch_resolution, src_resolution))

        # 进行图片缩放:
        resized_im_search = cv2.resize(im_search, (w_re, h_re))
        return resized_im_search


def _get_predicted_area(source, query):
    """从im_source中提取出预测区域."""
    # 提取预测参数:
    im_source = source.img_src
    src_resolution = source.src_resolution
    op_pos = query.record_pos
    radius_x, radius_y = ST.RADIUS_X, ST.RADIUS_Y

    # 预测操作位置: (按照比例进行点预测) clk_x, clk_y是规划为比例的
    clk_x, clk_y = op_pos
    # 如果没有传递
    if src_resolution:
        res_x, res_y = src_resolution
    else:
        res_y, res_x = im_source.shape[:2]
    prePos_x, prePos_y = clk_x * res_x + 0.5 * res_x, clk_y * res_x + 0.5 * res_y

    def safe_xy(val, min_val, max_val):
        return min(max(min_val, val), max_val)

    # 再以预测点为中心，进行范围提取:
    start_x = int(safe_xy(prePos_x - radius_x, 0, res_x - 1))
    end_x = int(safe_xy(prePos_x + radius_x, 0, res_x - 1))
    start_y = int(safe_xy(prePos_y - radius_y, 0, res_y - 1))
    end_y = int(safe_xy(prePos_y + radius_y, 0, res_y - 1))

    # 调试代码: 输出调试信息.
    G.LOGGING.debug("predict rect:  X (%(start_x)s:%(end_x)s)   Y (%(start_y)s:%(end_y)s)" % {"start_x": start_x, "end_x":end_x, "start_y": start_y, "end_y": end_y})

    # 如果发现预测区域完全在图像外，预测区域将只剩下一条像素，预测失败，直接raise:
    if start_x == end_x or start_y == end_y:
        raise PredictAreaNoneError("Predict has just one pixel !")

    # 预测区域正常，则截取预测区域，并将预测区域在源图像中的位置一并返回:
    img_src = im_source[start_y:end_y, start_x:end_x]
    left_top_pos = (start_x, start_y)

    return img_src, left_top_pos


def _pos_fix(ret, left_top_pos):
    """用于在预测区(给出了其左上角点)查找成功后，进行最终的结果偏移对齐."""
    left_top_x, left_top_y = left_top_pos
    # 在预测区域内进行图像查找时，需要转换到整张图片内的坐标，再进行左上角的位置校准:
    # 进行识别中心result的偏移:
    result_pos = list(ret.get('result'))
    result = [i + j for (i, j) in zip(left_top_pos, result_pos)]
    # 进行识别区域rectangle的偏移:
    rectangle = []
    for point in ret.get('rectangle'):
        tmpoint = [i + j for (i, j) in zip(left_top_pos, point)]  # 进行位置相对left_top_pos进行偏移
        rectangle.append(tuple(tmpoint))
    # 重置偏移后的识别中心、识别区域:
    ret['result'], ret['rectangle'] = tuple(result), tuple(rectangle)

    return ret


def _refresh_result_pos(pre_result, left_top_pos):
    """根据所给的偏移坐标，更新识别结果."""
    left_top_x, left_top_y = left_top_pos
    # 分别针对单个和多个结果的情况，进行指定
    if isinstance(pre_result, dict):
        result = _pos_fix(pre_result, left_top_pos)
    elif isinstance(pre_result, list):
        result = [_pos_fix(item, left_top_pos) for item in pre_result]

    return result


def mask_template_in_predicted_area(source, query):
    """带预测区域的mask-template."""
    # 第一步: 定位im_source中的预测区域:
    img_src, left_top_pos = _get_predicted_area(source, query)
    source.img_src = img_src  # 更新待识别图像为预测区域的图像

    # 第二步：在预测区域内，进行跨分辨率识别，调用mask_template_after_resize
    pre_result = mask_template_after_resize(source, query)

    # 第三步：对结果进行位置校正:
    return _refresh_result_pos(pre_result, left_top_pos) if pre_result else None


def mask_template_after_resize(source, query):
    """带有mask的跨分辨率template图像匹配, 带有ignore-focus区域. find_all未启用."""
    im_search = _get_search_img(query)
    im_source = source.img_src
    ignore, focus = query.ignore, query.focus
    resize_strategy = ST.RESIZE_METHOD or cocos_min_strategy

    # 第一步：对im_search进行跨分辨率适配resize
    img_sch = _resize_im_search(query, source.src_resolution)

    # 第二步：ignore-focus参数的处理
    if ignore:
        # 在截图中含有ignore区域时,在得到初步结果后需要进行可信度的更新:
        # 需要根据ignore区域生成匹配时的mask图像,注意需要进行跨分辨率的resize:
        # # 先生成原始im_search的mask，下面再进行resize
        origin_mask_img = _generate_mask_img(im_search, rect_list=ignore)
        ignore_mask = _resize_im_search(query, source.src_resolution, target_img=origin_mask_img)
        # 根据缩放后的im_search、缩放后的mask图像，在im_source中获取初步识别区域的图像:
        result = template_with_mask(im_source, img_sch, ignore_mask)
        target_img = _get_image_target_area(im_source, result)  # 截图在截屏中的目标区域

        if focus:
            # 截图既包含ignore, 又包含focus: 则在初始结果中进行focus区域的可信度计算:
            confidence = _cal_confi_only_in_focus(target_img, query, source.src_resolution, resize_strategy)
        else:
            # 截图包含ignore区域，但是不包含focus,在初始结果内进行focus区域以外的图像进行可信度计算:
            confidence = _cal_confi_outside_ignore(target_img, query, source.src_resolution, resize_strategy)
    else:
        # 没有ignore区域，但是有focus区域，先找到img_sch的最优匹配，然后计算focus区域可信度
        if focus:
            result = find_template(im_source, img_sch, threshold=0, rgb=rgb)
            target_img = _get_image_target_area(im_source, result)
            confidence = _cal_confi_only_in_focus(target_img, query, source.src_resolution, resize_strategy)
        else:
            # 既没有focus，也没有ignore，默认为基础的template匹配
            result = find_template(im_source, img_sch, threshold=0, rgb=rgb)
            confidence = result.get("confidence", 0)

    # 校验可信度:
    if confidence < query.threshold:
        return None
    else:
        # 本方法中一直求取的是最佳解，因此此处result一定有效
        result['confidence'] = confidence
        return result


def template_with_mask(im_source, img_sch, ignore_mask):
    """mask-template方法. img_sch已进行缩放."""
    # 第一步：校验图像输入
    checkImageParamInput(im_source, img_sch, check_size_flag=True)

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


def _generate_mask_img(img_search, rect_list=[]):
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


def _get_image_target_area(im_source, result={}):
    """根据识别结果,提取出来识别区域."""
    rectangle = result.get("rectangle", [])
    # 校验结果矩阵:
    if not rectangle:
        raise InvalidCropTargetError("Cannot crop im_source by a invalid result!")
    # 获取截图起始位置: rectangle (left_top_pos, left_bottom_pos, right_bottom_pos, right_top_pos)
    (x_min, y_min), (x_max, y_max) = rectangle[0], rectangle[2]

    return im_source[y_min:y_max, x_min:x_max]


def _cal_confi_only_in_focus(target_img, query, src_resolution, resize_strategy):
    """将focus中的rect逐个进行可信度计算，再按面积加权平均."""
    # 提取参数:
    im_search = _get_search_img(query)
    focus_list = query.focus
    sch_resolution = query.resolution
    rgb = query.rgb
    design_resolution = ST.DESIGN_RESOLUTION

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
        ret = find_template(target_img, focus_area, threshold=0, rgb=rgb)
        confidence = ret.get("confidence", 0)
        # 记录各个foux_area的相应数据
        area_list.append(area)
        confidence_list.append(confidence)

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
    im_search = _get_search_img(query)
    ignore_list = query.ignore
    sch_resolution = query.resolution
    rgb = query.rgb
    design_resolution = ST.DESIGN_RESOLUTION

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
            ret = find_template(target_img, ignore_area, threshold=0, rgb=rgb)
            confidence = ret.get("confidence", 0)
            confidence_list.append(confidence)

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
