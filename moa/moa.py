#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx gzliuxin
# Created: 2015-05-17 20:30
# Modified: 2015-06-09

"""
Moa = AIRADB + AIRCV + thisfile

Script engine.
"""

__version__ = '0.0.1'
__all__ = [
    'set_serialno', 'set_basedir', 'set_logfile',
    'snapshot', 'touch', 'swipe', 'home', 'keyevent', 'type', 'wake',
    'log', 'wait', 'exists', 'sleep', 'assert_exists', 'exec_string', 'exec_script',
    'is_screenon', 'wake', 'get_devices', 'get_top_activity_name', 'get_top_activity_name_and_pid',
    'is_keyboard_shown', 'unlock',
    'gevent_run'
    ]

DEBUG = True
AIRADB = 'adb.airtest.nie.netease.com'
AIRCV = '10.246.13.180:7311' # master
AIRCV = '10.246.13.180:7756' # dev
#AIRCV = '10.246.13.180:5000' # test
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
ADB = None
KEEP_CAPTURE = False
RECENT_CAPTURE = None


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
import requests
import socket
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from error import MoaError, MoaNotFoundError
from core import get_devices
import core


def set_address((host, port)):
    global ADDRESS
    ADDRESS = (host, port)
    # FIXME(ssx): need to verify


def set_serialno(sn):
    ''' support filepath match patten '''
    global SERIALNO
    global ADB
    if not sn:
        devs = get_devices(state='device', addr=ADDRESS)
        devs = list(devs)
        if len(devs) != 1:
            raise MoaError("SerialNo empty, Assert device count {} != 1".format(len(devs)))
        SERIALNO = devs[1][0]
    else:
        exists = 0
        status = None
        for (serialno, st) in get_devices(addr=ADDRESS):
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
    ADB = core.ADB(SERIALNO, addr=ADDRESS)
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


def log(tag, data):
    ''' Not thread safe '''
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

def _oper(action, params):
    r = requests.post('http://{0}/api/devices/{1}/operation'.format(AIRADB, SERIALNO),
        data={'action': action, 'params': json.dumps(params)})
    if r.status_code != 200:
        raise MoaError(r.text)
    data = r.json()
    if not data['success']:
        raise MoaError(data['message'])

def _isstr(s):
    return isinstance(s, basestring)

def _islist(v):
    return isinstance(v, list) or isinstance(v, tuple)

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

def _pic2pos(picdata, rect=None):
    ''' find picture position in screen '''
    if KEEP_CAPTURE and RECENT_CAPTURE is not None:
        screen = RECENT_CAPTURE
    else:
        screen = snapshot()
    offsetx, offsety = (0,0)
    if rect is not None and len(rect) == 4:
        x0, y0, x1, y1 = rect
        r = requests.post('http://{}/api/opencv/crop'.format(AIRCV),
            files={'file': screen},
            data={'startx': x0, 'starty': y0, 'endx': x1, 'endy': y1})
        if r.status_code != 200:
            raise MoaError("Crop image use air-opencv error: " + r.text)
        screen = r.content
        (offsetx, offsety) = (x0, y0)

    r = requests.post('http://{0}/api/opencv/locate-element'.format(AIRCV), files={
        'background': screen,
        'target': picdata,
        })
    data = r.json()
    if data.get('success'):
        (x, y) = data['data']['result'].get('point')
        return offsetx+x, offsety+y

def _loop_find(picfile, background=None, timeout=TIMEOUT, rect=None):
    pos = None
    left = max(1, int(timeout))
    picfile = os.path.join(BASE_DIR, picfile)
    picdata = open(picfile, 'rb').read()
    while left > 0:
        pos = _pic2pos(picdata, rect=rect)
        if pos is None:
            time.sleep(1)
            left -= 1
            continue
        return pos
    if pos is None:
        raise MoaNotFoundError('Picture %s not found' % picfile)


def shell(cmd, shell=True):
    if ADB is None:
        raise MoaError("Should call set_serialno(...) at first")
    return ADB.shell(cmd)

def _get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for port in range(13000, 14000):
        if s.connect_ex(('127.0.0.1', port)) != 0:
            return port #('127.0.0.1', port)
    raise MoaError("No free address avaliable")

def _install_air_native():
    upgrade = True
    exists = "imhere" in ADB.shell("test -x /data/local/tmp/air-android-native && echo imhere")
    print 'exists', exists
    if exists:
        if 'fixme: version' == ADB.shell('/data/local/tmp/air-android-native -version').strip():
            upgrade = False
    if upgrade:
        # FIXME
        print 'install air-native'


def init_air_native():
    forwarded = False
    for (serialno, local, remote) in ADB.get_forwards():
        if serialno == SERIALNO and remote == 'tcp:7037':
            AIR_NATIVE_ADDR = ('127.0.0.1', int(local[4:]))
            forwarded = True
            break
    if not forwarded:
        port = _get_free_port()
        ADB.forward('tcp:'+str(port), 'tcp:7037')
        AIR_NATIVE_ADDR = ('127.0.0.1', port)

    try:
        req = requests.head('http://%s:%d/api/version' % AIR_NATIVE_ADDR)
        if req.status_code != 200:
            raise NameError("Status code != 200")
    except (requests.ConnectionError, NameError) as e:
        print 'detected', e
        _install_air_native()



@logwrap
def amstart(package):
    output = shell(['pm', 'path', package], shell=False)
    if not output.startswith('package:'):
        raise MoaError('amstart package not found')
    shell(['monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1'], shell=False)

@logwrap
def amstop(package):
    shell(['am', 'force-stop', package], shell=False)

@logwrap
def amclear(package):
    shell(['pm', 'clear', package], shell=False)

@logwrap
def snapshot(filename=None):
    global RECENT_CAPTURE
    r = requests.get('http://{0}/api/devices/{1}/screen'.format(AIRADB, SERIALNO))
    if r.status_code != 200:
        raise MoaError(r.text)

    if _isstr(filename):
        open(filename, 'wb').write(r.content)

    _show_screen(r.content)
    RECENT_CAPTURE = r.content # used for keep_capture()
    return r.content

def keep_capture(flag=True):
    global KEEP_CAPTURE
    KEEP_CAPTURE = flag

@logwrap
def wake():
    ADB.wake()

@logwrap
def home():
    shell(["input", "keyevent", "HOME"])

@logwrap
def touch(v, rect=None, timeout=TIMEOUT):
    if _isstr(v):
        pos = _loop_find(v, timeout=timeout, rect=rect)
        #pos = (offset[0]+pos[0], offset[1]+pos[1])
    else:
        pos = v
    print 'touch pos:', pos
    TOUCH_POINTS[time.time()] = {'type': 'touch', 'value': pos}
    log('touchpos', pos)
    ADB.touch(*pos)
    #_oper('touch', {'pos': pos})

@logwrap
def swipe(v1, v2):
    if _isstr(v1) and _isstr(v2):
        pos1, pos2 = _loop_find(v1), _loop_find(v2)
    else:
        pos1, pos2 = v1, v2
    ADB.swipe(pos1, pos2)
    #_oper('swipe', {'from': pos1, 'to': pos2})

@logwrap
def keyevent(keyname):
    shell(["input", "keyevent", keyname])

@logwrap
def type(text):
    shell(["input", "text", text])

@logwrap
def sleep(secs=1.0):
    time.sleep(secs)

@logwrap
def wait(v, timeout=10, safe=False):
    try:
        return _loop_find(v, timeout=timeout)
    except RuntimeError:
        if not safe:
            raise
        return None

@logwrap
def exists(v, rect=None):
    try:
        return _loop_find(v, timeout=1, rect=rect)
    except MoaNotFoundError as e:
        return False

@logwrap
def assert_exists(v, msg="", timeout=TIMEOUT, rect=None):
    print "assert exists:", v, msg
    try:
        return _loop_find(v, timeout=timeout, rect=rect)
    except RuntimeError:
        raise AssertionError("%s does not exists" % v)

@logwrap
def assert_equal(first, second, msg=""):
    print "assert equal:", msg
    result = (first == second)
    if not result:
        raise AssertionError("%s and %s are not equal" % (first, second))


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


def exec_script(code):
    """secure matter to be fix"""
    #print "in moa", repr(code)
    tree = ast.parse(code)
    exec(compile(tree, filename="<ast>", mode="exec"))

def is_screenon():
    screenOnRE = re.compile('mScreenOnFully=(true|false)')
    m = screenOnRE.search(shell('dumpsys window policy'))
    if m:
        return (m.group(1) == 'true')
    raise MoaError("Couldn't determine screen ON state")

def wake():
    if not is_screenon():
        shell('input keyevent POWER')

def get_top_activity_name_and_pid():
    dat = shell('dumpsys activity top')
    lines = dat.replace('\r', '').splitlines()
    activityRE = re.compile('\s*ACTIVITY ([A-Za-z0-9_.]+)/([A-Za-z0-9_.]+) \w+ pid=(\d+)')
    m = activityRE.search(lines[1])
    if m:
        return (m.group(1), m.group(2), m.group(3))
    else:
        warnings.warn("NO MATCH:" + lines[1])
        return None

def get_top_activity_name():
    tanp = get_top_activity_name_and_pid()
    if tanp:
        return tanp[0] + '/' + tanp[1]
    else:
        return None

def is_keyboard_shown():
    dim = shell('dumpsys input_method')
    if dim:
        return "mInputShown=true" in dim
    return False

def is_locked():
    lockScreenRE = re.compile('mShowingLockscreen=(true|false)')
    m = lockScreenRE.search(shell('dumpsys window policy'))
    if m:
        return (m.group(1) == 'true')
    raise MoaError("Couldn't determine screen lock state")

def unlock():
    # REWRITE ME
    if SERIALNO == 'cff039ebb31fa11':
        ADB.swipe((360, 915), (370, 1203))
    else:
        shell('input keyevent MENU')
        shell('input keyevent BACK')

def test():
    set_serialno('9a4b171d')
    set_basedir('../taskdata/1433820164')
    #wake()
    #touch('target.png')
    #touch([100, 200])
    #swipe([100, 500], [800, 600])
    #exec_string('touch("target.png", timeout=3)')
    exec_script('touch("target.png", timeout=3)\nhome()')


if __name__ == '__main__':
    import sys
    # serialno, base_dir, script = sys.argv[1: 4]
    # print sys.argv[1: 4]
    set_serialno('cff039ebb31fa11')
    # set_serialno('9a4b171d')

    # set_basedir(base_dir)
    set_logfile('xx.log')
    touch('earth.png')
    # exec_script(script.decode('string-escape'))

    # import urllib
    # serialno, base_dir, script = sys.argv[1: 4]
    # # print sys.argv[1: 4]
    # set_serialno(serialno)
    # set_basedir(base_dir)
    # exec_script(urllib.unquote(script))
