# encoding=utf-8
from airtest.core.android.android import Android, Minicap
from airtest.aircv.utils import string_2_img
from numpy import ndarray
from testconf import PKG
import time
import unittest


class TestMinicapBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dev = Android()
        cls.dev.rotation_watcher.get_ready()
        cls.minicap = cls.dev.minicap

    def _count_server_proc(self):
        output = self.dev.adb.raw_shell("ps").strip()
        cnt = 0
        for line in output.splitlines():
            if "minicap" in line and "do_exit" not in line:
                cnt += 1
        return cnt

    @classmethod
    def tearDownClass(cls):
        cls.minicap.teardown_stream()


class TestMinicap(TestMinicapBase):

    def test_get_display_info(self):
        info = self.minicap.get_display_info()
        self.assertIsInstance(info, dict)

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
        time.sleep(1)
        frame_horizontal = self.minicap.get_frame_from_stream()
        frame_horizontal = string_2_img(frame_horizontal)

        self.assertEqual(frame_vertical.shape[0], frame_horizontal.shape[1])
        self.assertEqual(frame_vertical.shape[1], frame_horizontal.shape[0])
        self.assertEqual(self._count_server_proc(), 1)


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
