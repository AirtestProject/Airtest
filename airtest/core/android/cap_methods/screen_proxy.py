# -*- coding: utf-8 -*-
from collections import OrderedDict
from airtest.core.error import AdbError, ScreenError
from airtest.core.android.cap_methods.base_cap import BaseCap
from airtest.utils.logger import get_logger


LOGGING = get_logger(__name__)


class ScreenProxy(object):
    """
    Perform screen operation according to the specified method
    """
    SCREEN_METHODS = OrderedDict()

    def __init__(self, screen_method):
        self.screen_method = screen_method

    def __getattr__(self, name):
        if hasattr(self.screen_method, name):
            return getattr(self.screen_method, name, None)
        elif name == "method_name":
            return self.screen_method.__class__.__name__.upper()
        else:
            raise NotImplementedError("%s does not support \'%s\' method" %
                                      (getattr(self.screen_method, "METHOD_NAME", ""), name))

    def __setattr__(self, name, value):
        if name == "screen_method":
            object.__setattr__(self, name, value)
        else:
            object.__setattr__(self.screen_method, name, value)

    @classmethod
    def register_method(cls, name, method_class):
        cls.SCREEN_METHODS[name] = method_class

    @classmethod
    def check_frame(cls, cap_method):
        """
        Test whether a frame of image can be obtained correctly

        测试能否正确获取一帧图像

        Args:
            cap_method: :py:mod:`airtest.core.android.cap_methods.base_cap.BaseCap`

        Returns:

        """
        try:
            cap_method.get_frame()
        except (AdbError, ScreenError) as e:
            if isinstance(e, AdbError):
                LOGGING.error(repr(e.stdout))
                LOGGING.error(repr(e.stderr))
            else:
                LOGGING.error(e)
            LOGGING.error("%s setup up failed!" % cap_method.__class__.__name__)
            return False
        else:
            return True

    @classmethod
    def auto_setup(cls, adb, default_method=None, *args, **kwargs):
        """
        In order of priority, try to initialize all registered screenshot methods,
        select an available method to return

        按优先顺序，尝试初始化注册过的所有屏幕截图方法，选择一个可用方法返回

        Custom method 自定义方法 > MINICAP > JAVACAP > ADBCAP

        Args:
            adb: :py:mod:`airtest.core.android.adb.ADB`
            default_method: String such as "MINICAP", or :py:mod:`airtest.core.android.cap_methods.minicap.Minicap` object

        Returns: ScreenProxy object

        Examples:
            >>> dev = Android()
            >>> screen_proxy = ScreenProxy.auto_setup(dev.adb, rotation_watcher=dev.rotation_watcher)
            >>> screen_proxy.get_frame_from_stream()
            >>> screen_proxy.teardown_stream()

        """
        screen = None
        if default_method:
            if isinstance(default_method, str) and default_method.upper() in cls.SCREEN_METHODS:
                screen = cls.SCREEN_METHODS[default_method.upper()](adb, *args, **kwargs)
            elif isinstance(default_method, BaseCap):
                screen = default_method
            if screen and cls.check_frame(screen):
                return ScreenProxy(screen)
        # 从self.SCREEN_METHODS中，逆序取出可用的方法
        for name, screen_class in reversed(cls.SCREEN_METHODS.items()):
            if name == default_method:
                continue
            screen = screen_class(adb, *args, **kwargs)
            if cls.check_frame(screen):
                return ScreenProxy(screen)
        # 如果没有找到任何可用方法，抛出异常（但是至少adbcap是可用的）
        raise ScreenError("No available screen capture method found")


def register_screen():
    # 按优先级逆序注册默认的屏幕截图方法
    from airtest.core.android.cap_methods.minicap import Minicap
    from airtest.core.android.cap_methods.javacap import Javacap
    from airtest.core.android.cap_methods.adbcap import AdbCap
    ScreenProxy.SCREEN_METHODS["ADBCAP"] = AdbCap
    ScreenProxy.SCREEN_METHODS["JAVACAP"] = Javacap
    ScreenProxy.SCREEN_METHODS["MINICAP"] = Minicap


register_screen()
