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
    'set_serialno', 'set_basedir', 'set_logfile', 'keep_capture',
    'snapshot', 'touch', 'swipe', 'home', 'keyevent', 'text', 'wake',
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
GEVENT_RUNNING = False
SCREEN = None
GEVENT_DONE = [False]
TOUCH_POINTS = {}
DEVICE = None
KEEP_CAPTURE = False
RECENT_CAPTURE = None
OPDELAY = 0.1
THRESHOLD = 0.6

import os
import re
import sys
import warnings
import json
import time
import functools
import fnmatch
import subprocess
import signal
import ast
import socket
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from error import MoaError, MoaNotFoundError
from core import adb_devices
import core
from aircv import aircv, textgen
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
            raise MoaError("more than one device, please specify serialno: set_serialno(sn)")
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


def set_logfile(filename, inbase=True):
    global LOG_FILE, LOG_FILE_FD
    LOG_FILE = filename
    if inbase:
        LOG_FILE = os.path.join(BASE_DIR, filename)
    LOG_FILE_FD = open(LOG_FILE, 'wb')


"""
Some utils
"""


def log(tag, data):
    ''' Not thread safe '''
    if DEBUG:
        print tag, data
    if LOG_FILE_FD is None:
        return
    LOG_FILE_FD.write(json.dumps({'tag': tag, 'depth': len(RUNTIME_STACK), 'time': time.strftime("%Y-%m-%d %H:%M:%S"), 'data': data}) + '\n')
    LOG_FILE_FD.flush()


def logwrap(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        RUNTIME_STACK.append(f)
        start = time.time()
        fndata = {'name': f.__name__, 'args': args, 'kwargs': kwargs}
        try:
            res = f(*args, **kwargs)
        except MoaError as e:
            data = {"message": e.value, "time_used": time.time()-start}
            data.update(fndata)
            log("error", data)
            print "Program terminated:", e.value
            # Exit when meet MoaError
            raise SystemExit(1)
        else:
            print '>'*len(RUNTIME_STACK), 'Time used:', f.__name__, time.time() - start
            sys.stdout.flush()
            log('function', {'name': f.__name__, 'args': args, 'kwargs': kwargs, 'time_used': time.time()-start})
        finally:
            RUNTIME_STACK.pop()
        return res
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


def _find_pic(picdata, rect=None, threshold=THRESHOLD):
    ''' find picture position in screen '''
    if KEEP_CAPTURE and RECENT_CAPTURE is not None:
        screen = RECENT_CAPTURE
    else:
        screen = snapshot()
    offsetx, offsety = 0, 0
    if rect is not None and len(rect) == 4:
        if len(filter(lambda x: (x<=1 and x>=0), rect)) == 4:
            x0, y0, x1, y1 = rect[0] * DEVICE.size["width"], rect[1] * DEVICE.size["height"], rect[2] * DEVICE.size["width"], rect[3] * DEVICE.size["height"]
        else:
            x0, y0, x1, y1 = rect
        screen = aircv.crop(screen, (x0, y0), (x1, y1))
        offsetx, offsety = x0, y0
    try:
        ret = aircv.find_sift(screen, picdata)
    # need to specify different exceptions
    except Exception as err:
        print err
        ret = None
    print ret
    if not ret:
        return None
    if threshold and ret["confidence"] < threshold:
        return None
    ret = ret["result"]
    return ret[0] + offsetx, ret[1] + offsety


def _loop_find(pictarget, background=None, timeout=TIMEOUT, rect=None, threshold=THRESHOLD):
    pos = None
    left = max(1, int(timeout))
    if isinstance(pictarget, MoaText):
        # pil_2_cv2函数有问题，会变底色，后续修改
        # picdata = aircv.pil_2_cv2(pictarget.img)
        pictarget.img.save("text.png")
        picdata = aircv.imread("text.png")
    else:
        pictarget = os.path.join(BASE_DIR, pictarget)
        picdata = aircv.imread(pictarget)
    while left > 0:
        pos = _find_pic(picdata, rect=rect, threshold=threshold)
        if pos is None:
            time.sleep(1)
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

    def __repr__(self):
        return "MhText(%s)" % repr(self.info)


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
def snapshot(filename="screen.jpg"):
    global RECENT_CAPTURE
    screen = DEVICE.snapshot()
    # to be fixed, screen.jpg is used for debug 
    open(filename, 'wb').write(screen)
    screen = aircv.imread(filename)
    # _show_screen(screen)
    RECENT_CAPTURE = screen # used for keep_capture()
    return screen


@logwrap
def wake():
    DEVICE.wake()


@logwrap
def home():
    DEVICE.home()


@logwrap
def touch(v, rect=None, timeout=TIMEOUT, delay=OPDELAY, offset=None):
    '''
    @param offset: {'x':10,'y':10,'percent':True}
    '''
    if _isstr(v) or isinstance(v, MoaText):
        pos = _loop_find(v, timeout=timeout, rect=rect)
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
def swipe(v1, v2):
    if (_isstr(v1) or isinstance(v1, MoaText)) and (_isstr(v2) or isinstance(v2, MoaText)):
        pos1 = _loop_find(v1)
        keep_capture()
        pos2 = _loop_find(v2)
        keep_capture(False)
    else:
        pos1, pos2 = v1, v2
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
def wait(v, timeout=10, safe=False):
    try:
        return _loop_find(v, timeout=timeout)
    except MoaNotFoundError:
        if not safe:
            raise
        return None


@logwrap
def exists(v, rect=None):
    try:
        return _loop_find(v, timeout=1, rect=rect)
    except MoaNotFoundError as e:
        return False


"""
Assertions for result verification
"""


@logwrap
def assert_exists(v, msg="", timeout=TIMEOUT, rect=None, threshold=0.5):
    try:
        return _loop_find(v, timeout=timeout, rect=rect, threshold=threshold)
    except MoaNotFoundError:
        raise AssertionError("%s does not exists" % v)


@logwrap
def assert_not_exists(v, msg="", timeout=TIMEOUT, rect=None):
    try:
        pos = _loop_find(v, timeout=timeout, rect=rect)
        raise AssertionError("%s exists unexpectedly at pos: %s" % (v, pos))
    except MoaNotFoundError:
        pass


@logwrap
def assert_equal(first, second, msg=""):
    print "assert equal:", msg
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
    # set_basedir()
    # set_logfile('run.log')
    # touch('weixin.jpg', rect=(10, 10, 500, 500))
    # time.sleep(1)
    # home()
    # time.sleep(1)
    # swipe('weixin.jpg', 'qq.jpg')
    # time.sleep(1)
    # swipe('vp.jpg', 'cal.jpg')
    # img = MoaText(u"你妹").img
    # img.show()
    touch(MoaText(u"副 本", font=u"华康唐风隶"))
