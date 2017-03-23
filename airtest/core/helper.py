# -*- coding: utf-8 -*-
import os
import time
import functools
import aircv
from airtest.core import device
from airtest.core.utils import Logwrap, MoaLogger, TargetPos, is_str, get_logger
from airtest.core.settings import Settings as ST


class G(object):
    """globals variables"""
    LOGGER = MoaLogger(None)
    LOGGING = get_logger("main")
    SCREEN = None
    DEVICE = None
    DEVICE_LIST = []
    RECENT_CAPTURE = None
    RECENT_CAPTURE_PATH = None
    WATCHER = {}


class MoaPic(object):
    """
    picture as touch/swipe/wait/exists target and extra info for cv match
    filename: pic filename
    target_pos: ret which pos in the pic
    record_pos: pos in screen when recording
    resolution: screen resolution when recording
    rect: find pic in rect of screen
    find_outside: 在源图像指定区域外寻找. (执行方式：抹去对应区域的图片有效内容)
    find_inside:  在源图像指定区域内寻找，find_inside=[x, y, w, h]时，进行截图寻找.（其中，x,y,w,h为像素值）
    whole_screen: 为True时，则指定在全屏内寻找.
    ignore: [ [x_min, y_min, x_max, y_max], ... ]  识别时，忽略掉ignore包含的矩形区域 (mask_tpl)
    focus: [ [x_min, y_min, x_max, y_max], ... ]  识别时，只识别ignore包含的矩形区域 (可信度为面积加权平均)
    rgb: 识别结果是否使用rgb三通道进行校验.
    find_all: 是否寻找所有满足条件的结果.
    """

    def __init__(self, filename, threshold=None, target_pos=TargetPos.MID, record_pos=None, resolution=[], new_snapshot=True, find_inside=None, find_outside=None, whole_screen=False, ignore=None, focus=None, rgb=False, find_all=False):
        self.filename = filename
        self.filepath = filename if os.path.isabs(filename) else os.path.join(ST.BASE_DIR, filename)
        # 结果可信阈值优先取脚本参数传入的阈值，其次是utils.py中设置的
        self.threshold = threshold or ST.THRESHOLD
        self.target_pos = target_pos
        self.record_pos = record_pos
        self.resolution = resolution
        self.new_snapshot = new_snapshot
        self.find_inside = find_inside or ST.FIND_INSIDE
        self.find_outside = find_outside or ST.FIND_OUTSIDE
        self.whole_screen = whole_screen or ST.WHOLE_SCREEN
        self.ignore = ignore
        self.focus = focus
        self.rgb = rgb
        self.find_all = find_all

    def __repr__(self):
        return "MoaPic(%s)" % self.filepath

    def get_search_img(self):
        """获取搜索图像(cv2格式)."""
        return aircv.imread(self.filepath)


class MoaScreen(object):
    """保存截屏及截屏相关的参数."""

    def __init__(self, screen=None, img_src=None, offset=None, wnd_pos=None, src_resolution=None):
        self.screen = screen
        self.img_src = img_src
        self.offset = offset
        self.wnd_pos = wnd_pos
        self.src_resolution = src_resolution

    @classmethod
    def create_by_query(cls, screen, query):
        """求取图像匹配的截屏数据类."""
        # 第一步: 获取截屏
        if not query.whole_screen and get_platform() == "Windows" and G.DEVICE.handle:
            # win平非全屏识别、且指定句柄的情况:使用hwnd获取有效图像
            # 获取窗口相对于屏幕坐标系的坐标(用于操作坐标的转换)
            wnd_pos = G.DEVICE.get_wnd_pos_by_hwnd(G.DEVICE.handle)
        else:
            wnd_pos = None  # 没有所谓的窗口偏移，设为None
            # 其他情况：手机回放或者windows全屏回放时，使用之前的截屏方法( 截屏offset为0 )
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

        return cls(screen=screen, img_src=img_src, offset=offset, wnd_pos=wnd_pos, src_resolution=src_resolution)

    def predict_area(self):
        pass

    def fix_cv_pos(self):
        pass


class MoaText(object):
    """autogen Text with aircv
        Deprecated!
    """

    def __init__(self, text, font=u"微软雅黑", size=70, inverse=True):
        self.info = dict(text=text, font=font, size=size, inverse=inverse)
        self.img = textgen.gen_text(text, font, size, inverse)
        # self.img.save("text.png")
        self.threshold = THRESHOLD
        self.target_pos = TargetPos.MID

    def __repr__(self):
        return "MoaText(%s)" % repr(self.info)


"""
helper functions
"""


def log(tag, data, in_stack=True):
    if G.LOGGER:
        G.LOGGER.log(tag, data, in_stack)


def log_in_func(data):
    if G.LOGGER:
        G.LOGGER.extra_log.update(data)


def logwrap(f):
    return Logwrap(f, G.LOGGER)


def moapicwrap(f):
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
            if k in ["whole_screen", "find_inside", "find_outside", "ignore", "focus", "threshold", "target_pos", "record_pos", "resolution", "rgb"]:
                picargs[k] = v
            else:
                opargs[k] = v
        pictarget = MoaPic(picname, **picargs)
        return f(pictarget, *args[1:], **opargs)
    return wrapper


def get_platform():
    for name, cls in device.DEV_TYPE_DICT.items():
        if G.DEVICE.__class__ == cls:
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


def register_device(dev):
    G.DEVICE = dev
    G.DEVICE_LIST.append(dev)


def delay_after_operation(secs):
    delay = secs or ST.OPDELAY
    time.sleep(delay)
