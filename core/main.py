#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx gzliuxin
# Created: 2015-05-17 20:30
# Modified: 2015-06-09
# Modified: 2015-10-13 ver 0.0.2 gzliuxin
# Modified: 2016-04-28 ver 0.0.3 gzliuxin

"""
Moa for Android/Windows/iOS
Moa Android = ADB + AIRCV + MINICAP + MINITOUCH
Script engine.
"""

__version__ = '0.0.3'

import os
import shutil
import time
import functools
import fnmatch
import traceback
from moa.aircv import aircv
from moa.aircv import generate_character_img as textgen
from moa.core.error import MoaError, MoaNotFoundError
from moa.core.utils import _isstr, MoaLogger, Logwrap, TargetPos
from moa.core.settings import *
from moa.core import android
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
            print get_platform(), on
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
        devs = list(android.adb_devices(state='device', addr=addr))
        if len(devs) > 1:
            print ("more than one device, auto choose one, to specify serialno: set_serialno(sn)")
        elif len(devs) == 0:
            raise MoaError("no device, please check your adb connection")
        sn = devs[0][0]
    else:
        for (serialno, st) in android.adb_devices(addr=addr):
            if not fnmatch.fnmatch(serialno, sn):
                continue
            if st != 'device':
                raise MoaError("Device status not good: %s" % (st,))
            sn = serialno
            break
        if sn is None:
            raise MoaError("Device[%s] not found in %s" % (sn, addr))
    global CVSTRATEGY, DEVICE, PLAYRES
    CVSTRATEGY = CVSTRATEGY or CVSTRATEGY_ANDROID
    DEVICE = android.Android(sn, addr=addr, minicap=minicap, minitouch=minitouch)
    PLAYRES = [DEVICE.size["width"], DEVICE.size["height"]]
    return sn

def set_udid(udid=None):
    '''
    auto set if only one device
    support filepath match patten, eg: c123*
    '''

    udids = ios.utils.list_all_udid()
    if not udid:
        if len(udids) > 1:
            print ("more than one device, auto choose one, to specify serialno: set_udid(udid)")
        elif len(udids) == 0:
            raise MoaError("no device, please check your connection")
        udid = udids[0]
    else:
        for id in udids:
            if not fnmatch.fnmatch(id,udid):
                continue
            udid = id
        if udid is None:
            raise MoaError("Device[%s] not found" % udid)
        
    global CVSTRATEGY,DEVICE,PLAYRES
    if not CVSTRATEGY:
        CVSTRATEGY = ["siftpre", "siftnopre", "tpl"]
    DEVICE = ios.client.IOS(udid)
    PLAYRES = [DEVICE.size["width"], DEVICE.size["height"]]
    return udid

def resign(ipaname):
    """resign an app, only valid on Mac"""

    import platform
    os_name = platform.system()
    if os_name != "Darwin":  # Mac os name
        raise MoaError("can't resign ipa on %s OS" %os_name)

    new_ipaname = ios.resign.sign(ipaname)
    return new_ipaname


def set_windows():
    if win is None:
        raise RuntimeError("win module is not available")
    global DEVICE, CVSTRATEGY, RESIZE_METHOD
    DEVICE = win.Windows()
    CVSTRATEGY = CVSTRATEGY or CVSTRATEGY_WINDOWS
    # set no resize on windows as default
    RESIZE_METHOD = RESIZE_METHOD or aircv.no_resize


def set_basedir(base_dir):
    global BASE_DIR
    BASE_DIR = base_dir


def set_logfile(filename=LOGFILE, inbase=True):
    global LOGGER
    basedir = BASE_DIR if inbase else ""
    filepath = os.path.join(filename, basedir)
    LOGGER.set_logfile(filepath)


def set_screendir(dirpath=SCREEN_DIR):
    global SAVE_SCREEN
    # force clear dir
    shutil.rmtree(dirpath, ignore_errors=True)
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)
    SAVE_SCREEN = dirpath


def set_threshold(value):
    global THRESHOLD
    if value > 1 or value < 0:
        raise MoaError("invalid threshold: %s"%value)
    THRESHOLD = value


def set_scripthome(dirpath):
    global SCRIPTHOME
    SCRIPTHOME = dirpath


def set_globals(key, value):
    globals()[key] = value


def set_mask_rect(mask_rect=None):
    if mask_rect:
        global MASK_RECT

        str_rect = mask_rect.split(',')
        mask_rect = []
        for i in str_rect:
            try:
                mask_rect.append(max(int(i), 0)) # 如果有负数，就用0 代替
            except:
                MASK_RECT = None
                return
        # global MASK_RECT
        MASK_RECT = mask_rect
        print 'MASK_RECT in moa changed : ', MASK_RECT
    else:
        print "pass wrong IDE rect into moa.MASK_RECT."


def _find_pic(picdata, rect=None, threshold=THRESHOLD, target_pos=TargetPos.MID, record_pos=[], sch_resolution=[], templateMatch=False, find_in=None):
    ''' find picture position in screen '''
    '''mask_rect: 原图像中需要被白色化的区域——IDE的所在区域.'''
    # 如果是KEEP_CAPTURE, 就取上次的截屏，否则重新截屏
    if KEEP_CAPTURE and RECENT_CAPTURE is not None:
        screen = RECENT_CAPTURE
    else:
        screen = snapshot()

    # 如果截屏失败，则screen为空，打印提示后，识别结果直接返回None
    if screen is None:
        print "Cannot captured SCREEN : SCREEN is None !"
        return None
    # 临时措施：将屏幕文件写出后，再使用OpenCV方法读出来：
    # 改进思路:(core.py中的snapshot()函数调用了aircv.string_2_img(screen))
    aircv.cv2.imwrite("screen.png", screen)
    screen = aircv.imread("screen.png")

    # 建军添加：进行IDE区域的遮挡：
    global MASK_RECT
    if MASK_RECT:
        screen = aircv.cv2.rectangle(screen, (MASK_RECT[0],MASK_RECT[1]), (MASK_RECT[2],MASK_RECT[3]), (255,255,255), -1)

    #---------------稍后再aircv内实现，遮住图像某一半，达到指定左右对半区域的查找：
    # 如果在左半边寻找，遮住右半边图像；如果在右半边寻找，遮住左半边图像。
    if find_in=="left":
        h, w = screen.shape[:2]
        screen = aircv.cv2.rectangle(screen, (w/2, 0), (w, h), (255,255,255), -1)
    elif find_in=="right":
        h, w = screen.shape[:2]
        screen = aircv.cv2.rectangle(screen, (0, 0), (w/2,h), (255,255,255), -1)

    # 在rect矩形区域内查找，有record_pos之后，基本上没用
    offsetx, offsety = 0, 0
    if rect is not None and len(rect) == 4:
        if len(filter(lambda x: (x<=1 and x>=0), rect)) == 4:
            x0, y0, x1, y1 = rect[0] * DEVICE.size["width"], rect[1] * DEVICE.size["height"], rect[2] * DEVICE.size["width"], rect[3] * DEVICE.size["height"]
        else:
            x0, y0, x1, y1 = rect
        screen = aircv.crop(screen, (x0, y0), (x1, y1))
        offsetx, offsety = x0, y0
    # 三种不同的匹配算法：
    try:
        if templateMatch is True:
            print "method: matchtpl"
            device_resolution = SRC_RESOLUTION or DEVICE.getCurrentScreenResolution()
            ret = aircv.find_template_after_pre(screen, picdata, sch_resolution=sch_resolution, src_resolution=device_resolution, design_resolution=[960, 640], threshold=0.6, resize_method=RESIZE_METHOD)
        #三个参数要求：点击位置press_pos=[x,y]，搜索图像截屏分辨率sch_pixel=[a1,b1]，源图像截屏分辨率src_pixl=[a2,b2]
        #如果调用时四个要求参数输入不全，不调用区域预测，仍然使用原来的方法：
        elif not record_pos:
            print "method: siftnopre"
            ret = aircv.find_sift(screen, picdata)
        #三个要求的参数均有输入时，加入区域预测部分：
        else:
            print "method: siftpre"
            _pResolution = DEVICE.getCurrentScreenResolution()
            ret = aircv.find_sift_by_pre(screen, picdata, _pResolution, record_pos[0], record_pos[1])
    except aircv.Error:
        ret = None
    except Exception as err:
        traceback.print_exc()
        ret = None
    # print ret
    _log_in_func({"cv": ret})
    if not ret:
        return None
    if threshold and ret["confidence"] < threshold:
        return None
    pos = TargetPos().getXY(ret, target_pos)
    return int(pos[0] + offsetx), int(pos[1] + offsety)


@logwrap
def _loop_find(pictarget, timeout=TIMEOUT, interval=CVINTERVAL, threshold=None, intervalfunc=None, find_in=None):
    '''
    find_in: 用于windows的测试时双开，
            find_in="left"时，只在左半边屏幕中寻找(双屏幕的话只在左屏幕中寻找)
            find_in="left"时，只在右半边屏幕中寻找(双屏幕的话只在右屏幕中寻找)
    '''
    print "\nTry finding:\n %s" % pictarget
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
                    pos = _find_pic(picdata, threshold=threshold, rect=pictarget.rect, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos, find_in=find_in)
                elif st == "siftnopre":
                    # 在预测区域没有找到，则退回全局查找
                    pos = _find_pic(picdata, threshold=threshold, target_pos=pictarget.target_pos, find_in=find_in)
                elif st == "tpl" and getattr(pictarget, "resolution"):
                    # 再用缩放后的模板匹配来找
                    pos = _find_pic(picdata, threshold=threshold, rect=pictarget.rect, target_pos=pictarget.target_pos, record_pos=pictarget.record_pos, sch_resolution=pictarget.resolution, templateMatch=True, find_in=find_in)
                else:
                    print "skip CV_STRATEGY:%s"%st
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
@platform(on=["Android","IOS"])
def amstart(package, activity=None):
    if get_platform() == "IOS":
        DEVICE.launch_app(package) # package = appid
        return

    DEVICE.amstart(package, activity)
    refresh_device()

@logwrap
@platform(on=["Android","IOS"])
def amstop(package):
    if get_platform() == "IOS": # package = appid
        DEVICE.stop_app(package)
        return

    DEVICE.amstop(package)
    refresh_device()


@logwrap
@platform(on=["Android"])
def amclear(package):
    DEVICE.amclear(package)

@logwrap
@platform(on=["Android","IOS"])
def install(filepath, clean=False, **kwargs):
    return DEVICE.install(filepath)

@logwrap
@platform(on=["Android", "IOS"])
def reinstall(filepath, package):
    return DEVICE.reinstall(filepath, package)

@logwrap
@platform(on=["Android","IOS"])
def uninstall(package):
    return DEVICE.uninstall(package)


@logwrap
@platform(on=["Android", "Windows", "IOS"])
def snapshot(filename="screen.png"):
    global RECENT_CAPTURE, SAVE_SCREEN
    if SAVE_SCREEN:
        filename = "%s.jpg" % int(time.time()*1000)
        filename = os.path.join(SAVE_SCREEN, filename)
        _log_in_func({"screen": filename})
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


@platform(on=["Android"])
def refresh_device():
    time.sleep(REFRESH_SCREEN_DELAY)
    DEVICE.refreshOrientationInfo()


@logwrap
@_transparam
@platform(on=["Android", "Windows"])
def touch(v, timeout=TIMEOUT, delay=OPDELAY, offset=None, safe=False, times=1, right_click=False, duration=0.01, find_in=None):
    '''
    @param offset: {'x':10,'y':10,'percent':True}
    '''
    if _isstr(v) or isinstance(v, (MoaPic, MoaText)):
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
            pos = (pos[0] + offset['x'] * w / 100, pos[1] + offset['y'] * h / 100)
        else:
            pos = (pos[0] + offset['x'], pos[1] + offset['y'])
        print ('touchpos after offset', pos)
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
        if _isstr(v1) or isinstance(v1, MoaPic) or isinstance(v1, MoaText):
            pos1 = _loop_find(v1, find_in=find_in)
        else:
            pos1 = v1

        if v2:
            if (_isstr(v2) or isinstance(v2, MoaText)):
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
@platform(on=["Android","Windows"])
def operate(v, route, timeout=TIMEOUT, delay=OPDELAY, find_in=None):
    if _isstr(v) or isinstance(v, MoaPic) or isinstance(v, MoaText):
        pos = _loop_find(v, timeout=timeout, find_in=find_in)
    else:
        pos = v
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
def sleep(secs=1.0):
    time.sleep(secs)


@logwrap
@_transparam
def wait(v, timeout=TIMEOUT, safe=False, interval=CVINTERVAL, intervalfunc=None, find_in=None):
    try:
        pos = _loop_find(v, timeout=timeout, interval=interval, intervalfunc=intervalfunc, find_in=find_in)
        return pos
    except MoaNotFoundError:
        if not safe:
            raise
        return None


@logwrap
@_transparam
def exists(v, timeout=1, find_in=None):
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
        pos = _loop_find(v, timeout=timeout, threshold=THRESHOLD_STRICT, find_in=find_in)
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
    elif type(first)==type(second):
        result = (first == second)

    if not result:
        raise AssertionError("%s and %s are not equal" % (first, second))

    time.sleep(delay)


@logwrap
def assert_not_equal(first, second, msg="", delay=OPDELAY):
    if isinstance(second, unicode) or isinstance(first, unicode):
        result = (unicode(first) == unicode(second))
    elif type(first)==type(second):
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
    home()
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
    set_windows()
    swipe("win.png", (300, 300))
    sleep(1.0)
    swipe("win.png", vector=(0.3, 0.3))
    touch("win.png")

def test_ios():
    basedir = os.path.dirname(os.path.abspath(__file__))
    new_ipaname = resign(os.path.join(basedir,"ios/mhxy_mobile2016-05-20-09-58_265402_resign.ipa"))
    print new_ipaname
    udid = set_udid()
    print udid
    install(new_ipaname)
    # amstart("com.netease.devtest")
    # screen_filename = os.path.join(basedir,'tmp.png')
    # snapshot(screen_filename)
    # uninstall("com.netease.devtest")


if __name__ == '__main__':
    test_android()
    # test_ios()
