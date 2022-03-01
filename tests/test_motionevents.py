# encoding=utf-8
from airtest.core.android.android import ADB, Android
from airtest.core.android.touch_methods.base_touch import MotionEvent, DownEvent, UpEvent, MoveEvent, SleepEvent
import unittest
import warnings
import time
warnings.simplefilter("always")


class TestMotionEvents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.device = Android()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_multi_touch(self):
        """
        测试两指同时点击
        """
        multitouch_event = [
            DownEvent((100, 100), 0),
            DownEvent((300, 300), 1),  # second finger
            SleepEvent(1),
            UpEvent(0), UpEvent(1)]

        self.device.touch_proxy.perform(multitouch_event)

    def test_swipe(self):
        """
        测试滑动
        """
        swipe_event = [DownEvent((500, 500)), SleepEvent(0.1)]

        for i in range(5):
            swipe_event.append(MoveEvent((500 + 100 * i, 500 + 100 * i)))
            swipe_event.append(SleepEvent(0.2))

        swipe_event.append(UpEvent())

        self.device.touch_proxy.perform(swipe_event)

    def test_retry_touch(self):
        """
        测试在指令内容异常时，能够自动尝试重连

        """
        # 在安卓10部分型号手机上，如果乱序发送指令，可能会导致maxtouch断开连接
        events = [MoveEvent((100, 100), 0),  UpEvent(), DownEvent((165, 250), 0), SleepEvent(0.2), UpEvent(), DownEvent((165, 250), 0), SleepEvent(0.2), UpEvent()]
        self.device.touch_proxy.perform(events)
        time.sleep(3)
        self.device.touch((165, 250))

    def test_horizontal(self):
        """
        如果设备是横屏，必须要加上坐标转换（竖屏也可以加）
        """
        ori_transformer = self.device.touch_proxy.ori_transformer
        touch_landscape_point = [DownEvent(ori_transformer((100, 100))), SleepEvent(1), UpEvent()]
        self.device.touch_proxy.perform(touch_landscape_point)



