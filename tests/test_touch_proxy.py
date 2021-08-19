# encoding=utf-8
import unittest
from airtest.core.android.android import Android
from airtest.core.android.touch_methods.touch_proxy import TouchProxy
import warnings
warnings.simplefilter("always")


class TestTouchProxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dev = Android()
        cls.dev.ori_method = "ADBORI"

    def test_auto_setup(self):
        touch_proxy = TouchProxy.auto_setup(self.dev.adb,
                                            ori_transformer=self.dev._touch_point_by_orientation,
                                            size_info=None,
                                            input_event=None)
        touch_proxy.touch((100, 100))

        touch_proxy = TouchProxy.auto_setup(self.dev.adb,
                                            default_method="MINITOUCH",
                                            ori_transformer=self.dev._touch_point_by_orientation,
                                            size_info=self.dev.display_info,
                                            input_event=self.dev.input_event)
        touch_proxy.touch((100, 100))

    def test_touch_method(self):
        self.assertIn(self.dev.touch_method, TouchProxy.TOUCH_METHODS.keys())

    def test_get_deprecated_var(self):
        for name in ["minitouch", "maxtouch"]:
            obj = getattr(self.dev, name)
            self.assertIsInstance(obj, TouchProxy)
