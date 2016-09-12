#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author:  hzsunshx gzliuxin
# Created: 2015-05-17 20:30
# Modified: 2015-06-09
# Modified: 2015-10-13 ver 0.0.2 gzliuxin
# Modified: 2016-04-28 ver 0.0.3 gzliuxin
# Modified: 2016-08-04 ver 0.0.4 gzliuxin

__version__ = '0.1.0'

"""
    Airtest
    Automated test framework for Android/Windows/iOS
    This file is a script engine.
    Use cli.py to run scripts
"""

import os
import shutil
import time
import traceback
import fnmatch
import functools
from airtest.aircv import aircv
from airtest.aircv import generate_character_img as textgen
from airtest.aircv.aircv_tool_func import crop_image, mask_image
from airtest.core import device
from airtest.core import android
from airtest.core.android import uiautomator
from airtest.core.error import MoaError, MoaNotFoundError
from airtest.core.settings import *
from airtest.core.utils import Logwrap, MoaLogger, TargetPos, is_str, get_logger
try:
    from airtest.core import win
except ImportError as e:
    win = None
    print "win module available on Windows only: %s" % e.message
try:
    from airtest.core import ios
except ImportError as e:
    ios = None
    print "ios module available on Mac OS only: %s" % e.message


"""
Global running status
"""


LOGGER = MoaLogger(None)
LOGGING = get_logger("main")
SCREEN = None
DEVICE = None
DEVICE_LIST = []
KEEP_CAPTURE = False
RECENT_CAPTURE = None
WATCHER = {}


"""
Some utils
"""


def log(tag, data, in_stack=True):
    if LOGGER:
        LOGGER.log(tag, data, in_stack)


def _log_in_func(data):
    if LOGGER:
        LOGGER.extra_log.update(data)


def logwrap(f):
    return Logwrap(f, LOGGER)


def _transparam(f):
    """
    put pic & related cv params into MoaPic object
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not is_str(args[0]):
            return f(*args, **kwargs)
        picname = args[0]
        picargs = {}
        opargs = {}
        for k, v in kwargs.iteritems():
            if k in ["whole_screen", "find_inside", "find_outside", "ignore", "focus", "rect", "threshold", "target_pos", "record_pos", "resolution"]:
                picargs[k] = v
            else:
                opargs[k] = v
        pictarget = MoaPic(picname, **picargs)
        return f(pictarget, *args[1:], **opargs)
    return wrapper


def get_platform():
    for name, cls in device.DEV_TYPE_DICT.items():
        if DEVICE.__class__ == cls:
            return name
    return None 


def platform(on=["Android"]):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if get_platform() not in on:
                raise NotImplementedError()
            r = f(*args, **kwargs)
            return r
        return wrapper
    return decorator


def _register_device(dev):
    global DEVICE, DEVICE_LIST
    DEVICE = dev
    DEVICE_LIST.append(dev)


def _delay_after_operation(secs):
    delay = secs or OPDELAY
    time.sleep(delay)


"""
Environment initialization
"""


def set_serialno(sn=None, minicap=True, minitouch=True, addr=None):
    '''
    auto set if only one device
    support filepath match pattern, eg: c123*
    '''
    addr = addr or ADDRESS
    def get_available_sn(sn):
        devs = android.ADB(server_addr=addr).devices(state='device')
        if not sn:
            # if len(devs) > 1:
            #     print("more than one device, auto choose one, to specify serialno: set_serialno(sn)")
            # elif len(devs) == 0:
            if len(devs) == 0:
                raise MoaError("no device, please check your adb connection")
            devs = [d[0] for d in devs]
            devs_in_moa = [d.serialno for d in DEVICE_LIST]
            try:
                another_sn = (set(devs) - set(devs_in_moa)).pop()
            except KeyError:
                raise MoaError("no more device to add")
            sn = another_sn
        else:
            for (serialno, st) in devs:
                if not fnmatch.fnmatch(serialno, sn):
                    continue
                if st != 'device':
                    raise MoaError("Device status not good: %s" % (st,))
                sn = serialno
                break
            if sn is None:
                raise MoaError("Device[%s] not found in %s" % (sn, addr))
        return sn
    sn = get_available_sn(sn)
    dev = android.Android(sn, addr=addr, minicap=minicap, minitouch=minitouch)
    _register_device(dev)
    global CVSTRATEGY
    CVSTRATEGY = CVSTRATEGY or CVSTRATEGY_ANDROID
    return sn


def set_emulator(emu_name='bluestacks', sn=None, addr=None):
    '''
    auto set if only one device
    support filepath match pattern, eg: c123*
    '''
    if not android.Emulator:
        raise RuntimeError("Emulator module available on Windows only")
    addr = addr or ADDRESS
    if not sn:
        devs = android.ADB(server_addr=addr).devices(state='device')
        if len(devs) > 1:
            ("more than one device, auto choose one, to specify serialno: set_serialno(sn)")
        elif len(devs) == 0:
            raise MoaError("no device, please check your adb connection")
        sn = devs[0][0]
    else:
        for (serialno, st) in android.ADB(server_addr=addr).devices(state='device'):
            if not fnmatch.fnmatch(serialno, sn):
                continue
            if st != 'device':
                raise MoaError("Device status not good: %s" % (st,))
            sn = serialno
            break
        if sn is None:
            raise MoaError("Device[%s] not found in %s" % (sn, addr))
    #dev = android.Android(sn, addr=addr, minicap=minicap, minitouch=minitouch)
    if not emu_name:
        emu_name = 'bluestacks'
    dev = android.Emulator(emu_name, sn, addr=addr)
    _register_device(dev)
    global CVSTRATEGY
    CVSTRATEGY = CVSTRATEGY or CVSTRATEGY_ANDROID
    return sn


def set_udid(udid=None):
    '''
    auto set if only one device
    support filepath match patten, eg: c123*
    '''
    global IOSUDID
    udids = ios.utils.list_all_udid()
    if not udid:
        if len(udids) > 1:
            LOGGING.info("more than one device, auto choose one, to specify serialno: set_udid(udid)")
        elif len(udids) == 0:
            raise MoaError("no device, please check your connection")
        IOSUDID = udids[0]
    else:
        exists = 0
        for id in udids:
            if fnmatch.fnmatch(id, udid):
                exists += 1
                IOSUDID = id
        if exists == 0:
            raise MoaError("Device[{}] not found".format(udid))
        if exists > 1:
            IOSUDID = ''
            raise MoaError("too many devices found")
    dev = ios.client.IOS(IOSUDID)
    _register_device(dev)
    global CVSTRATEGY
    CVSTRATEGY = CVSTRATEGY or CVSTRATEGY_ANDROID
    return IOSUDID


def resign(ipaname):
    """resign an app, only valid on Mac"""
    import platform
    os_name = platform.system()
    if os_name != "Darwin":  # Mac os name
        raise MoaError("can't resign ipa on %s OS" % os_name)

    new_ipaname = ios.resign.sign(ipaname)
    return new_ipaname


def set_windows(handle=None, window_title=None):
    if win is None:
        raise RuntimeError("win module is not available")
    window_title = window_title or WINDOW_TITLE
    dev = win.Windows()
    if handle:
        dev.set_handle(int(handle))
    elif window_title:
        devs = dev.find_window_list(window_title)
        if not devs:
            raise MoaError("no window found with title: '%s'" % window_title)
        devs_in_moa = [d.handle for d in DEVICE_LIST]
        try:
            another_dev = (set(devs) - set(devs_in_moa)).pop()
        except KeyError:
            raise MoaError("no more device to add")
        dev.set_handle(another_dev)
    else:
        LOGGING.info("handle not set, use entire screen")
    if dev.handle:
        dev.set_foreground()
    _register_device(dev)

    global CVSTRATEGY, RESIZE_METHOD
    CVSTRATEGY = CVSTRATEGY or CVSTRATEGY_WINDOWS
    # set no resize on windows as default
    RESIZE_METHOD = RESIZE_METHOD or aircv.no_resize


@platform(on=["Android", "Windows"])
def set_current(index):
    global DEVICE
    if index > len(DEVICE_LIST):
        raise IndexError("device index out of range")
    DEVICE = DEVICE_LIST[index]
    if win and get_platform() == "Windows" :
        DEVICE.set_foreground()


def set_basedir(base_dir):
    global BASE_DIR
    BASE_DIR = base_dir


def set_logfile(filename=LOGFILE, inbase=True):
    global LOGGER
    basedir = BASE_DIR if inbase else ""
    filepath = os.path.join(basedir, filename)
    LOGGING.info("set_logfile %s", repr(os.path.realpath(filepath)))
    LOGGER.set_logfile(filepath)


def set_screendir(dirpath=SCREEN_DIR):
    global SAVE_SCREEN
    shutil.rmtree(dirpath, ignore_errors=True)
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)
    SAVE_SCREEN = dirpath


def set_threshold(value):
    global THRESHOLD
    if value > 1 or value < 0:
        raise MoaError("invalid threshold: %s" % value)
    THRESHOLD = value


def set_find_outside(find_outside):
    """设置FIND_OUTSIDE, IDE中调用遮挡脚本编辑区."""
    str_rect = find_outside.split(',')
    find_outside = []
    for i in str_rect:
        find_outside.append(max(int(i), 0))  # 如果有负数，就用0 代替
    global FIND_OUTSIDE
    FIND_OUTSIDE = find_outside


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
        screen = snapshot(windows_hwnd=windows_hwnd)
    return screen


def _find_pic(screen, picdata, threshold=THRESHOLD, target_pos=TargetPos.MID, record_pos=[], sch_resolution=[], templateMatch=False):
    try:
        if templateMatch is True:
            LOGGING.debug("method: template match..")
            device_resolution = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
            ret = aircv.find_template_after_resize(screen, picdata, sch_resolution=sch_resolution, src_resolution=device_resolution, design_resolution=[960, 640], threshold=0.6, resize_method=RESIZE_METHOD, check_color=CHECK_COLOR)
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
    _log_in_func({"cv": ret})
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
            ret = _find_pic(screen, picdata, threshold=threshold, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos, sch_resolution=pictarget.resolution, templateMatch=True)
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
    except aircv.Error:
        ret = None
    except Exception as err:
        traceback.print_exc()
        ret = None

    _log_in_func({"cv": ret})

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

        _log_in_func({"cv": ret_list})

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
def _loop_find(pictarget, timeout=TIMEOUT, interval=CVINTERVAL, threshold=None, intervalfunc=None, find_all=False):
    '''
        keep looking for pic util timeout, execute intervalfunc if pic not found.
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
            elif pictarget.ignore or pictarget.focus:  # 只要含有ignore或focus参数，就使用_find_pic_with_ignore_focus方法进行匹配
                ret = _find_pic_with_ignore_focus(screen, picdata, threshold, pictarget)
            else:
                ret = _find_pic_by_strategy(screen, picdata, threshold, pictarget)
        else:
            LOGGING.warning("Whole screen is black, skip cv matching")
            ret, offset = None, None

        if DEBUG:  # 如果指定调试状态，展示图像识别时的有效截屏区域：
            aircv.show(screen)

        # find_all相关：如果发现ret是个list，如果是[]或者None则换成None，list非空，则求出ret = ret_pos_list
        ret = _settle_ret_list(ret, pictarget, offset, wnd_pos)
        if isinstance(ret, list):  # 如果发现返回的是个list，说明是find_all模式，直接返回这个结果ret_pos_list
            return ret

        # 如果识别失败，调用用户指定的intervalfunc
        if ret is None:
            if intervalfunc is not None:
                intervalfunc()
            for name, func in WATCHER.items():
                LOGGING.info("exec watcher %s", name)
                func()
            # 超时则抛出异常
            if (time.time() - start_time) > timeout:
                raise MoaNotFoundError('Picture %s not found in screen' % pictarget)
            time.sleep(interval)
            continue
        else:
            ret_pos = TargetPos().getXY(ret, pictarget.target_pos)
            if offset:   # 需要把find_inside造成的crop偏移，加入到操作偏移值offset中：
                ret_pos = int(ret_pos[0] + offset[0]), int(ret_pos[1] + offset[1])
            if wnd_pos:  # 实际操作位置：将相对于窗口的操作坐标，转换成相对于整个屏幕的操作坐标
                ret_pos = int(ret_pos[0] + wnd_pos[0]), int(ret_pos[1] + wnd_pos[1])
                # 将窗口位置记录进log内，以便report在解析时可以mark到正确位置
                _log_in_func({"wnd_pos": wnd_pos})
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
                _log_in_func({"wnd_pos": wnd_pos})
            ret_pos_list.append(ret_pos)

        return ret_pos_list

    else:  # 非find_all模式，返回的是一个dict，则正常返回即可
        return ret


def keep_capture(flag=True):
    global KEEP_CAPTURE
    KEEP_CAPTURE = flag


class MoaText(object):
    """autogen Text with aircv"""

    def __init__(self, text, font=u"微软雅黑", size=70, inverse=True):
        self.info = dict(text=text, font=font, size=size, inverse=inverse)
        self.img = textgen.gen_text(text, font, size, inverse)
        # self.img.save("text.png")
        self.threshold = THRESHOLD
        self.target_pos = TargetPos.MID

    def __repr__(self):
        return "MhText(%s)" % repr(self.info)


class MoaPic(object):
    """
    picture as touch/swipe/wait/exists target and extra info for cv match
    filename: pic filename
    rect: find pic in rect of screen
    target_pos: ret which pos in the pic
    record_pos: pos in screen when recording
    resolution: screen resolution when recording
    find_outside: 在源图像指定区域外寻找. (执行方式：抹去对应区域的图片有效内容)
    find_inside:  在源图像指定区域内寻找，find_inside=[x, y, w, h]时，进行截图寻找.（其中，x,y,w,h为像素值）
    whole_screen: 为True时，则指定在全屏内寻找.
    ignore: [ [x_min, y_min, x_max, y_max], ... ]  识别时，忽略掉ignore包含的矩形区域 (mask_tpl)
    focus: [ [x_min, y_min, x_max, y_max], ... ]  识别时，只识别ignore包含的矩形区域 (可信度为面积加权平均)
    """

    def __init__(self, filename, rect=None, threshold=None, target_pos=TargetPos.MID, record_pos=None, resolution=[], find_inside=None, find_outside=None, whole_screen=False, ignore=None, focus=None):
        self.filename = filename
        self.rect = rect
        self.threshold = threshold  # if threshold is not None else THRESHOLD
        self.target_pos = target_pos
        self.record_pos = record_pos
        self.resolution = resolution
        self.filepath = os.path.join(BASE_DIR, filename)

        self.find_inside = find_inside or FIND_INSIDE
        self.find_outside = find_outside or FIND_OUTSIDE
        self.whole_screen = whole_screen or WHOLE_SCREEN

        self.ignore = ignore
        self.focus = focus

    def __repr__(self):
        return self.filepath


"""
Device operation & flow control
"""


@logwrap
@platform(on=["Android"])
def shell(cmd):
    return DEVICE.shell(cmd)


@logwrap
@platform(on=["Android", "IOS"])
def amstart(package, activity=None):
    DEVICE.start_app(package, activity)


@logwrap
@platform(on=["Android", "IOS"])
def amstop(package):
    DEVICE.stop_app(package)


@logwrap
@platform(on=["Android"])
def amclear(package):
    DEVICE.clear_app(package)


@logwrap
@platform(on=["Android", "IOS"])
def install(filepath):
    return DEVICE.install_app(filepath)


@logwrap
@platform(on=["Android", "IOS"])
def uninstall(package):
    return DEVICE.uninstall_app(package)


@logwrap
@platform(on=["Android", "Windows", "IOS"])
def snapshot(filename="screen.png", windows_hwnd=None):
    global RECENT_CAPTURE, SAVE_SCREEN
    if SAVE_SCREEN:
        filename = "%s.jpg" % int(time.time() * 1000)
        filename = os.path.join(SAVE_SCREEN, filename)
        _log_in_func({"screen": filename})

    if get_platform() == "Windows" and windows_hwnd:
        screen = DEVICE.snapshot_by_hwnd(filename=filename, hwnd_to_snap=windows_hwnd)
    else:
        screen = DEVICE.snapshot(filename=filename)
    # 实际上手机可能正好是全黑，不做特殊处理了
    RECENT_CAPTURE = screen  # used for keep_capture()
    return screen


@logwrap
@platform(on=["Android"])
def wake():
    DEVICE.wake()


@logwrap
@platform(on=["Android"])
def home():
    DEVICE.home()


@logwrap
@_transparam
@platform(on=["Android", "Windows"])
def touch(v, timeout=0, delay=0, offset=None, if_exists=False, times=1, right_click=False, duration=0.01):
    '''
    @param if_exists: touch only if the target pic exists
    @param offset: {'x':10,'y':10,'percent':True}
    '''
    timeout = timeout or FIND_TIMEOUT
    if is_str(v) or isinstance(v, (MoaPic, MoaText)):
        try:
            pos = _loop_find(v, timeout=timeout)
        except MoaNotFoundError:
            if if_exists:
                return False
            raise
    else:
        pos = v
        # 互通版需求：点击npc，传入FIND_INSIDE参数作为touch位置矫正(此时的v非img_name_str、非MoaPic、MoaText)
        if FIND_INSIDE and get_platform() == "Windows" and DEVICE.handle:
            wnd_pos = DEVICE.get_wnd_pos_by_hwnd(DEVICE.handle)
            # 操作坐标 = 窗口坐标 + 有效画面在窗口内的偏移坐标 + 传入的有效画面中的坐标
            pos = (wnd_pos[0] + FIND_INSIDE[0] + pos[0], wnd_pos[1] + FIND_INSIDE[1] + pos[1])

    if offset:
        if offset['percent']:
            w, h = DEVICE.size['width'], DEVICE.size['height']
            pos = (pos[0] + offset['x'] * w / 100,
                   pos[1] + offset['y'] * h / 100)
        else:
            pos = (pos[0] + offset['x'], pos[1] + offset['y'])
        LOGGING.debug('touchpos after offset %s', pos)
    else:
        LOGGING.debug('touchpos: %s', pos)

    for i in range(times):
        if right_click:
            DEVICE.touch(pos, right_click=True)
        else:
            DEVICE.touch(pos, duration=duration)
    _delay_after_operation(delay)


@logwrap
@_transparam
@platform(on=["Android", "Windows"])
def swipe(v1, v2=None, delay=0, vector=None, target_poses=None, duration=0.5):
    if target_poses:
        if len(target_poses) == 2 and isinstance(target_poses[0], int) and isinstance(target_poses[1], int):
            v1.target_pos = target_poses[0]
            pos1 = _loop_find(v1)
            v1.target_pos = target_poses[1]
            pos2 = _loop_find(v1)
        else:
            raise Exception("invalid params for swipe")
    else:
        if is_str(v1) or isinstance(v1, MoaPic) or isinstance(v1, MoaText):
            pos1 = _loop_find(v1)
        else:
            pos1 = v1

        if v2:
            if (is_str(v2) or isinstance(v2, MoaText)):
                keep_capture()
                pos2 = _loop_find(v2)
                keep_capture(False)
            else:
                pos2 = v2
        elif vector:
            if (vector[0] <= 1 and vector[1] <= 1):
                w, h = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
                vector = (int(vector[0] * w), int(vector[1] * h))
            pos2 = (pos1[0] + vector[0], pos1[1] + vector[1])
        else:
            raise Exception("no enouph params for swipe")
    DEVICE.swipe(pos1, pos2, duration=duration)
    _delay_after_operation(delay)


@logwrap
@_transparam
@platform(on=["Android", "Windows"])
def operate(v, route, timeout=TIMEOUT, delay=0):
    if is_str(v) or isinstance(v, MoaPic) or isinstance(v, MoaText):
        pos = _loop_find(v, timeout=timeout)
    else:
        pos = v

    DEVICE.operate({"type": "down", "x": pos[0], "y": pos[1]})
    for vector in route:
        if (vector[0] <= 1 and vector[1] <= 1):
            w, h = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
            vector = [vector[0] * w, vector[1] * h, vector[2]]
        pos2 = (pos[0] + vector[0], pos[1] + vector[1])
        DEVICE.operate({"type": "move", "x": pos2[0], "y": pos2[1]})
        time.sleep(vector[2])
    DEVICE.operate({"type": "up"})
    _delay_after_operation(delay)


@logwrap
@platform(on=["Android"])
def pinch(in_or_out='in', center=None, percent=0.5, delay=0):
    DEVICE.pinch(in_or_out=in_or_out, center=center, percent=percent)
    _delay_after_operation(delay)


@logwrap
@platform(on=["Android", "Windows"])
def keyevent(keyname, escape=False, combine=None, delay=0):
    if get_platform() == "Windows":
        DEVICE.keyevent(keyname, escape, combine)
    else:
        DEVICE.keyevent(keyname)
    _delay_after_operation(delay)


@logwrap
@platform(on=["Android", "Windows"])
def text(text, delay=0, clear=False):
    text_temp = text.lower()
    if clear is True:
        if get_platform() == "Windows":
            for i in range(30):
                DEVICE.keyevent('backspace', escape=True)
        else:
            DEVICE.shell(" && ".join(["input keyevent KEYCODE_DEL"] * 30))

    if text_temp == "-delete":
        # 如果文本是“-delete”，那么删除一个字符
        if get_platform() == "Windows":
            DEVICE.keyevent('backspace', escape=True)
        else:
            DEVICE.keyevent('KEYCODE_DEL')
    else:
        DEVICE.text(text)
    _delay_after_operation(delay)


@logwrap
def sleep(secs=1.0):
    time.sleep(secs)


@logwrap
@_transparam
def wait(v, timeout=0, interval=CVINTERVAL, intervalfunc=None):
    timeout = timeout or FIND_TIMEOUT
    pos = _loop_find(v, timeout=timeout, interval=interval, intervalfunc=intervalfunc)
    return pos


@logwrap
@_transparam
def exists(v, timeout=0):
    timeout = timeout or FIND_TIMEOUT_TMP
    try:
        pos = _loop_find(v, timeout=timeout)
        return pos
    except MoaNotFoundError as e:
        return False


@logwrap
@_transparam
def find_all(v, timeout=0):
    timeout = timeout or FIND_TIMEOUT_TMP
    try:
        return _loop_find(v, timeout=timeout, find_all=True)
    except MoaNotFoundError:
        return []


@logwrap
@platform(on=["Android"])
def logcat(grep_str="", extra_args="", read_timeout=10):
    return DEVICE.logcat(grep_str, extra_args, read_timeout)


@logwrap
def add_watcher(name, func):
    WATCHER[name] = func


@logwrap
def remove_watcher(name):
    WATCHER.pop(name)


"""
Assertions for result verification
"""


@logwrap
@_transparam
def assert_exists(v, msg="", timeout=0):
    timeout = timeout or FIND_TIMEOUT
    try:
        pos = _loop_find(v, timeout=timeout, threshold=THRESHOLD_STRICT)
        return pos
    except MoaNotFoundError:
        raise AssertionError("%s does not exist in screen" % v)


@logwrap
@_transparam
def assert_not_exists(v, msg="", timeout=0):
    timeout = timeout or FIND_TIMEOUT_TMP
    try:
        pos = _loop_find(v, timeout=timeout)
        raise AssertionError("%s exists unexpectedly at pos: %s" % (v, pos))
    except MoaNotFoundError:
        pass


@logwrap
def assert_equal(first, second, msg=""):
    if isinstance(second, unicode) or isinstance(first, unicode):
        result = (unicode(first) == unicode(second))
    elif type(first) == type(second):
        result = (first == second)

    if not result:
        raise AssertionError("%s and %s are not equal" % (first, second))


@logwrap
def assert_not_equal(first, second, msg=""):
    if isinstance(second, unicode) or isinstance(first, unicode):
        result = not (unicode(first) == unicode(second))
    elif type(first) == type(second):
        result = False if first == second else True

    if not result:
        raise AssertionError("%s and %s are equal" % (first, second))
