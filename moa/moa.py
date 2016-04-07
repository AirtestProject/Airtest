#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx gzliuxin
# Created: 2015-05-17 20:30
# Modified: 2015-06-09
# Modified: 2015-10-13 ver 0.0.2

"""
Moa = ADB + AIRCV + MINICAP + MINITOUCH

Script engine.
"""

__version__ = '0.0.2'


DEBUG = False
SERIALNO = ''
ADDRESS = ('127.0.0.1', 5037)
BASE_DIR = '.'
LOG_FILE = ''
LOG_FILE_FD = None
TIMEOUT = 20
RUNTIME_STACK = []
EXTRA_LOG = {}
GEVENT_RUNNING = False
SCREEN = None
GEVENT_DONE = [False]
TOUCH_POINTS = {}
DEVICE = None
KEEP_CAPTURE = False
RECENT_CAPTURE = None
OPDELAY = 0.1
THRESHOLD = 0.6
THRESHOLD_STRICT = 0.7
PLAYRES = []
CVINTERVAL = 0.5
SAVE_SCREEN = None
REFRESH_SCREEN_DELAY = 1
SRC_RESOLUTION = []
CVSTRATEGY = None
SCRIPTHOME = None
RESIZE_METHOD = None
RECONNECT_TIMES = 5

MASK_RECT = None # windows运行时，将当前的IDE窗口屏蔽掉，防止识别为脚本中的图片


import os
import re
import sys
import shutil
import warnings
import json
import time
import functools
import fnmatch
import subprocess
import signal
import ast
import socket
import traceback
import atexit
import uiautomator
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from error import MoaError, MoaNotFoundError
from core import adb_devices
import core
from ..aircv import aircv
from ..aircv import generate_character_img as textgen
from utils import _isstr, _islist
try:
    import win
except ImportError:
    win = None
    print "win module import error"


"""
Some utils
"""


def log(tag, data, exec_script_fail=False):
    ''' Not thread safe '''
    if DEBUG:
        print tag, data
    if LOG_FILE_FD is None:
        return
    def dumper(obj):
        try:
            return obj.__dict__
        except:
            return None

    # 调度脚本失败时，单独记入log中：
    if exec_script_fail==True:
        LOG_FILE_FD.write(json.dumps({'tag': tag, 'depth': 1, 'time': time.strftime("%Y-%m-%d %H:%M:%S"), 'data': data}, default=dumper) + '\n')
        LOG_FILE_FD.flush()
        return

    LOG_FILE_FD.write(json.dumps({'tag': tag, 'depth': len(RUNTIME_STACK), 'time': time.strftime("%Y-%m-%d %H:%M:%S"), 'data': data}, default=dumper) + '\n')
    LOG_FILE_FD.flush()


def handle_stacked_log():
    # 处理stack中的log
    while RUNTIME_STACK:
        # 先取最后一个，记了log之后再pop，避免depth错误
        log_stacked = RUNTIME_STACK[-1]
        log("function", fndata)
        RUNTIME_STACK.pop()

atexit.register(handle_stacked_log)


def logwrap(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        global RUNTIME_STACK, EXTRA_LOG
        start = time.time()
        fndata = {'name': f.__name__, 'args': args, 'kwargs': kwargs}
        RUNTIME_STACK.append(fndata)
        try:
            res = f(*args, **kwargs)
        except (MoaError, Exception) as err:
            data = {"traceback": traceback.format_exc(), "time_used": time.time()-start}
            fndata.update(data)
            fndata.update(EXTRA_LOG)
            log("error", fndata)
            # traceback.print_exc()
            # Exit when meet MoaError
            # raise SystemExit(1)
            raise
        else:
            time_used = time.time() - start
            print '>'*len(RUNTIME_STACK), 'Time used:', f.__name__, time_used
            sys.stdout.flush()
            fndata.update({'time_used': time_used, 'ret': res})
            fndata.update(EXTRA_LOG)
            log('function', fndata)
        finally:
            EXTRA_LOG = {}
            RUNTIME_STACK.pop()
        return res
    return wrapper


def transparam(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not _isstr(args[0]):
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
            core.Android: "Android",
            win.Windows: "Windows"
        }
    else:
        name_dict = {
            core.Android: "Android"
        }
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


def _show_screen(pngstr):
    if not GEVENT_RUNNING:
        return
    try:
        import cv2
        import numpy as np
        global SCREEN
        nparr = np.fromstring(pngstr, np.uint8)
        SCREEN = cv2.imdecode(nparr, cv2.CV_LOAD_IMAGE_COLOR)
    except:
        pass


"""
Script initialization
"""


def set_address((host, port)):
    global ADDRESS
    ADDRESS = (host, port)
    # FIXME(ssx): need to verify


def set_serialno(sn=None, minicap=True, minitouch=True):
    '''
    auto set if only one device
    support filepath match patten, eg: c123*
    '''
    global SERIALNO
    if not sn:
        devs = list(adb_devices(state='device', addr=ADDRESS))
        if len(devs) > 1:
            print ("more than one device, auto choose one, to specify serialno: set_serialno(sn)")
        elif len(devs) == 0:
            raise MoaError("no device, please check your adb connection")
        SERIALNO = devs[0][0]
    else:
        exists = 0
        status = None
        for (serialno, st) in adb_devices(addr=ADDRESS):
            if fnmatch.fnmatch(serialno, sn):
                exists += 1
                status = st
                SERIALNO = serialno
        if exists == 0:
            raise MoaError("Device[{}] not found in {}".format(sn, ADDRESS))
        if exists > 1:
            SERIALNO = None
            raise MoaError("too many devices found")
        if status != 'device':
            raise MoaError("Device status not good: {}".format(status))
    global CVSTRATEGY
    CVSTRATEGY = ["siftpre", "siftnopre", "tpl"]
    global DEVICE
    DEVICE = core.Android(SERIALNO, addr=ADDRESS, minicap=minicap, minitouch=minitouch)
    global PLAYRES
    PLAYRES = [DEVICE.size["width"], DEVICE.size["height"]]
    return SERIALNO


def set_windows():
    if win is None:
        raise RuntimeError("win module is not available")
    global DEVICE
    DEVICE = win.Windows()
    global CVSTRATEGY
    if not CVSTRATEGY:
        CVSTRATEGY = ["tpl", "siftnopre"]
    # set no resize on windows as default
    global RESIZE_METHOD
    if not RESIZE_METHOD:
        RESIZE_METHOD = aircv.no_resize


def connect(url):
    parsed = urlparse(url)
    if parsed.scheme != 'moa':
        raise MoaError("url should start with moa://")

    host = parsed.hostname or '127.0.0.1'
    port = parsed.port or 5037
    sn = parsed.path[1:]
    set_address((host, port))
    set_serialno(sn)


def set_basedir(base_dir):
    global BASE_DIR
    BASE_DIR = base_dir


def set_logfile(filename="log.txt", inbase=True):
    global LOG_FILE, LOG_FILE_FD
    LOG_FILE = filename
    if inbase:
        LOG_FILE = os.path.join(BASE_DIR, filename)
    LOG_FILE_FD = open(LOG_FILE, 'wb')


def set_screendir(dirpath="img_record"):
    global SAVE_SCREEN
    # force clear dir
    shutil.rmtree(dirpath, ignore_errors=True)
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)
    SAVE_SCREEN = dirpath


def set_threshold(value):
    global THRESHOLD
    if value > 1 or value < 0:
        raise RuntimeError("invalid threshold: %s"%value)
    THRESHOLD = value


def set_scripthome(dirpath):
    global SCRIPTHOME
    SCRIPTHOME = dirpath


def set_globals(key, value):
    globals()[key] = value


def refresh_device():
    time.sleep(REFRESH_SCREEN_DELAY)
    DEVICE.refreshOrientationInfo()


class TargetPos(object):
    """
    点击目标图片的不同位置，默认为中心点0
    1 2 3
    4 0 6
    7 8 9
    """
    LEFTUP, UP, RIGHTUP = 1, 2, 3
    LEFT, MID, RIGHT = 4, 5, 6
    LEFTDOWN, DOWN, RIGHTDOWN = 7, 8, 9

    def getXY(self, cvret, pos):
        if pos == 0 or pos == self.MID:
            return cvret["result"]
        rect = cvret.get("rectangle")
        if not rect:
            print "could not get rectangle, use mid point instead"
            return cvret["result"]
        w = rect[2][0] - rect[0][0]
        h = rect[2][1] - rect[0][1]
        if pos == self.LEFTUP:
            return rect[0]
        elif pos == self.LEFTDOWN:
            return rect[1]
        elif pos == self.RIGHTDOWN:
            return rect[2]
        elif pos == self.RIGHTUP:
            return rect[3]
        elif pos == self.LEFT:
            return rect[0][0], rect[0][1] + h / 2
        elif pos == self.UP:
            return rect[0][0] + w / 2, rect[0][1]
        elif pos == self.RIGHT:
            return rect[2][0], rect[2][1] - h / 2
        elif pos == self.DOWN:
            return rect[2][0] - w / 2, rect[2][1]
        else:
            print "invalid target_pos:%s, use mid point instead" % pos
            return cvret["result"]


def set_mask_rect(mask_rect=None):
    if mask_rect:
        str_rect = mask_rect.split(',')
        mask_rect = []
        for i in str_rect:
            mask_rect.append(max(int(i), 0)) # 如果有负数，就用0 代替
        global MASK_RECT
        MASK_RECT = mask_rect
        print 'MASK_RECT in moa changed : ', MASK_RECT
    else:
        print "pass wrong IDE rect into moa.MASK_RECT."


def _find_pic(picdata, rect=None, threshold=THRESHOLD, target_pos=TargetPos.MID, record_pos=[], sch_resolution=[], templateMatch=False):
    ''' find picture position in screen '''
    '''mask_rect: 原图像中被黑化的东西'''
    # 如果是KEEP_CAPTURE, 就取上次的截屏，否则重新截屏
    if KEEP_CAPTURE and RECENT_CAPTURE is not None:
        screen = RECENT_CAPTURE
    else:
        screen = snapshot()

    # 如果截屏失败，则screen为空，打印提示后，识别结果直接返回None
    if screen is None:
        print "SCREEN captured Fail : SCREEN is None !"
        return None
    # 临时措施：将屏幕文件写出后，再使用OpenCV方法读出来：
    # 改进思路:(core.py中的snapshot()函数调用了aircv.string_2_img(screen))
    aircv.cv2.imwrite("screen.jpg", screen)
    screen = aircv.imread("screen.jpg")

    # -----建军添加：进行IDE区域的遮挡：
    global MASK_RECT
    print "----------- MASK_RECT :", MASK_RECT
    if MASK_RECT:
        # screen = aircv.cv2.rectangle(screen, (200,50), (500,800), (0,255,0), -1)
        screen = aircv.cv2.rectangle(screen, (MASK_RECT[0],MASK_RECT[1]), (MASK_RECT[2],MASK_RECT[3]), (255,255,255), -1)
        # aircv.cv2.imshow("check_mask_rect", screen)
        # aircv.cv2.waitKey(0)

    # 在rect矩形区域内查找，有record_pos之后，基本上没用
    offsetx, offsety = 0, 0
    if rect is not None and len(rect) == 4:
        if len(filter(lambda x: (x<=1 and x>=0), rect)) == 4:
            x0, y0, x1, y1 = rect[0] * DEVICE.size["width"], rect[1] * DEVICE.size["height"], rect[2] * DEVICE.size["width"], rect[3] * DEVICE.size["height"]
        else:
            x0, y0, x1, y1 = rect
        screen = aircv.crop(screen, (x0, y0), (x1, y1))
        offsetx, offsety = x0, y0
    # 三种不同的匹配算
    try:
        if templateMatch is True:
            print "matchtpl"
            device_resolution = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
            ret = aircv.find_template_after_pre(screen, picdata, sch_resolution=sch_resolution, src_resolution=device_resolution, design_resolution=[960, 640], threshold=0.6, resize_method=RESIZE_METHOD)
        #三个参数要求：点击位置press_pos=[x,y]，搜索图像截屏分辨率sch_pixel=[a1,b1]，源图像截屏分辨率src_pixl=[a2,b2]
        #如果调用时四个要求参数输入不全，不调用区域预测，仍然使用原来的方法：
        elif not record_pos:
            print "siftnopre"
            ret = aircv.find_sift(screen, picdata)
        #三个要求的参数均有输入时，加入区域预测部分：
        else:
            print "siftpre"
            _pResolution = DEVICE.getCurrentScreenResolution()
            ret = aircv.find_sift_by_pre(screen, picdata, _pResolution, record_pos[0], record_pos[1])
    except aircv.Error:
        ret = None
    except Exception as err:
        traceback.print_exc()
        ret = None
    print ret
    EXTRA_LOG.update({"cv": ret})
    if not ret:
        return None
    if threshold and ret["confidence"] < threshold:
        return None
    pos = TargetPos().getXY(ret, target_pos)
    return int(pos[0] + offsetx), int(pos[1] + offsety)


@logwrap
def _loop_find(pictarget, timeout=TIMEOUT, interval=CVINTERVAL, threshold=None, intervalfunc=None):
    print "try finding %s" % pictarget
    pos = None
    left = max(1, int(timeout))
    start_time = time.time()
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
    while True:
        # 阈值优先取自定义设置的，再取函数传入的
        threshold = getattr(pictarget, "threshold") or threshold or THRESHOLD
        def find_pic_by_strategy():
            pos = None
            for st in CVSTRATEGY:
                if st == "siftpre" and getattr(pictarget, "record_pos"):
                    pos = _find_pic(picdata, threshold=threshold, rect=pictarget.rect, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos)
                elif st == "siftnopre":
                    # 在预测区域没有找到，则退回全局查找
                    pos = _find_pic(picdata, threshold=threshold, target_pos=pictarget.target_pos)
                elif st == "tpl" and getattr(pictarget, "resolution"):
                    # 再用缩放后的模板匹配来找
                    pos = _find_pic(picdata, threshold=threshold, rect=pictarget.rect, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos, sch_resolution=pictarget.resolution, templateMatch=True)
                else:
                    print "skip CVSTRATEGY:%s"%st
                # 找到一个就返回
                if pos is not None:
                    return pos
            return pos
        pos = find_pic_by_strategy()
        if pos is None:
            # 如果没找到，调用用户指定的intervalfunc
            if intervalfunc is not None:
                intervalfunc()
            # 超时则抛出异常
            if (time.time() - start_time) > timeout:
                raise MoaNotFoundError('Picture %s not found in screen' % pictarget)
            time.sleep(interval)
            continue
        return pos


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
        self.threshold = threshold # if threshold is not None else THRESHOLD
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
@platform(on=["Android"])
def amstart(package, activity=None):
    DEVICE.amstart(package, activity)
    refresh_device()


@logwrap
@platform(on=["Android"])
def amstop(package):
    DEVICE.amstop(package)
    refresh_device()


@logwrap
@platform(on=["Android"])
def amclear(package):
    DEVICE.amclear(package)


@logwrap
@platform(on=["Android"])
def install(filepath):
    return DEVICE.install(filepath)


@logwrap
@platform(on=["Android"])
def uninstall(package):
    return DEVICE.uninstall(package)


@logwrap
@platform(on=["Android", "Windows"])
def snapshot(filename="screen.png"):
    global RECENT_CAPTURE, SAVE_SCREEN, EXTRA_LOG
    if SAVE_SCREEN:
        filename = "%s.jpg" % int(time.time()*1000)
        filename = os.path.join(SAVE_SCREEN, filename)
        EXTRA_LOG.update({"screen": filename})
    screen = DEVICE.snapshot(filename)
    # 如果截屏失败，直接返回None
    if screen is not None and screen.any():
        # screen = aircv.cv2.cvtColor(screen, aircv.cv2.COLOR_BGR2GRAY)
        RECENT_CAPTURE = screen # used for keep_capture()
        return screen
    else:
        return None


@logwrap
@platform(on=["Android"])
def wake():
    DEVICE.wake()


@logwrap
@platform(on=["Android"])
def home():
    DEVICE.home()
    refresh_device()


@logwrap
@transparam
@platform(on=["Android", "Windows"])
def touch(v, timeout=TIMEOUT, delay=OPDELAY, offset=None, safe=False, times=1, right_click=False):
    '''
    @param offset: {'x':10,'y':10,'percent':True}
    '''
    if _isstr(v) or isinstance(v, (MoaPic, MoaText)):
        try:
            pos = _loop_find(v, timeout=timeout)
        except MoaNotFoundError:
            if safe:
                return False
            raise
    else:
        pos = v
    TOUCH_POINTS[time.time()] = {'type': 'touch', 'value': pos}
    print ('touchpos', pos)

    if offset:
        if offset['percent']:
            w, h = DEVICE.size['width'], DEVICE.size['height']
            pos = (pos[0] + offset['x'] * w / 100, pos[1] + offset['y'] * h / 100)
        else:
            pos = (pos[0] + offset['x'], pos[1] + offset['y'])
        print ('touchpos after offset', pos)

    for i in range(times):
        if right_click:
            DEVICE.touch(pos, right_click=True)
        else:
            DEVICE.touch(pos)
    time.sleep(delay)

@logwrap
@transparam
@platform(on=["Android", "Windows"])
def swipe(v1, v2=None, delay=OPDELAY, vector=None, target_poses=None):
    if target_poses:
        if len(target_poses) == 2 and isinstance(target_poses[0], int) and isinstance(target_poses[1], int):
            v1.target_pos = target_poses[0]
            pos1 = _loop_find(v1)
            v1.target_pos = target_poses[1]
            pos2 = _loop_find(v1)
        else:
            raise Exception("invalid params for swipe")
    else:
        if _isstr(v1) or isinstance(v1, MoaPic) or isinstance(v1, MoaText):
            pos1 = _loop_find(v1)
        else:
            pos1 = v1

        if v2:
            if (_isstr(v2) or isinstance(v2, MoaText)):
                keep_capture()
                pos2 = _loop_find(v2)
                keep_capture(False)
            else:
                pos2 = v2
        elif vector:
            print SRC_RESOLUTION
            if (vector[0] <= 1 and vector[1] <= 1):
                w, h = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
                vector = (int(vector[0] * w), int(vector[1] * h))
            pos2 = (pos1[0] + vector[0], pos1[1] + vector[1])
        else:
            raise Exception("no enouph params for swipe")
    print pos1, pos2
    DEVICE.swipe(pos1, pos2)

    time.sleep(delay)


@logwrap
@transparam
@platform(on=["Android","Windows"])
def operate(v, route, timeout=TIMEOUT, delay=OPDELAY):
    if _isstr(v) or isinstance(v, MoaPic) or isinstance(v, MoaText):
        pos = _loop_find(v, timeout=timeout)
    else:
        pos = v
    TOUCH_POINTS[time.time()] = {'type': 'touch', 'value': pos}
    print ('downpos', pos)

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
    if text_temp=="-delete":
        if get_platform()=="Windows":
            # 执行一次‘backspace’删除操作：
            key_str='backspace'
            keyevent(key_str,escape=True)
            return 
        else:
            # print "do sth in android device."
            DEVICE.keyevent('KEYCODE_DEL')
            return
    DEVICE.text(text)

    time.sleep(delay)


@logwrap
@platform(on=["Android", "Windows"])
def sleep(secs=1.0):
    time.sleep(secs)


@logwrap
@transparam
def wait(v, timeout=TIMEOUT, safe=False, interval=CVINTERVAL, intervalfunc=None):
    try:
        pos = _loop_find(v, timeout=timeout, interval=interval, intervalfunc=intervalfunc)
        return pos
    except MoaNotFoundError:
        if not safe:
            raise
        return None


@logwrap
@transparam
def exists(v, timeout=1):
    try:
        pos = _loop_find(v, timeout=timeout)
        return pos
    except MoaNotFoundError as e:
        return False


"""
Assertions for result verification
"""


@logwrap
@transparam
def assert_exists(v, msg="", timeout=TIMEOUT):
    try:
        pos = _loop_find(v, timeout=timeout, threshold=THRESHOLD_STRICT)
        return pos
    except MoaNotFoundError:
        raise AssertionError("%s does not exist in screen" % v)


@logwrap
@transparam
def assert_not_exists(v, msg="", timeout=TIMEOUT, delay=OPDELAY):
    try:
        pos = _loop_find(v, timeout=timeout)
        time.sleep(delay)
        raise AssertionError("%s exists unexpectedly at pos: %s" % (v, pos))
    except MoaNotFoundError:
        # 本语句成功执行后，睡眠delay时间后，再执行下一行语句：
        time.sleep(delay)
        pass


@logwrap
def assert_equal(first, second, msg="", delay=OPDELAY):
    result = (first == second)
    if not result:
        raise AssertionError("%s and %s are not equal" % (first, second))

    time.sleep(delay)


@logwrap
def assert_not_equal(first, second, msg="", delay=OPDELAY):
    result = False if first==second else True
    if not result:
        raise AssertionError("%s and %s are equal" % (first, second))

    time.sleep(delay)


def test_android():
    set_serialno()
    # set_serialno('9ab171d')
    # set_basedir('../taskdata/1433820164')
    #wake()
    #touch('target.png')
    #touch([100, 200])
    #swipe([100, 500], [800, 600])
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
    amstart("com.netease.my")


def test_win():
    set_windows()
    swipe("win.png", (300, 300))
    sleep(1.0)
    swipe("win.png", vector=(0.3, 0.3))
    touch("win.png")


if __name__ == '__main__':
    test_android()
