# encoding=utf-8
from airtest.core.android.android import ADB, Maxtouch
import unittest
import warnings
warnings.simplefilter("always")


class TestMaxTouchBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        devices = cls.adb.devices()
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb.serialno = devices[0][0]
        cls.maxtouch = Maxtouch(cls.adb)

    @classmethod
    def tearDownClass(cls):
        cls.maxtouch.teardown()

    def _count_server_proc(self):
        output = self.adb.raw_shell("ps").strip()
        cnt = 0
        for line in output.splitlines():
            if "app_process" in line and line.split(" ")[-2] not in ["Z", "T", "X"]:
                # 进程状态是睡眠或运行
                cnt += 1
        return cnt


class TestMaxTouch(TestMaxTouchBase):

    def test_touch(self):
        self.maxtouch.touch((100, 100))

    def test_swipe(self):
        self.maxtouch.swipe((100, 100), (200, 200))

    def test_swipe_along(self):
        self.maxtouch.swipe_along([(100, 100), (200, 200), (300, 300)])

    def test_two_finger_swipe(self):
        self.maxtouch.two_finger_swipe((100, 100), (200, 200))

    def test_pinch(self):
        self.maxtouch.pinch()
        self.maxtouch.pinch(in_or_out='out')


class TestMaxTouchBackend(TestMaxTouch):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        devices = cls.adb.devices()
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb.serialno = devices[0][0]
        cls.maxtouch = Maxtouch(cls.adb, backend=True)


class TestMaxTouchSetup(TestMaxTouchBase):

    def test_0_install(self):
        self.maxtouch.uninstall()
        self.maxtouch.install()

    def test_teardown(self):
        self.maxtouch.touch((0, 0))
        cnt = self._count_server_proc()
        self.maxtouch.teardown()
        self.assertEqual(self._count_server_proc(), cnt - 1)


if __name__ == '__main__':
    unittest.main()
