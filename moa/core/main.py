#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author:  hzsunshx gzliuxin
# Created: 2015-05-17 20:30
# Modified: 2015-06-09
# Modified: 2015-10-13 ver 0.0.2 gzliuxin
# Modified: 2016-04-28 ver 0.0.3 gzliuxin


import os
import shutil
import time
import traceback
import fnmatch
import functools
from moa.aircv import aircv
from moa.aircv import generate_character_img as textgen
from moa.aircv.aircv_tool_func import crop_image, mask_image
from moa.core import android
from moa.core.error import MoaError, MoaNotFoundError
from moa.core.settings import *
from moa.core.utils import Logwrap, MoaLogger, TargetPos, is_str

__version__ = '0.0.4'

"""
    Moa for Android/Windows/iOS
    Moa Android = ADB + AIRCV + MINICAP + MINITOUCH
    Script engine.
"""

try:
    from moa.core import win
except ImportError as e:
    win = None
    print "win module available on Windows only: %s" % e.message
try:
    from moa.core import ios
except ImportError as e:
    ios = None
    print "ios module available on Mac OS only: %s" % e.message

LOGGER = MoaLogger(None)
SCREEN = None
DEVICE = None
DEVICE_LIST = []
KEEP_CAPTURE = False
RECENT_CAPTURE = None


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
    """put pic & related cv params into MoaPic object
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not is_str(args[0]):
            return f(*args, **kwargs)
        picname = args[0]
        picargs = {}
        opargs = {}
        for k, v in kwargs.iteritems():
            if k in ["rect", "threshold", "target_pos", "record_pos", "resolution"]:
                picargs[k] = v
            else:
                opargs[k] = v
        pictarget = MoaPic(picname, **picargs)
        return f(pictarget, *args[1:], **opargs)
    return wrapper


def get_platform():
    if win:
        name_dict = {
            android.Android: "Android",
            win.Windows: "Windows"
        }
    else:
        name_dict = {
            android.Android: "Android"
        }

    if ios:
        name_dict[ios.client.IOS] = "IOS"
    return name_dict.get(DEVICE.__class__)


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


"""
Environment initialization
"""


def set_serialno(sn=None, minicap=True, minitouch=True, addr=None):
    '''
    auto set if only one device
    support filepath match patten, eg: c123*
    '''
    addr = addr or ADDRESS
    if not sn:
        devs = android.ADB(server_addr=addr).devices(state='device')
        if len(devs) > 1:
            print("more than one device, auto choose one, to specify serialno: set_serialno(sn)")
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
    dev = android.Android(sn, addr=addr, minicap=minicap, minitouch=minitouch)
    dev.wake()
    print dev
    global CVSTRATEGY, DEVICE, DEVICE_LIST
    CVSTRATEGY = CVSTRATEGY or CVSTRATEGY_ANDROID
    DEVICE = dev
    DEVICE_LIST.append(dev)
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
            print("more than one device, auto choose one, to specify serialno: set_udid(udid)")
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
    global CVSTRATEGY, DEVICE, DEVICE_LIST
    CVSTRATEGY = CVSTRATEGY or CVSTRATEGY_ANDROID
    DEVICE = dev
    DEVICE_LIST.append(dev)
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
    dev = win.Windows()
    if handle:
        dev.set_handle(int(handle))
    elif window_title:
        handle = dev.find_window(window_title)
        if handle is None:
            raise MoaError("no window found with title: '%s'" % window_title)
    else:
        print "handle not set, use entire screen"
    if dev.handle:
        dev.set_foreground()
    global DEVICE, DEVICE_LIST, CVSTRATEGY, RESIZE_METHOD
    DEVICE = dev
    DEVICE_LIST.append(dev)
    CVSTRATEGY = CVSTRATEGY or CVSTRATEGY_WINDOWS
    # set no resize on windows as default
    RESIZE_METHOD = RESIZE_METHOD or aircv.no_resize


@platform(on=["Android", "Windows"])
def add_device():
    # for android  add another serialno
    if isinstance(DEVICE, android.Android):
        devs = DEVICE.adb.devices(state='device')
        devs = [d[0] for d in devs]
        try:
            another_dev = (set(devs) - set([DEVICE.serialno])).pop()
        except KeyError:
            raise MoaError("no more device to add")
        set_serialno(another_dev)
    # for win add another handler
    elif isinstance(DEVICE, win.Windows):
        if not (DEVICE.window_title and DEVICE.handle):
            raise MoaError("please set_windows with window_title first")
        devs = DEVICE.find_window_list(DEVICE.window_title)
        print devs
        print DEVICE.handle
        try:
            another_dev = (set(devs) - set([DEVICE.handle])).pop()
        except KeyError:
            raise MoaError("no more device to add")
        set_windows(handle=another_dev)
    else:
        pass


@platform(on=["Android", "Windows"])
def set_current(index):
    global DEVICE
    DEVICE = DEVICE_LIST[index]
    if isinstance(DEVICE, win.Windows):
        DEVICE.set_foreground()
    print DEVICE


def set_basedir(base_dir):
    global BASE_DIR
    BASE_DIR = base_dir


def set_logfile(filename=LOGFILE, inbase=True):
    global LOGGER
    basedir = BASE_DIR if inbase else ""
    filepath = os.path.join(basedir, filename)
    LOGGER.set_logfile(filepath)


def set_screendir(dirpath=SCREEN_DIR):
    global SAVE_SCREEN
    # 强制删除dirpath (文件目录树)，新建截屏文件夹ditpath:
    # windows系统下：如果资源管理器中打开了dirpath，再运行脚本时会有WindowsError[5]出现。
    shutil.rmtree(dirpath, ignore_errors=True)
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)
    SAVE_SCREEN = dirpath


def set_threshold(value):
    global THRESHOLD
    if value > 1 or value < 0:
        raise MoaError("invalid threshold: %s" % value)
    THRESHOLD = value


def set_globals(key, value):
    globals()[key] = value


def set_mask_rect(mask_rect):
    global MASK_RECT
    str_rect = mask_rect.split(',')
    mask_rect = []
    for i in str_rect:
        try:
            mask_rect.append(max(int(i), 0))  # 如果有负数，就用0 代替
        except:
            MASK_RECT = None
            return
    # global MASK_RECT
    MASK_RECT = mask_rect
    print 'MASK_RECT in moa changed : ', MASK_RECT


def _get_search_img(pictarget):
    '''获取 截图  (picdata)'''
    if isinstance(pictarget, MoaText):
        # moaText暂时没用了，截图太方便了，以后再考虑文字识别, pil_2_cv2函数有问题，会变底色，后续修
        # picdata = aircv.pil_2_cv2(pictarget.img)
        pictarget.img.save("text.png")
        picdata = aircv.imread("text.png")
    elif isinstance(pictarget, MoaPic):
        picdata = aircv.imread(pictarget.filepath)
    else:
        pictarget = MoaPic(pictarget)
        picdata = aircv.imread(pictarget.filepath)
    return picdata


def _get_screen_img():
    # 如果是KEEP_CAPTURE, 就取上次的截屏，否则重新截屏
    if KEEP_CAPTURE and RECENT_CAPTURE is not None:
        screen = RECENT_CAPTURE
    else:
        screen = snapshot()
    return screen


def _find_pic(screen, picdata, threshold=THRESHOLD, target_pos=TargetPos.MID, record_pos=[], sch_resolution=[], templateMatch=False):
    try:
        if templateMatch is True:
            print "method: template match.."
            device_resolution = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
            ret = aircv.find_template_after_pre(screen, picdata, sch_resolution=sch_resolution, src_resolution=device_resolution, design_resolution=[960, 640], threshold=0.6, resize_method=RESIZE_METHOD)
        # 参数要求：点击位置press_pos=[x,y]，搜索图像截屏分辨率sch_pixel=[a1,b1]，源图像截屏分辨率src_pixl=[a2,b2],如果参数输入不全，不调用区域预测：
        elif not record_pos:
            print "method: sift in whole screen.."
            ret = aircv.find_sift(screen, picdata)
        # 三个要求的参数均有输入时，加入区域预测部分：
        else:
            print "method: sift in predicted area.."
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


def find_pic_by_strategy(screen, picdata, threshold, pictarget, strict_ret=STRICT_RET):
    '''图像搜索时，按照CVSTRATEGY的顺序，依次使用不同方法进行图像搜索'''
    # 在screen中寻找picdata: 分别尝试CVSTRATEGY中的方法
    ret = None
    for st in CVSTRATEGY:
        if st == "siftpre" and getattr(pictarget, "record_pos"):
            # 预测区域sift匹配
            ret = _find_pic(screen, picdata, threshold=threshold, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos)
            print "sift pre  result: ", ret
        elif st == "siftnopre":
            # 全局sift
            ret = _find_pic(screen, picdata, threshold=threshold, target_pos=pictarget.target_pos)
            print "sift result: ", ret
        elif st == "tpl" and getattr(pictarget, "resolution"):
            # 缩放后的模板匹配
            ret = _find_pic(screen, picdata, threshold=threshold, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos, sch_resolution=pictarget.resolution, templateMatch=True)
            print "tpl result: ", ret
        else:
            print "skip CV_STRATEGY:%s" % st
        # 找到一个就返回
        if ret is None:
            continue
        # strict_mode进行进一步检测
        if strict_ret:
            ret = aircv.cal_strict_confi(screen, picdata, ret, threshold=threshold)
        if ret is not None:
            return ret
    return ret


@logwrap
def _loop_find(pictarget, timeout=TIMEOUT, interval=CVINTERVAL, threshold=None, intervalfunc=None, find_in=None):
    '''
    mask_rect: 原图像中需要被白色化的区域——IDE的所在区域.
    find_in: 用于指定区域的图片位置定位，
            find_in="left"时，只在左半边屏幕中寻找(双屏幕的话只在左屏幕中寻找)
            find_in="right"时，只在右半边屏幕中寻找(双屏幕的话只在右屏幕中寻找)
            find_in=[x, y, w, h]时，进行截图寻找（其中，x,y,w,h可以为像素值，也可以为0.0-1.0的比例值）
            注意，之前的rect参数现在已并入find_in，兼容之前脚本
    '''
    print "Try finding:\n %s" % pictarget
    picdata = _get_search_img(pictarget)
    # 兼容以前的rect参数（指定寻找区域），如果脚本层仍然有rect参数，传递给find_in:
    if pictarget.rect and not find_in:
        rect = pictarget.rect
        find_in = [rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]]
    # 阈值优先取脚本传入的，其次是utils.py中设置的，再次是moa默认阈值
    threshold = getattr(pictarget, "threshold") or threshold or THRESHOLD
    start_time = time.time()
    while True:
        screen = _get_screen_img()
        offset = (0, 0)
        if not screen.any():
            ret = None
            print "Whole screen is black, skip cv matching"
        else:
            # windows下使用IDE运行脚本时，会有识别到截屏中IDE脚本区的问题，MASK_RECT区域遮挡：
            if MASK_RECT:
                screen = mask_image(screen, MASK_RECT)
            # 获取图像识别的指定区域：指定区域图像+指定区域坐标偏移
            if find_in:
                screen, offset = crop_image(screen, find_in)
            ret = find_pic_by_strategy(screen, picdata, threshold, pictarget)
        # 如果没找到，调用用户指定的intervalfunc
        if ret is None:
            if intervalfunc is not None:
                intervalfunc()
            # 超时则抛出异常
            if (time.time() - start_time) > timeout:
                raise MoaNotFoundError('Picture %s not found in screen' % pictarget)
            time.sleep(interval)
            continue
        else:
            pos = TargetPos().getXY(ret, pictarget.target_pos)
            ret_pos = int(pos[0] + offset[0]), int(pos[1] + offset[1])
            return ret_pos


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
    """

    def __init__(self, filename, rect=None, threshold=None, target_pos=TargetPos.MID, record_pos=None, resolution=[]):
        self.filename = filename
        self.rect = rect
        self.threshold = threshold  # if threshold is not None else THRESHOLD
        self.target_pos = target_pos
        self.record_pos = record_pos
        self.resolution = resolution
        self.filepath = os.path.join(BASE_DIR, filename)

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
    if get_platform() == "IOS":
        DEVICE.launch_app(package)  # package = appid
        return

    DEVICE.amstart(package, activity)


@logwrap
@platform(on=["Android", "IOS"])
def amstop(package):
    if get_platform() == "IOS":  # package = appid
        DEVICE.stop_app(package)
        return

    DEVICE.amstop(package)


@logwrap
@platform(on=["Android"])
def amclear(package):
    DEVICE.amclear(package)


@logwrap
@platform(on=["Android", "IOS"])
def install(filepath):
    return DEVICE.install(filepath)


@logwrap
@platform(on=["Android", "IOS"])
def uninstall(package):
    return DEVICE.uninstall(package)


@logwrap
@platform(on=["Android", "Windows", "IOS"])
def snapshot(filename="screen.png"):
    global RECENT_CAPTURE, SAVE_SCREEN
    if SAVE_SCREEN:
        filename = "%s.jpg" % int(time.time() * 1000)
        filename = os.path.join(SAVE_SCREEN, filename)
        _log_in_func({"screen": filename})
    screen = DEVICE.snapshot(filename)
    # 如果屏幕全黑，则screen.any()返回false
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


@platform(on=["Android"])
def refresh_device():
    print 'Warning, refresh_device is deprecated'
    # time.sleep(REFRESH_SCREEN_DELAY)
    # DEVICE.refreshOrientationInfo()


@logwrap
@_transparam
@platform(on=["Android", "Windows"])
def touch(v, timeout=TIMEOUT, delay=OPDELAY, offset=None, safe=False, times=1, right_click=False, duration=0.01, find_in=None):
    '''
    @param offset: {'x':10,'y':10,'percent':True}
    '''
    if is_str(v) or isinstance(v, (MoaPic, MoaText)):
        try:
            pos = _loop_find(v, timeout=timeout, find_in=find_in)
        except MoaNotFoundError:
            if safe:
                return False
            raise
    else:
        pos = v

    if offset:
        if offset['percent']:
            w, h = DEVICE.size['width'], DEVICE.size['height']
            pos = (pos[0] + offset['x'] * w / 100,
                   pos[1] + offset['y'] * h / 100)
        else:
            pos = (pos[0] + offset['x'], pos[1] + offset['y'])
        print('touchpos after offset', pos)
    else:
        print 'touchpos:', pos

    for i in range(times):
        if right_click:
            DEVICE.touch(pos, right_click=True)
        else:
            # print "in moa , duration is:", duration
            DEVICE.touch(pos, duration=duration)
    time.sleep(delay)


@logwrap
@_transparam
@platform(on=["Android", "Windows"])
def swipe(v1, v2=None, delay=OPDELAY, vector=None, target_poses=None, find_in=None, duration=0.5):
    if target_poses:
        if len(target_poses) == 2 and isinstance(target_poses[0], int) and isinstance(target_poses[1], int):
            v1.target_pos = target_poses[0]
            pos1 = _loop_find(v1, find_in=find_in)
            v1.target_pos = target_poses[1]
            pos2 = _loop_find(v1, find_in=find_in)
        else:
            raise Exception("invalid params for swipe")
    else:
        if is_str(v1) or isinstance(v1, MoaPic) or isinstance(v1, MoaText):
            pos1 = _loop_find(v1, find_in=find_in)
        else:
            pos1 = v1

        if v2:
            if (is_str(v2) or isinstance(v2, MoaText)):
                keep_capture()
                pos2 = _loop_find(v2, find_in=find_in)
                keep_capture(False)
            else:
                pos2 = v2
        elif vector:
            # print SRC_RESOLUTION
            if (vector[0] <= 1 and vector[1] <= 1):
                w, h = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
                vector = (int(vector[0] * w), int(vector[1] * h))
            pos2 = (pos1[0] + vector[0], pos1[1] + vector[1])
        else:
            raise Exception("no enouph params for swipe")
    # print pos1, pos2
    DEVICE.swipe(pos1, pos2, duration=duration)

    time.sleep(delay)


@logwrap
@_transparam
@platform(on=["Android", "Windows"])
def operate(v, route, timeout=TIMEOUT, delay=OPDELAY, find_in=None):
    if is_str(v) or isinstance(v, MoaPic) or isinstance(v, MoaText):
        pos = _loop_find(v, timeout=timeout, find_in=find_in)
    else:
        pos = v
    print('downpos', pos)

    DEVICE.operate({"type": "down", "x": pos[0], "y": pos[1]})
    for vector in route:
        if (vector[0] <= 1 and vector[1] <= 1):
            w, h = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
            vector = [vector[0] * w, vector[1] * h, vector[2]]
        pos2 = (pos[0] + vector[0], pos[1] + vector[1])
        DEVICE.operate({"type": "move", "x": pos2[0], "y": pos2[1]})
        time.sleep(vector[2])
    DEVICE.operate({"type": "up"})
    time.sleep(delay)


@logwrap
@platform(on=["Android", "Windows"])
def keyevent(keyname, escape=False, combine=None, delay=OPDELAY):
    if get_platform() == "Windows":
        DEVICE.keyevent(keyname, escape, combine)
    else:
        DEVICE.keyevent(keyname)

    time.sleep(delay)


@logwrap
@platform(on=["Android", "Windows"])
def text(text, delay=OPDELAY):
    # 如果文本是“-delete”，那么判定为删除一个字符：
    text_temp = text.lower()
    if text_temp == "-delete":
        if get_platform() == "Windows":
            # 执行一次‘backspace’删除操作：
            key_str = 'backspace'
            keyevent(key_str, escape=True)
            return
        else:
            # print "do sth in android device."
            DEVICE.keyevent('KEYCODE_DEL')
            return
    DEVICE.text(text)

    time.sleep(delay)


@logwrap
def sleep(secs=1.0):
    time.sleep(secs)


@logwrap
@_transparam
def wait(v, timeout=TIMEOUT, safe=False, interval=CVINTERVAL, intervalfunc=None, find_in=None):
    try:
        pos = _loop_find(v, timeout=timeout, interval=interval,
                         intervalfunc=intervalfunc, find_in=find_in)
        return pos
    except MoaNotFoundError:
        if not safe:
            raise
        return None


@logwrap
@_transparam
def exists(v, timeout=3, find_in=None):
    try:
        pos = _loop_find(v, timeout=timeout, find_in=find_in)
        return pos
    except MoaNotFoundError as e:
        return False


"""
Assertions for result verification
"""


@logwrap
@_transparam
def assert_exists(v, msg="", timeout=TIMEOUT, find_in=None):
    try:
        pos = _loop_find(v, timeout=timeout,
                         threshold=THRESHOLD_STRICT, find_in=find_in)
        return pos
    except MoaNotFoundError:
        raise AssertionError("%s does not exist in screen" % v)


@logwrap
@_transparam
def assert_not_exists(v, msg="", timeout=TIMEOUT, delay=OPDELAY, find_in=None):
    try:
        pos = _loop_find(v, timeout=timeout, find_in=find_in)
        time.sleep(delay)
        raise AssertionError("%s exists unexpectedly at pos: %s" % (v, pos))
    except MoaNotFoundError:
        # 本语句成功执行后，睡眠delay时间后，再执行下一行语句：
        time.sleep(delay)
        pass


@logwrap
def assert_equal(first, second, msg="", delay=OPDELAY):
    if isinstance(second, unicode) or isinstance(first, unicode):
        result = (unicode(first) == unicode(second))
    elif type(first) == type(second):
        result = (first == second)

    if not result:
        raise AssertionError("%s and %s are not equal" % (first, second))

    time.sleep(delay)


@logwrap
def assert_not_equal(first, second, msg="", delay=OPDELAY):
    if isinstance(second, unicode) or isinstance(first, unicode):
        result = (unicode(first) == unicode(second))
    elif type(first) == type(second):
        result = False if first == second else True

    if not result:
        raise AssertionError("%s and %s are equal" % (first, second))

    time.sleep(delay)


def test_android():
    set_serialno()
    # set_serialno('9ab171d')
    # set_basedir('../taskdata/1433820164')
    home()
    add_device()
    home()
    # touch('target.png')
    # touch([100, 200])
    # swipe([100, 500], [800, 600])
    # exec_script(script.decode('string-escape'))
    # import urllib
    # serialno, base_dir, script = sys.argv[1: 4]
    # # print sys.argv[1: 4]
    # set_serialno(serialno)
    # set_basedir(base_dir)
    # set_serialno()
    # snapshot()
    # set_basedir()
    # set_logfile('run.log')
    # touch('fb.png', rect=(10, 10, 500, 500))
    # time.sleep(1)
    # home()
    # time.sleep(1)
    # swipe('sm.png', vector=(0, 0.3))
    # time.sleep(1)
    # swipe('vp.jpg', 'cal.jpg')
    # img = MoaText(u"你妹").img
    # img.show()
    # install(r"C:\Users\game-netease\Desktop\netease.apk")
    # uninstall("com.example.netease")
    # amstart("com.netease.my", "AppActivity")
    # amstart("com.netease.my")


def test_win():
    # set_windows(window_title="Chrome")
    # touch("win.png")
    # add_device()
    # touch("win.png")
    set_windows()
    touch("win.png")
    # # swipe("win.png", (300, 300))
    # # sleep(1.0)
    # # swipe("win.png", vector=(0.3, 0.3))


def test_ios():
    basedir = os.path.dirname(os.path.abspath(__file__))
    new_ipaname = resign(os.path.join(basedir, "ios/mhxy_mobile2016-05-20-09-58_265402_resign.ipa"))
    print new_ipaname
    udid = set_udid()
    print udid
    install(new_ipaname)
    # amstart("com.netease.devtest")
    # screen_filename = os.path.join(basedir,'tmp.png')
    # snapshot(screen_filename)
    # uninstall("com.netease.devtest")


if __name__ == '__main__':
    # test_android()
    # test_ios()
    test_win()
