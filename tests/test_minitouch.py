# encoding=utf-8
from airtest.core.android.android import ADB, Minitouch
import unittest


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
        output = self.adb.raw_shell("ps | grep minitouch | grep -v do_exit").strip()
        print(output)
        if output:
            return len(output.splitlines())
        else:
            return 0


class TestMiniTouch(TestMiniTouchBase):

    def test_touch(self):
        self.minitouch.touch((100, 100))

    def test_swipe(self):
        self.minitouch.swipe((100, 100), (200, 200))

    def test_pinch(self):
        self.minitouch.pinch()
        self.minitouch.pinch(in_or_out='out')


class TestMiniTouchSetup(TestMiniTouchBase):

    def test_0_install(self):
        self.minitouch.uninstall()
        self.minitouch.install()

    def test_teardown(self):
        self.minitouch.touch((0, 0))
        self.minitouch.teardown()
        self.assertEqual(self._count_server_proc(), 0)


if __name__ == '__main__':
    unittest.main()
