# -*- coding: utf-8 -*-
from airtest.core.helper import G, MoaPic, MoaText, log_in_func, logwrap, get_platform, platform
from airtest.core.settings import Settings as ST
from airtest.core.utils import TargetPos
# import aircv


def _get_search_img(pictarget):
    '''根据图片属性获取: 截图(picdata)'''
    if isinstance(pictarget, MoaText):
        # moaText暂时没用了，截图太方便了，以后再考虑文字识别
        # pil_2_cv2函数有问题，会变底色，后续修
        # picdata = aircv.pil_2_cv2(pictarget.img)
        pictarget.img.save("text.png")
        picdata = aircv.imread("text.png")
    elif isinstance(pictarget, MoaPic):
        picdata = aircv.imread(pictarget.filepath)
    else:
        pictarget = MoaPic(pictarget)
        picdata = aircv.imread(pictarget.filepath)
    return picdata


def _get_screen_img(windows_hwnd=None):
    # 如果是KEEP_CAPTURE, 就取上次的截屏，否则重新截屏
    if KEEP_CAPTURE and RECENT_CAPTURE is not None:
        screen = RECENT_CAPTURE
    else:
        screen = _snapshot(windows_hwnd=windows_hwnd)
    return screen


def _find_pic(screen, picdata, threshold=ST.THRESHOLD, target_pos=TargetPos.MID, record_pos=[], sch_resolution=[], templateMatch=False, rgb=False):
    try:
        if templateMatch is True:
            LOGGING.debug("method: template match..")
            device_resolution = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
            ret = aircv.find_template_after_resize(screen, picdata, sch_resolution=sch_resolution, src_resolution=device_resolution, design_resolution=DESIGN_RESOLUTION, threshold=0.6, resize_method=RESIZE_METHOD, check_color=CHECK_COLOR, rgb=rgb)
        # 参数要求：点击位置press_pos=[x,y]，搜索图像截屏分辨率sch_pixel=[a1,b1]，源图像截屏分辨率src_pixl=[a2,b2],如果参数输入不全，不调用区域预测：
        elif not record_pos:
            LOGGING.debug("method: sift in whole screen..")
            ret = aircv.find_sift(screen, picdata)
        # 三个要求的参数均有输入时，加入区域预测部分：
        else:
            LOGGING.debug("method: sift in predicted area..")
            _pResolution = DEVICE.getCurrentScreenResolution()
            ret = aircv.find_sift_by_pre(screen, picdata, _pResolution, record_pos[0], record_pos[1])
    except aircv.Error:
        ret = None
    except Exception as err:
        traceback.print_exc()
        ret = None
    log_in_func({"cv": ret})
    if not ret:
        return None
    if threshold and ret["confidence"] < threshold:
        return None
    return ret


def _find_pic_by_strategy(screen, picdata, threshold, pictarget, strict_ret=False):
    '''图像搜索时，按照CVSTRATEGY的顺序，依次使用不同方法进行图像搜索'''
    ret = None
    for st in CVSTRATEGY:
        if st == "siftpre" and getattr(pictarget, "record_pos"):
            # 预测区域sift匹配
            ret = _find_pic(screen, picdata, threshold=threshold, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos)
            LOGGING.debug("sift pre  result: %s", ret)
        elif st == "siftnopre":
            # 全局sift
            ret = _find_pic(screen, picdata, threshold=threshold, target_pos=pictarget.target_pos)
            LOGGING.debug("sift result: %s", ret)
        elif st == "tpl" and getattr(pictarget, "resolution"):
            # 缩放后的模板匹配
            ret = _find_pic(screen, picdata, threshold=threshold, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos, sch_resolution=pictarget.resolution, templateMatch=True, rgb=pictarget.rgb)
            LOGGING.debug("tpl result: %s", ret)
        else:
            LOGGING.warning("skip CV_STRATEGY:%s", st)
        # 找到一个就返回
        if ret is None:
            continue
        # cal_strict_confi进行进一步计算精确相似度
        strict_ret = strict_ret or STRICT_RET
        if strict_ret:
            ret = aircv.cal_strict_confi(screen, picdata, ret, threshold=threshold)
        if ret is not None:
            return ret
    return ret

def _find_pic_with_ignore_focus(screen, picdata, threshold, pictarget):
    '''图像搜索时，按照CVSTRATEGY的顺序，依次使用不同方法进行图像搜索'''
    ret = None
    try:
        # 缩放后的模板匹配
        LOGGING.debug("method: template match (with ignore & focus rects) ..")
        device_resolution = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
        ret = aircv.template_focus_ignore_after_resize(screen, picdata, sch_resolution=pictarget.resolution, src_resolution=device_resolution, design_resolution=[960, 640], threshold=0.6, ignore=pictarget.ignore, focus=pictarget.focus, resize_method=RESIZE_METHOD)
        # record_pos = pictarget.record_pos
        # ret = aircv.tpl_focus_ignore_after_resize_with_pre(screen, picdata, record_pos[0], record_pos[1], sch_resolution=pictarget.resolution, src_resolution=device_resolution, design_resolution=[960, 640], threshold=0.6, ignore=pictarget.ignore, focus=pictarget.focus, resize_method=RESIZE_METHOD)
    except aircv.Error:
        ret = None
    except Exception as err:
        traceback.print_exc()
        ret = None

    log_in_func({"cv": ret})

    if threshold and ret:
        if ret["confidence"] < threshold:
            ret = None
    LOGGING.debug("tpl result (with ignore & focus rects): %s", ret)
    return ret


def _find_all_pic(screen, picdata, threshold, pictarget, strict_ret=False):
    '''直接使用单个方法进行寻找(find_template_after_resize).'''
    ret_list = []
    if getattr(pictarget, "resolution"):
        try:
            # 缩放后的模板匹配
            LOGGING.debug("method: template match (find_all) ..")
            device_resolution = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
            ret_list = aircv.find_template_after_resize(screen, picdata, sch_resolution=pictarget.resolution, src_resolution=device_resolution, design_resolution=[960, 640], threshold=0.6, resize_method=RESIZE_METHOD, check_color=CHECK_COLOR, find_all=True)
        except aircv.Error:
            ret_list = []
        except Exception as err:
            traceback.print_exc()
            ret_list = []

        log_in_func({"cv": ret_list})

        if threshold and ret_list:
            nice_ret_list = []
            for one_ret in ret_list:  # 将ret列表内低于阈值的结果都去掉
                if one_ret["confidence"] >= threshold:
                    nice_ret_list.append(one_ret)
            ret_list = nice_ret_list
        LOGGING.debug("tpl result_list (find_all): %s", ret_list)
        return ret_list
    else:
        LOGGING.warning("please check script : there is no 'resolution' param.")
        return ret_list    # 走了else逻辑，ret_list为空


@logwrap
def _loop_find(pictarget, timeout=ST.FIND_TIMEOUT, threshold=None, interval=0.5, intervalfunc=None, find_all=False):
    '''
        keep looking for pic until timeout, execute intervalfunc if pic not found.
    '''
    LOGGING.info("Try finding:\n%s", pictarget)
    picdata = _get_search_img(pictarget)
    # 兼容以前的rect参数（指定寻找区域），如果脚本层仍然有rect参数，传递给find_inside:
    if pictarget.rect and not pictarget.find_inside:
        rect = pictarget.rect
        pictarget.find_inside = [rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]]
    # 结果可信阈值优先取脚本传入的，其次是utils.py中设置的，再次是moa默认阈值
    threshold = getattr(pictarget, "threshold") or threshold or THRESHOLD
    start_time = time.time()
    while True:
        wnd_pos = None
        # 未指定whole_screen、win平台回放、且指定了handle 的情况下：使用hwnd获取有效图像
        if not pictarget.whole_screen and get_platform() == "Windows" and DEVICE.handle:
            screen = _get_screen_img(windows_hwnd=DEVICE.handle)
            wnd_pos = DEVICE.get_wnd_pos_by_hwnd(DEVICE.handle)  # 获取窗口相对于屏幕坐标系的坐标(用于操作坐标的转换)
        # 其他情况：手机回放，或者windows全屏回放时，使用之前的截屏方法( 截屏offset为0 )
        else:
            screen = _get_screen_img()
            # 暂时只在全屏截取时才执行find_outside，主要关照IDE调试脚本情形
            screen = mask_image(screen, pictarget.find_outside)

        if screen.any():
            # *************************************************************************************
            # 先不加通用回放时的find_outside，稍后根据具体需求，仔细考虑如何添加：
            # find_outside = find_outside or FIND_OUTSIDE
            # if find_outside:  # 在截屏的find_outside区域外寻找(win下指定了hwnd则是相对窗口的区域)
            #     screen = mask_image(screen, find_outside)
            # *************************************************************************************
            # 如果find_inside为None，获取的offset=None.
            screen, offset = crop_image(screen, pictarget.find_inside)
            if find_all:  # 如果是要find_all，就执行一下找到所有图片的逻辑:
                ret = _find_all_pic(screen, picdata, threshold, pictarget)
            # 只要含有ignore或focus参数，就使用_find_pic_with_ignore_focus方法进行匹配
            elif pictarget.ignore or pictarget.focus:
                ret = _find_pic_with_ignore_focus(screen, picdata, threshold, pictarget)
            else:
                ret = _find_pic_by_strategy(screen, picdata, threshold, pictarget)
        else:
            LOGGING.warning("Whole screen is black, skip cv matching")
            ret, offset = None, None
        # 如果指定调试状态，展示图像识别时的截屏图片：
        if DEBUG:
            aircv.show(screen)
        # find_all相关：如果发现ret是个list，如果是[]或者None则换成None，list非空，则求出ret = ret_pos_list
        ret = _settle_ret_list(ret, pictarget, offset, wnd_pos)
        # 如果发现返回的是个list，说明是find_all模式，直接返回这个结果ret_pos_list
        if isinstance(ret, list):
            return ret
        # 如果识别失败，调用用户指定的intervalfunc
        if ret is None:
            if intervalfunc is not None:
                aircv.imwrite(RECENT_CAPTURE_PATH, screen)
                intervalfunc()
            for name, func in WATCHER.items():
                LOGGING.info("exec watcher %s", name)
                func()
            # if timeout and not found: save img and raise
            if (time.time() - start_time) > timeout:
                aircv.imwrite(RECENT_CAPTURE_PATH, screen)
                raise MoaNotFoundError('Picture %s not found in screen' % pictarget)

            time.sleep(interval)
            continue
        else:
            # if image found, save img and return
            aircv.imwrite(RECENT_CAPTURE_PATH, screen)
            ret_pos = TargetPos().getXY(ret, pictarget.target_pos)
            if offset:   # 需要把find_inside造成的crop偏移，加入到操作偏移值offset中：
                ret_pos = int(ret_pos[0] + offset[0]), int(ret_pos[1] + offset[1])
            if wnd_pos:  # 实际操作位置：将相对于窗口的操作坐标，转换成相对于整个屏幕的操作坐标
                ret_pos = int(ret_pos[0] + wnd_pos[0]), int(ret_pos[1] + wnd_pos[1])
                # 将窗口位置记录进log内，以便report在解析时可以mark到正确位置
                log_in_func({"wnd_pos": wnd_pos})
            return ret_pos


def _settle_ret_list(ret, pictarget, offset=None, wnd_pos=None):
    """
        find_all相关：如果发现ret是个list，如果是[]则换成None，list非空，则求出ret = ret_pos_list
    """
    if not ret:  # 没找到结果，直接返回None,以便_loop_find执行未找到的逻辑
        return None

    elif isinstance(ret, list):  # 如果是find_all模式，则找到的是一个结果列表，处理后返回ret_pos_list
        ret_pos_list = []

        for one_ret in ret:  # 对结果列表中的每一个结果都进行一次结果偏移的处理
            ret_pos = TargetPos().getXY(one_ret, pictarget.target_pos)
            if offset:   # 需要把find_inside造成的crop偏移，加入到操作偏移值offset中：
                ret_pos = int(ret_pos[0] + offset[0]), int(ret_pos[1] + offset[1])
            if wnd_pos:  # 实际操作位置：将相对于窗口的操作坐标，转换成相对于整个屏幕的操作坐标
                ret_pos = int(ret_pos[0] + wnd_pos[0]), int(ret_pos[1] + wnd_pos[1])
                # 将窗口位置记录进log内，以便report在解析时可以mark到正确位置
                log_in_func({"wnd_pos": wnd_pos})
            ret_pos_list.append(ret_pos)

        return ret_pos_list

    else:  # 非find_all模式，返回的是一个dict，则正常返回即可
        return ret


@logwrap
@platform(on=["Android", "Windows", "IOS"])
def _snapshot(filename="screen.png", windows_hwnd=None):
    filename = "%s.jpg" % int(time.time() * 1000)
    # to use it as snapshot file name:
    G.RECENT_CAPTURE_PATH = os.path.join(LOG_DIR, SAVE_SCREEN, filename)
    # write filepath into log:
    if ST.SAVE_SCREEN:
        log_in_func({"screen": os.path.join(SAVE_SCREEN, filename)})
    # device snapshot: default not save
    if get_platform() == "Windows" and windows_hwnd:
        screen = DEVICE.snapshot_by_hwnd(filename=None, hwnd_to_snap=windows_hwnd)
    else:
        screen = DEVICE._snapshot_impl(filename=None)
    global RECENT_CAPTURE
    RECENT_CAPTURE = screen  # used for keep_capture()
    return screen
