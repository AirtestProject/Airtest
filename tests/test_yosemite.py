# encoding=utf-8
from airtest.core.android.android import ADB, Javacap, YosemiteIme
from airtest.aircv.utils import string_2_img
from numpy import ndarray
import unittest


class TestJavacap(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        devices = cls.adb.devices()
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb.serialno = devices[0][0]
        cls.javacap = Javacap(cls.adb)

    def test_0_get_frame(self):
        frame = self.javacap.get_frame_from_stream()
        frame = string_2_img(frame)
        self.assertIsInstance(frame, ndarray)

    def test_teardown(self):
        self.javacap.get_frame_from_stream()
        self.javacap.teardown_stream()


class TestIme(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        devices = cls.adb.devices()
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb.serialno = devices[0][0]
        cls.ime = YosemiteIme(cls.adb)
        cls.ime.start()

    def test_text(self):
        self.ime.text("nimei")
        self.ime.text("你妹")

    def test_code(self):
        self.ime.text("test code")
        self.ime.code("2")

    def test_0_install(self):
        self.ime.yosemite.install_or_upgrade()
        self.ime.text("安装")

    def test_end(cls):
        cls.ime.end()


if __name__ == '__main__':
    unittest.main()
