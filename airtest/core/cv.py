#!/usr/bin/env python
# -*- coding: utf-8 -*-

""""Airtest图像识别专用."""

import aircv
from airtest.core.helper import G, MoaPic, MoaText, log_in_func, logwrap, get_platform, platform
from airtest.core.settings import Settings as ST
from airtest.core.utils import TargetPos
from airtest.core.img_matcher import template_in_predicted_area, template_after_resize, mask_template_in_predicted_area, mask_template_after_resize, find_sift_in_predicted_area, _refresh_result_pos


def _get_search_img(pictarget):
    """获取搜索图像(cv2格式)."""
    if not isinstance(pictarget, MoaPic):
        pictarget = MoaPic(pictarget)

    return aircv.imread(pictarget.filepath)


def _get_screen_img(windows_hwnd=None):
    """获取屏幕图像."""
    last_capture_flag = KEEP_CAPTURE and (G.RECENT_CAPTURE is not None)
    screen = _snapshot(windows_hwnd=windows_hwnd) if not last_capture_flag else G.RECENT_CAPTURE

    return screen


@logwrap
@platform(on=["Android", "Windows", "IOS"])
def _snapshot(filename="screen.png", windows_hwnd=None):
    """设备截屏."""
    filename = "%(time)d.jpg" % {'time': time.time() * 1000}
    G.RECENT_CAPTURE_PATH = os.path.join(ST.LOG_DIR, ST.SAVE_SCREEN, filename)
    # write filepath into log:
    if ST.SAVE_SCREEN:
        log_in_func({"screen": os.path.join(ST.SAVE_SCREEN, filename)})
    # device snapshot: default not save
    if windows_hwnd:
        screen = DEVICE.snapshot_by_hwnd(filename=None, hwnd_to_snap=windows_hwnd)
    else:
        screen = DEVICE._snapshot_impl(filename=None)
    # 使用screen更新RECENT_CAPTURE
    G.RECENT_CAPTURE = screen
    return screen


@logwrap
def _loop_find(pictarget, timeout=ST.FIND_TIMEOUT, threshold=None, interval=0.5, intervalfunc=None, find_all=False):
    """keep looking for pic until timeout, execute intervalfunc if pic not found."""
    G.LOGGING.info("Try finding:\n%s", pictarget)
    # 结果可信阈值优先取脚本参数传入的阈值，其次是utils.py中设置的，再次是设置的默认阈值
    threshold = getattr(pictarget, "threshold") or threshold or ST.THRESHOLD

    start_time = time.time()
    while True:
        # 获取截图所在的设备操作位置: (注意截屏保存的时机.)
        ret = _get_img_match_result(pictarget, threshold, find_all=find_all)
        if ret:
            aircv.imwrite(G.RECENT_CAPTURE_PATH, screen)
            return ret

        if intervalfunc is not None:
            aircv.imwrite(G.RECENT_CAPTURE_PATH, screen)
            intervalfunc()
        for name, func in WATCHER.items():
            G.LOGGING.info("exec watcher %s", name)
            func()

        # 超时则raise，未超时则进行下次循环:
        if (time.time() - start_time) > timeout:
            aircv.imwrite(G.RECENT_CAPTURE_PATH, screen)
            raise MoaNotFoundError('Picture %s not found in screen' % pictarget)
        else:
            time.sleep(interval)
            continue


def _get_img_match_result(pictarget, threshold, find_all=False):
    """求取目标操作位置."""
    # 第一步: 获取截图和截屏,以及偏移位置
    # 兼容以前的rect参数（指定寻找区域），如果脚本层仍然有rect参数，传递给find_inside:
    if pictarget.rect and not pictarget.find_inside:
        rect = pictarget.rect
        pictarget.find_inside = [rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]]

    # 获取截图
    im_sch = _get_search_img(pictarget)

    # 获取截屏
    if not pictarget.whole_screen and get_platform() == "Windows" and DEVICE.handle:
        # win平非全屏识别、且指定句柄的情况:使用hwnd获取有效图像
        screen = _get_screen_img(windows_hwnd=DEVICE.handle)
        # 获取窗口相对于屏幕坐标系的坐标(用于操作坐标的转换)
        wnd_pos = DEVICE.get_wnd_pos_by_hwnd(DEVICE.handle)
    else:
        wnd_pos = None  # 没有所谓的窗口偏移，设为None
        # 其他情况：手机回放或者windows全屏回放时，使用之前的截屏方法( 截屏offset为0 )
        screen = _get_screen_img()
        # 暂时只在全屏截取时才启用find_outside，主要关照IDE调试脚本情形
        screen = mask_image(screen, pictarget.find_outside)
    # 检查截屏:
    screen = _check_screen(screen)
    if not screen:
        return None

    # 第二步：图像识别，并求取实际操作位置
    return _img_match(screen, im_sch, pictarget, threshold, find_all, wnd_pos)


def _check_screen(screen):
    """检查本次截屏."""
    # 如果截屏有问题，直接返回None
    if not screen.any():
        G.LOGGING.warning("Bad screen capture, skip cv matching")
        return None
    # 如果指定调试状态，展示图像识别时的截屏图片：
    if ST.DEBUG:
        aircv.show(screen)

    return screen


def _img_match(screen, im_sch, pictarget, threshold, find_all, wnd_pos):
    """获取图像识别结果，并求取操作位置."""
    # find_inside参数: 在寻找区得到结果后进行offset校正。为None则offset=[0, 0].
    screen, offset = aircv.crop_image(screen, pictarget.find_inside)
    # 先获取初始的图像识别结果:
    cv_ret = _cv_match(screen, im_sch, threshold, pictarget, find_all)
    G.LOGGING.debug("match result: %s", cv_ret)
    # 矫正识别区域结果，并处理偏移target_pos:
    ret_pos = _calibrate_ret(cv_ret, pictarget, offset, wnd_pos)

    return ret_pos


def _calibrate_ret(ret, pictarget, offset=None, wnd_pos=None):
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
            ret_pos = TargetPos().getXY(one_ret, pictarget.target_pos)
            ret_pos_list.append(ret_pos)
        return ret_pos_list
    else:
        # 非find_all模式，返回的是一个dict，则正常返回即可
        ret = cal_ret(ret, offset, wnd_pos)
        ret_pos = TargetPos().getXY(ret, pictarget.target_pos)
        return ret_pos


def _cv_match(screen, im_sch, threshold, pictarget, find_all):
    """根据传入的参数,进行图像识别."""
    # 取出匹配相关的参数:
    rgb = ST.STRICT_RET
    sch_resolution = pictarget.resolution
    src_resolution = ST.SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
    design_resolution = ST.DESIGN_RESOLUTION
    resize_strategy = ST.RESIZE_METHOD
    ignore, focus = pictarget.ignore, pictarget.focus
    op_pos = pictarget.record_pos

    try:
        ret = _do_match(screen, im_sch, op_pos, threshold, rgb, sch_resolution, src_resolution, design_resolution, ignore, focus, resize_strategy)
    except aircv.Error:
        ret = None
    except Exception as err:
        traceback.print_exc()
        ret = None

    # 将识别结果写入log文件:
    log_in_func({"cv": ret})

    return ret


def _do_match(screen, im_sch, op_pos, threshold, rgb, sch_resolution, src_resolution, design_resolution, ignore, focus, resize_strategy):
    """调用功能函数，执行图像匹配."""
    ret = None
    if ignore or focus:
        # 带有mask的模板匹配方法:
        G.LOGGING.debug("method: template match (with ignore & focus rects)")
        ret_in_pre = mask_template_in_predicted_area(screen, im_sch, op_pos, threshold=threshold, rgb=rgb, sch_resolution=sch_resolution, src_resolution=src_resolution, design_resolution=design_resolution, ignore=ignore, focus=focus, resize_strategy=resize_strategy)
        ret = ret_in_pre or mask_template_after_resize(screen, im_sch, threshold=threshold, rgb=rgb, sch_resolution=sch_resolution, src_resolution=src_resolution, design_resolution=design_resolution, ignore=ignore, focus=focus, resize_strategy=resize_strategy)
    else:
        # 根据cv_strategy配置进行匹配:
        for method in ST.CVSTRATEGY:
            if method == "tpl":
                # 普通的模板匹配: (默认pre，其次全屏)
                G.LOGGING.debug("method: template match")
                ret_in_pre = template_in_predicted_area(screen, im_sch, op_pos, threshold=threshold, rgb=rgb, sch_resolution=sch_resolution, src_resolution=src_resolution, design_resolution=design_resolution, resize_strategy=resize_strategy, find_all=find_all)
                ret = ret_in_pre or template_after_resize(screen, im_sch, threshold=threshold, rgb=rgb, sch_resolution=sch_resolution, src_resolution=src_resolution, design_resolution=design_resolution, resize_strategy=resize_strategy, find_all=find_all)
            elif method == "sift":
                # sift匹配，默认pre，其次全屏
                G.LOGGING.debug("method: sift match")
                ret_in_pre = find_sift_in_predicted_area(screen, im_sch, op_pos, src_resolution=src_resolution, threshold=threshold, rgb=rgb)
                ret = ret_in_pre or aircv.find_sift(screen, im_sch, threshold=threshold, rgb=rgb)
            else:
                G.LOGGING.warning("skip method in %s  CV_STRATEGY", method)

            # 使用某个识别方法找到后，就直接返回，不再继续循环下去:
            if ret:
                return ret

    return ret
