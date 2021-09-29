# encoding=utf-8
from airtest.core.android.android import Android
from airtest.core.android.cap_methods.screen_proxy import ScreenProxy
from airtest.core.android.cap_methods.minicap import Minicap
from airtest.aircv.utils import string_2_img
from numpy import ndarray
import unittest
import warnings
warnings.simplefilter("always")


class TestScreenProxy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dev = Android()
        cls.dev.rotation_watcher.get_ready()

    def test_setup(self):
        # 测试默认的初始化
        screen_proxy = ScreenProxy.auto_setup(self.dev.adb,
                                              rotation_watcher=self.dev.rotation_watcher,
                                              display_id=self.dev.display_id,
                                              ori_function=lambda: self.dev.display_info)
        self.assertIsNotNone(screen_proxy)
        screen_proxy.teardown_stream()

        # 测试指定默认类型初始化
        default_screen = ScreenProxy.auto_setup(self.dev.adb,
                                                default_method="MINICAP")
        self.assertEqual(default_screen.method_name, "MINICAP")
        default_screen.teardown_stream()

        minicap = Minicap(self.dev.adb)
        default_screen2 = ScreenProxy.auto_setup(self.dev.adb, default_method=minicap)
        self.assertEqual(default_screen2.method_name, "MINICAP")

    def test_snapshot(self):
        for name, method in ScreenProxy.SCREEN_METHODS.items():
            # 把所有的截图方法遍历一次，各截一次图片
            cap_method = method(self.dev.adb)
            screen_proxy = ScreenProxy(cap_method)
            img = screen_proxy.snapshot()
            self.assertIsInstance(img, ndarray)
            screen_proxy.teardown_stream()

    def test_get_deprecated_var(self):
        """
        dev.minicap  ->  dev.screen_proxy
        dev.minicap.get_frame_from_stream()  ->  dev.screen_proxy.get_frame_from_stream()

        Returns:

        """
        for name in ["minicap", "javacap"]:
            obj = getattr(self.dev, name)
            self.assertIsInstance(obj, ScreenProxy)
            self.assertIsInstance(obj.snapshot(), ndarray)

    def test_cap_method(self):
        self.assertIn(self.dev.cap_method, ScreenProxy.SCREEN_METHODS.keys())

    def test_set_projection(self):
        # 目前暂时只支持minicap设置projection参数
        if self.dev.cap_method == "MINICAP":
            self.dev.keyevent("HOME")
            default_height = 800
            height = self.dev.display_info.get("height")
            width = self.dev.display_info.get("width")
            scale_factor = min(default_height, height) / height
            projection = (scale_factor * width, scale_factor * height)
            screen = string_2_img(self.dev.screen_proxy.get_frame(projection=projection))
            self.assertEqual(screen.shape[0], default_height)

    def test_custom_cap_method(self):
        """
        Test adding a custom screenshot method
        测试添加一个自定义的截图方法

        Returns:

        """
        from airtest.core.android.cap_methods.base_cap import BaseCap

        class TestCap(BaseCap):
            def get_frame_from_stream(self):
                return b"frame"

        ScreenProxy.register_method("TESTCAP", TestCap)
        # 默认优先初始化为自定义的TestCap
        cap = ScreenProxy.auto_setup(self.dev.adb)
        self.assertIsInstance(cap.screen_method, TestCap)

        ScreenProxy.SCREEN_METHODS.pop("TESTCAP")

    @classmethod
    def tearDownClass(cls):
        cls.dev.rotation_watcher.teardown()
