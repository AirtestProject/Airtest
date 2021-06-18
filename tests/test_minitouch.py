# encoding=utf-8
from airtest.core.android.android import ADB, Minitouch
import unittest
import warnings
warnings.simplefilter("always")


class TestMiniTouchBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        devices = cls.adb.devices()
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb.serialno = devices[0][0]
        cls.minitouch = Minitouch(cls.adb)

    @classmethod
    def tearDownClass(cls):
        cls.minitouch.teardown()

    def _count_server_proc(self):
        output = self.adb.raw_shell("ps").strip()
        cnt = 0
        for line in output.splitlines():
            if "minitouch" in line and line.split(" ")[-2] not in ["Z", "T", "X"]:
                # 进程状态是睡眠或运行
                cnt += 1
        return cnt


class TestMiniTouch(TestMiniTouchBase):

    def test_touch(self):
        self.minitouch.touch((100, 100))

    def test_swipe(self):
        self.minitouch.swipe((100, 100), (200, 200))

    def test_swipe_along(self):
        self.minitouch.swipe_along([(100, 100), (200, 200), (300, 300)])

    def test_two_finger_swipe(self):
        self.minitouch.two_finger_swipe((100, 100), (200, 200))

    def test_pinch(self):
        self.minitouch.pinch()
        self.minitouch.pinch(in_or_out='out')


class TestMiniTouchBackend(TestMiniTouch):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        devices = cls.adb.devices()
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb.serialno = devices[0][0]
        cls.minitouch = Minitouch(cls.adb, backend=True)


class TestMiniTouchSetup(TestMiniTouchBase):

    def test_0_install(self):
        self.minitouch.uninstall()
        self.minitouch.install()

    def test_teardown(self):
        self.minitouch.touch((0, 0))
        cnt = self._count_server_proc()
        self.minitouch.teardown()
        self.assertEqual(self._count_server_proc(), cnt - 1)


if __name__ == '__main__':
    unittest.main()
