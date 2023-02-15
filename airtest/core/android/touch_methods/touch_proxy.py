# encoding=utf-8
import warnings
from collections import OrderedDict
from airtest.core.android.touch_methods.minitouch import Minitouch
from airtest.core.android.touch_methods.maxtouch import Maxtouch
from airtest.core.android.touch_methods.base_touch import BaseTouch
from airtest.core.android.constant import TOUCH_METHOD
from airtest.utils.logger import get_logger


LOGGING = get_logger(__name__)


class TouchProxy(object):
    """
    Perform touch operation according to the specified method
    """
    TOUCH_METHODS = OrderedDict()

    def __init__(self, touch_method):
        self.touch_method = touch_method

    def __getattr__(self, name):
        if name == "method_name":
            return self.touch_method.METHOD_NAME
        method = getattr(self.touch_method, name, getattr(self.touch_method.base_touch, name, None))
        if method:
            return method
        else:
            raise NotImplementedError("%s does not support %s method" %
                                      (getattr(self.touch_method, "METHOD_NAME", ""), name))

    @classmethod
    def check_touch(cls, touch_impl):
        try:
            touch_impl.base_touch.install_and_setup()
        except Exception as e:
            LOGGING.error(e)
            LOGGING.warning("%s setup up failed!" % touch_impl.METHOD_NAME)
            return False
        else:
            return True

    @classmethod
    def auto_setup(cls, adb, default_method=None, ori_transformer=None, size_info=None, input_event=None):
        """

        Args:
            adb: :py:mod:`airtest.core.android.adb.ADB`
            default_method: The default click method, such as "MINITOUCH"
            ori_transformer: dev._touch_point_by_orientation
            size_info: the result of dev.get_display_info()
            input_event: dev.input_event
            *args:
            **kwargs:

        Returns: TouchProxy object

        Examples:
            >>> dev = Android()
            >>> touch_proxy = TouchProxy.auto_setup(dev.adb, ori_transformer=dev._touch_point_by_orientation)
            >>> touch_proxy.touch((100, 100))

        """
        if default_method and default_method in cls.TOUCH_METHODS:
            touch_method = cls.TOUCH_METHODS[default_method].METHOD_CLASS(adb, size_info=size_info,
                                                                          input_event=input_event)
            impl = cls.TOUCH_METHODS[default_method](touch_method, ori_transformer)
            if cls.check_touch(impl):
                return TouchProxy(impl)

        if not default_method:
            for name, touch_impl in cls.TOUCH_METHODS.items():
                touch_method = touch_impl.METHOD_CLASS(adb, size_info=size_info, input_event=input_event)
                impl = touch_impl(touch_method, ori_transformer)
                if cls.check_touch(impl):
                    return TouchProxy(impl)

        # If both minitouch and maxtouch fail to initialize, use adbtouch
        # 如果minitouch和maxtouch都初始化失败，使用adbtouch
        adb_touch = AdbTouchImplementation(adb)
        warnings.warn("Currently using ADB touch, the efficiency may be very low.")
        return TouchProxy(adb_touch)


def register_touch(cls):
    TouchProxy.TOUCH_METHODS[cls.METHOD_NAME] = cls
    return cls


class AdbTouchImplementation(object):
    METHOD_NAME = TOUCH_METHOD.ADBTOUCH

    def __init__(self, base_touch):
        """

        :param base_touch: :py:mod:`airtest.core.android.adb.ADB`
        """
        self.base_touch = base_touch

    def touch(self, pos, duration=0.01):
        if duration <= 0.01:
            self.base_touch.touch(pos)
        else:
            self.swipe(pos, pos, duration=duration)

    def swipe(self, p1, p2, duration=0.5, *args, **kwargs):
        duration *= 1000
        self.base_touch.swipe(p1, p2, duration=duration)

    def teardown(self):
        pass


@register_touch
class MinitouchImplementation(AdbTouchImplementation):
    METHOD_NAME = TOUCH_METHOD.MINITOUCH
    METHOD_CLASS = Minitouch

    def __init__(self, minitouch, ori_transformer):
        """

        :param minitouch: :py:mod:`airtest.core.android.touch_methods.minitouch.Minitouch`
        :param ori_transformer: Android._touch_point_by_orientation()
        """
        super(MinitouchImplementation, self).__init__(minitouch)
        self.ori_transformer = ori_transformer

    def touch(self, pos, duration=0.01):
        pos = self.ori_transformer(pos)
        self.base_touch.touch(pos, duration=duration)

    def swipe(self, p1, p2, duration=0.5, steps=5, fingers=1):
        p1 = self.ori_transformer(p1)
        p2 = self.ori_transformer(p2)
        if fingers == 1:
            self.base_touch.swipe(p1, p2, duration=duration, steps=steps)
        elif fingers == 2:
            self.base_touch.two_finger_swipe(p1, p2, duration=duration, steps=steps)
        else:
            raise Exception("param fingers should be 1 or 2")

    def pinch(self, center=None, percent=0.5, duration=0.5, steps=5, in_or_out='in'):
        if center:
            center = self.ori_transformer(center)
        self.base_touch.pinch(center=center, percent=percent, duration=duration, steps=steps, in_or_out=in_or_out)

    def swipe_along(self, coordinates_list, duration=0.8, steps=5):
        pos_list = [self.ori_transformer(xy) for xy in coordinates_list]
        self.base_touch.swipe_along(pos_list, duration=duration, steps=steps)

    def two_finger_swipe(self, tuple_from_xy, tuple_to_xy, duration=0.8, steps=5, offset=(0, 50)):
        tuple_from_xy = self.ori_transformer(tuple_from_xy)
        tuple_to_xy = self.ori_transformer(tuple_to_xy)
        self.base_touch.two_finger_swipe(tuple_from_xy, tuple_to_xy, duration=duration, steps=steps, offset=offset)

    def perform(self, motion_events, interval=0.01):
        self.base_touch.perform(motion_events, interval)


@register_touch
class MaxtouchImplementation(MinitouchImplementation):
    METHOD_NAME = TOUCH_METHOD.MAXTOUCH
    METHOD_CLASS = Maxtouch

    def __init__(self, maxtouch, ori_transformer):
        """
        New screen click scheme, support Android10
        新的屏幕点击方案，支持Android10以上版本

        :param maxtouch: :py:mod:`airtest.core.android.touch_methods.maxtouch.Maxtouch`
        :param ori_transformer: Android._touch_point_by_orientation()
        """
        super(MaxtouchImplementation, self).__init__(maxtouch, ori_transformer)

    def perform(self, motion_events, interval=0.01):
        self.base_touch.perform(motion_events, interval)
