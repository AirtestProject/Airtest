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
__all__ = [
    'set_serialno', 'set_basedir', 'set_logfile', 'set_screendir',
    'keep_capture', 'refresh_device',
    'snapshot', 'touch', 'swipe', 'home', 'keyevent', 'text', 'wake',
    'amstart', 'amstop',
    'log', 'wait', 'exists', 'sleep', 'assert_exists', 'exec_string', 'exec_script',
    'wake', 'adb_devices',
    'gevent_run', 'MoaText',
    'assert_equal','assert_not_exists',
]

DEBUG = False
SERIALNO = ''
ADDRESS = ('127.0.0.1', 5037)
BASE_DIR = ''
LOG_FILE = ''
LOG_FILE_FD = None
TIMEOUT = 10
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
PLAYRES = []
CVINTERVAL = 0.5
SAVE_SCREEN = None

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
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from error import MoaError, MoaNotFoundError
from core import adb_devices
import core
from ..aircv import aircv, textgen
from utils import _isstr, _islist


"""
Script initialization
"""


def set_address((host, port)):
    global ADDRESS
    ADDRESS = (host, port)
    # FIXME(ssx): need to verify


def set_serialno(sn=None, minitouch=True):
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
    global DEVICE
    DEVICE = core.Android(SERIALNO, addr=ADDRESS, minitouch=minitouch)
    global PLAYRES
    PLAYRES = [DEVICE.size["width"], DEVICE.size["height"]]
    return SERIALNO


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


def refresh_device():
    DEVICE.refreshOrientationInfo()


"""
Some utils
"""


def log(tag, data):
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


class TargetPos(object):
    """
    点击目标图片的不同位置，默认为中心点0
    1 2 3 
    4 0 6
    7 8 9
    """
    LEFTUP, UP, RIGHTUP = 1, 2, 3
    LEFT, MID, RIGHT = 4, 0, 6
    LEFTDOWN, DOWN, RIGHTDOWN = 7, 8, 9

    def getXY(self, cvret, pos):
        if pos == self.MID:
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


def _find_pic(picdata, rect=None, threshold=THRESHOLD, target_pos=TargetPos.MID, record_pos=[], sch_resolution=[], templateMatch=False):
    ''' find picture position in screen '''
    # 如果是KEEP_CAPTURE, 就取上次的截屏，否则重新截屏
    if KEEP_CAPTURE and RECENT_CAPTURE is not None:
        screen = RECENT_CAPTURE
    else:
        screen = snapshot()
    # 在rect矩形区域内查找，有record_pos之后，基本上没用了
    offsetx, offsety = 0, 0
    if rect is not None and len(rect) == 4:
        if len(filter(lambda x: (x<=1 and x>=0), rect)) == 4:
            x0, y0, x1, y1 = rect[0] * DEVICE.size["width"], rect[1] * DEVICE.size["height"], rect[2] * DEVICE.size["width"], rect[3] * DEVICE.size["height"]
        else:
            x0, y0, x1, y1 = rect
        screen = aircv.crop(screen, (x0, y0), (x1, y1))
        offsetx, offsety = x0, y0
    # 三种不同的匹配算法
    try:
        if templateMatch is True:
            print "matchtpl"
            ret = aircv.find_template_after_pre(screen, picdata, sch_resolution=sch_resolution, src_resolution=DEVICE.getCurrentScreenResolution(), design_resolution=[960, 640])
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
    if not ret:
        return None
    if threshold and ret["confidence"] < threshold:
        return None
    pos = TargetPos().getXY(ret, target_pos)
    return pos[0] + offsetx, pos[1] + offsety


@logwrap
def _loop_find(pictarget, timeout=TIMEOUT, interval=CVINTERVAL, threshold=None):
    print "try finding %s" % pictarget
    pos = None
    left = max(1, int(timeout))
    if isinstance(pictarget, MoaText):
        # moaText暂时没用了，截图太方便了，以后再考虑文字识别吧
        # pil_2_cv2函数有问题，会变底色，后续修改
        # picdata = aircv.pil_2_cv2(pictarget.img)
        pictarget.img.save("text.png")
        picdata = aircv.imread("text.png")
    elif isinstance(pictarget, MoaPic):
        picpath = os.path.join(BASE_DIR, pictarget.filename)
        picdata = aircv.imread(picpath)
    else:
        pictarget = MoaPic(pictarget)
        picpath = os.path.join(BASE_DIR, pictarget)
        picdata = aircv.imread(picpath)
    while left > 0:
        pos = None
        # 阈值全部优先取自定义设置的
        threshold = getattr(pictarget, "threshold", THRESHOLD) 
        if getattr(pictarget, "record_pos"):
            pos = _find_pic(picdata, threshold=threshold, rect=pictarget.rect, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos)
        # 在预测区域没有找到，则退回全局查找
        if pos is None:
            pos = _find_pic(picdata, threshold=threshold, target_pos=pictarget.target_pos)
        # 再用缩放后的模板匹配来找
        if pos is None and getattr(pictarget, "resolution"):
            pos = _find_pic(picdata, threshold=threshold, rect=pictarget.rect, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos, sch_resolution=pictarget.resolution, templateMatch=True)
        if pos is None:
            time.sleep(interval)
            left -= 1
            continue
        return pos
    if pos is None:
        raise MoaNotFoundError('Picture %s not found' % pictarget)


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
    def __init__(self, filename, rect=None, threshold=THRESHOLD, target_pos=TargetPos.MID, record_pos=None, resolution=[]):
        self.filename = filename
        self.rect = rect
        self.threshold = threshold
        self.target_pos = target_pos
        self.record_pos = record_pos
        self.resolution = resolution

    def __repr__(self):
        return self.filename


"""
Device operation & flow control
"""

@logwrap
def shell(cmd, shell=True):
    return DEVICE.shell(cmd)


@logwrap
def amstart(package):
    DEVICE.amstart(package)


@logwrap
def amstop(package):
    DEVICE.amstop(package)


@logwrap
def amclear(package):
    DEVICE.amclear(package)


@logwrap
def install(filepath):
    return DEVICE.install(filepath)


@logwrap
def uninstall(package):
    return DEVICE.uninstall(package)


@logwrap
def snapshot(filename="screen.png"):
    global RECENT_CAPTURE, SAVE_SCREEN, EXTRA_LOG
    if SAVE_SCREEN:
        filename = "%s.jpg" % int(time.time()*1000)
        filename = os.path.join(SAVE_SCREEN, filename)
        EXTRA_LOG.update({"screen": filename})
    screen = DEVICE.snapshot(filename)
    screen = aircv.cv2.cvtColor(screen, aircv.cv2.COLOR_BGR2GRAY)
    RECENT_CAPTURE = screen # used for keep_capture()
    return screen


@logwrap
def wake():
    DEVICE.wake()


@logwrap
def home():
    DEVICE.home()


@logwrap
@transparam
def touch(v, timeout=TIMEOUT, delay=OPDELAY, offset=None):
    '''
    @param offset: {'x':10,'y':10,'percent':True}
    '''
    if _isstr(v) or isinstance(v, MoaPic) or isinstance(v, MoaText):
        pos = _loop_find(v, timeout=timeout)
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

    DEVICE.touch(pos)
    time.sleep(delay)


@logwrap
@transparam
def swipe(v1, v2=None, vector=None):
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
        if (vector[0] <= 1 and vector[1] <= 1):
            vector = (vector[0] * DEVICE.size["width"], vector[1] * DEVICE.size["height"])
        pos2 = (pos1[0] + vector[0], pos1[1] + vector[1])    
    else:
        raise Exception("no enouph params for swipe") 
    print pos1, pos2
    DEVICE.swipe(pos1, pos2)


@logwrap
def keyevent(keyname):
    DEVICE.keyevent(keyname)


@logwrap
def text(text):
    DEVICE.text(text)


@logwrap
def sleep(secs=1.0):
    time.sleep(secs)


@logwrap
@transparam
def wait(v, timeout=10, safe=False):
    try:
        return _loop_find(v, timeout=timeout)
    except MoaNotFoundError:
        if not safe:
            raise
        return None


@logwrap
@transparam
def exists(v, timeout=1):
    try:
        return _loop_find(v, timeout=timeout)
    except MoaNotFoundError as e:
        return False


"""
Assertions for result verification
"""


@logwrap
@transparam
def assert_exists(v, msg="", timeout=TIMEOUT):
    try:
        return _loop_find(v, timeout=timeout)
    except MoaNotFoundError:
        raise AssertionError("%s does not exists" % v)


@logwrap
@transparam
def assert_not_exists(v, msg="", timeout=2):
    try:
        pos = _loop_find(v, timeout=timeout)
        raise AssertionError("%s exists unexpectedly at pos: %s" % (v, pos))
    except MoaNotFoundError:
        pass


@logwrap
def assert_equal(first, second, msg=""):
    result = (first == second)
    if not result:
        raise AssertionError("%s and %s are not equal" % (first, second))


"""
Exececution & Debug
"""

def exec_script(code):
    """secure matter to be fixed"""
    #print "in moa", repr(code)
    tree = ast.parse(code)
    exec(compile(tree, filename="<ast>", mode="exec"))


def exec_string(code):
    '''
    Refs:
    https://greentreesnakes.readthedocs.org/en/latest/nodes.html#expressions
    '''
    st = ast.parse(code)
    assert len(st.body) == 1, "run one line"
    assert isinstance(st.body[0], ast.Expr), "invalid Expr"
    expr = st.body[0]
    assert isinstance(expr.value, ast.Call), "invalid Call"
    func = expr.value.func.id
    assert func in __all__, "invalid func name"
    return eval(code)


def gevent_run(func, *args):
    global GEVENT_RUNNING
    import gevent
    import gevent.monkey
    import cv2
    import numpy as np

    GEVENT_RUNNING = True
    gevent.monkey.patch_all()
    #gevent.signal(signal.SIGQUIT, gevent.shutdown)
    cv2.namedWindow('screen', cv2.WINDOW_NORMAL)

    def run_forever():
        while 1:
            if GEVENT_DONE[0]:
                return
            if SCREEN is None:
                gevent.sleep(0.5)
                continue

            img = SCREEN.copy()
            h, w = img.shape[:2]
            now = time.time()
            for timetag, val in TOUCH_POINTS.items():
                if now - timetag > 2.0:
                    del(TOUCH_POINTS[timetag])
                    continue
                if val['type'] == 'touch':
                    x, y = val['value']
                    cv2.line(img, (x,0), (x,h), (0,255,255), 3)
                    cv2.line(img, (0,y), (w,y), (0,255,255), 3)
            cv2.resizeWindow('screen', w/2, h/2)
            cv2.imshow('screen', img)
            cv2.waitKey(1)
            gevent.sleep(0.5)

    def moa_func():
        try:
            func(*args)
        except:
            raise
        finally:
            GEVENT_DONE[0] = True

    gevent.joinall([
        gevent.spawn(run_forever),
        gevent.spawn(moa_func),
    ])


def test():
    set_serialno('9a4b171d')
    set_basedir('../taskdata/1433820164')
    #wake()
    #touch('target.png')
    #touch([100, 200])
    #swipe([100, 500], [800, 600])
    #exec_string('touch("target.png", timeout=3)')
    exec_script('touch("target.png", timeout=3)\nhome()')
    # exec_script(script.decode('string-escape'))
    # import urllib
    # serialno, base_dir, script = sys.argv[1: 4]
    # # print sys.argv[1: 4]
    # set_serialno(serialno)
    # set_basedir(base_dir)
    # exec_script(urllib.unquote(script))


if __name__ == '__main__':
    set_serialno()
    snapshot()
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
    # touch(MoaText(u"副 本", font=u"华康唐风隶"))
    # install(r"C:\Users\game-netease\Desktop\netease.apk")
    # uninstall("com.example.netease")
