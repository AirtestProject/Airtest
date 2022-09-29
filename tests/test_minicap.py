# encoding=utf-8
from airtest.core.android.android import Android
from airtest.core.android.cap_methods.minicap import Minicap
from airtest.aircv.utils import string_2_img
from numpy import ndarray
from .testconf import PKG
import time
import unittest
import warnings
warnings.simplefilter("always")


class TestMinicapBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dev = Android()
        cls.dev.rotation_watcher.get_ready()
        cls.minicap = Minicap(cls.dev.adb, rotation_watcher=cls.dev.rotation_watcher)

    def _count_server_proc(self):
        output = self.dev.adb.raw_shell("ps").strip()
        cnt = 0
        for line in output.splitlines():
            if "minicap" in line and "do_exit" not in line and "R" in line:
                cnt += 1
        return cnt

    @classmethod
    def tearDownClass(cls):
        cls.dev.rotation_watcher.teardown()
        cls.minicap.teardown_stream()


class TestMinicap(TestMinicapBase):

    def test_get_frame(self):
        frame = self.minicap.get_frame()
        frame = string_2_img(frame)
        self.assertIsInstance(frame, ndarray)

    def test_get_frames(self):
        frame = self.minicap.get_frame_from_stream()
        frame = string_2_img(frame)
        self.assertIsInstance(frame, ndarray)

    def test_rotation(self):
        self.dev.keyevent("HOME")
        time.sleep(1)
        frame_vertical = self.minicap.get_frame_from_stream()
        frame_vertical = string_2_img(frame_vertical)
        self.dev.start_app(PKG)
        time.sleep(3)
        frame_horizontal = self.minicap.get_frame_from_stream()
        frame_horizontal = string_2_img(frame_horizontal)

        self.assertEqual(frame_vertical.shape[0], frame_horizontal.shape[1])
        self.assertEqual(frame_vertical.shape[1], frame_horizontal.shape[0])

    def test_projection(self):
        """
        先按home键回到桌面，确保当前是竖屏
        然后设置高度为800，大部分手机竖屏高度都大于这个数值，计算出对应的projection参数
        最后验证截出来的图是否高度等于800
        Returns:

        """
        self.dev.keyevent("HOME")
        default_height = 800
        height = self.dev.display_info.get("height")
        width = self.dev.display_info.get("width")
        scale_factor = min(default_height, height) / height
        projection = (scale_factor * width, scale_factor * height)
        screen = string_2_img(self.minicap.get_frame(projection=projection))
        self.assertEqual(screen.shape[0], default_height)

        self.minicap.projection = projection
        screen_stream = self.minicap.get_frame_from_stream()
        screen2 = string_2_img(screen_stream)
        self.assertEqual(screen2.shape[0], default_height)


class TestMinicapSetup(TestMinicapBase):

    def test_0_install(self):
        self.minicap.uninstall()
        self.minicap.install()

    def test_teardown(self):
        self.minicap.get_frame_from_stream()
        self.minicap.teardown_stream()
        self.assertEqual(self._count_server_proc(), 0)


if __name__ == '__main__':
    unittest.main()
