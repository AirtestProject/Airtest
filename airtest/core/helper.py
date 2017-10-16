# -*- coding: utf-8 -*-
import os
import time
import functools
import aircv
from airtest.core import device
from airtest.core.utils import Logwrap, AirtestLogger, TargetPos, is_str, get_logger, predict_area
from airtest.core.settings import Settings as ST
from airtest.core.utils.compat import PY3
from airtest.core.device import MetaDevice


class G(object):
    """globals variables"""
    BASEDIR = None
    LOGGER = AirtestLogger(None)
    LOGGING = get_logger("main")
    SCREEN = None
    DEVICE = None
    DEVICE_LIST = []
    RECENT_CAPTURE = None
    RECENT_CAPTURE_PATH = None

    @classmethod
    def add_device(cls, dev):
        """初始化设备，加入全局环境, eg:
        init_device(Android())
        """
        cls.DEVICE = dev
        cls.DEVICE_LIST.append(dev)


class Target(object):
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
        self.filepath = os.path.join(G.BASEDIR, filename)
        self.threshold = threshold or ST.THRESHOLD
        self.target_pos = target_pos
        self.record_pos = record_pos
        self.resolution = resolution
        self.new_snapshot = new_snapshot
        self.find_inside = find_inside
        self.find_outside = find_outside
        self.whole_screen = whole_screen
        self.ignore = ignore
        self.focus = focus
        self.rgb = rgb
        self.find_all = find_all

    def __repr__(self):
        return "Target(%s)" % self.filepath

    def get_search_img(self):
        """获取搜索图像(cv2格式)."""
        return aircv.imread(self.filepath)


class Screen(object):
    """保存截屏及截屏相关的参数."""

    def __init__(self, screen=None, img_src=None, offset=None, wnd_pos=None, src_resolution=None):
        self.screen = screen
        self.img_src = img_src
        self.offset = offset
        self.wnd_pos = wnd_pos
        self.src_resolution = src_resolution

    @classmethod
    def create_by_query(cls, screen, find_inside, find_outside, whole_screen, op_pos):
    # def create_by_query(cls, screen, query):
        """求取图像匹配的截屏数据类."""
        # 第一步: 获取截屏
        if not whole_screen and device_platform() == "Windows" and G.DEVICE.handle:
            # win平非全屏识别、且指定句柄的情况:使用hwnd获取有效图像
            # 获取窗口相对于屏幕坐标系的坐标(用于操作坐标的转换)
            wnd_pos = G.DEVICE.get_wnd_pos_by_hwnd(G.DEVICE.handle)
        else:
            wnd_pos = None  # 没有所谓的窗口偏移，设为None
            # 暂时只在全屏截取时才启用find_outside，主要关照IDE调试脚本情形
            screen = aircv.mask_image(screen, find_outside)

        # 检查截屏:
        if not screen.any():
            G.LOGGING.warning("Bad screen capture, check if screen is clocked !")
            screen, img_src, offset, src_resolution = None, None, None, []
        else:
            # 截屏分辨率(注意: 可能游戏分辨率与设备分辨率会有不同.)
            src_resolution = G.DEVICE.getCurrentScreenResolution()
            # 第二步: 封装截屏
            if find_inside:
                # 如果有find_inside，就在find_inside内进行识别
                img_src, offset = aircv.crop_image(screen, find_inside)
            else:
                # 如果没有find_inside，就提取预测区域，进行识别
                radius_x, radius_y = 250, 250
                if op_pos:
                    img_src, offset, log_info = predict_area(screen, op_pos, radius_x, radius_y, src_resolution)
                else:
                    # find_all语句是没有record_pos参数的,此时不要进行预测:
                    img_src, offset, log_info = screen, (0, 0), "no prediction without record_pos"
                G.LOGGING.debug(log_info)  # 输出预测区域的调试信息

        return cls(screen=screen, img_src=img_src, offset=offset, wnd_pos=wnd_pos, src_resolution=src_resolution)


class CvPosFix(object):

    def __init__(self):
        pass

    @classmethod
    def fix_cv_pos(cls, cv_ret, left_top_pos):
        """根据结果类型，进行cv识别结果校正."""
        if isinstance(cv_ret, dict):
            result = cls._fix_one_cv_pos(cv_ret, left_top_pos)
        elif isinstance(cv_ret, list):
            result = [cls._fix_one_cv_pos(item, left_top_pos) for item in cv_ret]
        else:
            pass

        return result

    @classmethod
    def _fix_one_cv_pos(cls, ret, left_top_pos):
        """用于修正cv的识别结果."""
        left_top_x, left_top_y = left_top_pos
        # 在预测区域内进行图像查找时，需要转换到整张图片内的坐标，再进行左上角的位置校准:
        # 进行识别中心result的偏移:
        result_pos = list(ret.get('result'))
        result = [i + j for (i, j) in zip(left_top_pos, result_pos)]
        # 进行识别区域rectangle的偏移:
        rectangle = []
        for point in ret.get('rectangle'):
            tmpoint = [i + j for (i, j) in zip(left_top_pos, point)]  # 进行位置相对left_top_pos进行偏移
            rectangle.append(tuple(tmpoint))
        # 重置偏移后的识别中心、识别区域:
        ret['result'], ret['rectangle'] = tuple(result), tuple(rectangle)

        return ret

    @classmethod
    def cal_target_pos(cls, cv_ret, target_pos):
        # 这个是脚本语句的target_pos的点击偏移处理:
        if isinstance(cv_ret, dict):
            # 非find_all模式，返回的是一个dict，则正常返回即可
            ret_pos = TargetPos().getXY(cv_ret, target_pos)
            return ret_pos
        elif isinstance(cv_ret, list):
            # find_all模式找到的是一个结果列表，处理后返回ret_pos_list
            ret_pos_list = []
            for one_ret in cv_ret:
                ret_pos = TargetPos().getXY(one_ret, target_pos)
                ret_pos_list.append(ret_pos)
            return ret_pos_list
        else:
            return cv_ret


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


def device_platform():
    for name, cls in MetaDevice.REPO.items():
        if G.DEVICE.__class__ == cls:
            return name
    return None


def on_platform(platforms):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            pf = device_platform()
            if pf is None:
                raise RuntimeError("Device not initialized yet.")
            if pf not in platforms:
                raise NotImplementedError("Method not implememted on {}. required {}.".format(pf, platforms))
            r = f(*args, **kwargs)
            return r
        return wrapper
    return decorator


def delay_after_operation():
    time.sleep(ST.OPDELAY)

