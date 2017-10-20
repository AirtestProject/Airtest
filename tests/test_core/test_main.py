# encoding=utf-8
from airtest.core.main import *
from airtest.core.helper import G
from airtest.core.android import Android
from airtest.core.error import AirtestError, AdbError, AdbShellError
import unittest

THISDIR = os.path.dirname(__file__)
DIR = lambda x: os.path.join(THISDIR, x)
APK = DIR("../../playground/test_blackjack.owl/blackjack-release-signed.apk")
PKG = "org.cocos2d.blackjack"


class TestMainOnAndroid(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        if not isinstance(G.DEVICE, Android):
            connect_device("Android:///")
        self.dev = G.DEVICE

    def test_shell(self):
        output = shell("pwd")
        self.assertIn("/", output)

    def test_shell_error(self):
        with self.assertRaises(AdbShellError):
            output = shell("nimeqi")
            self.assertIn("nimei: not found", output)

    def test_install(self):
        if PKG in self.dev.list_app():
            uninstall(APK)
        install(APK)
        self.assertIn(PKG, self.dev.list_app())

    def test_uninstall(self):
        if PKG not in self.dev.list_app():
            install(APK)
        uninstall(PKG)
        self.assertNotIn(PKG, self.dev.list_app())

    def test_start_app(self):
        if PKG not in self.dev.list_app():
            install(APK)
        start_app(PKG)

    def test_amclear(self):
        if PKG not in self.dev.list_app():
            install(APK)
        clear_app(PKG)

    def test_amstop(self):
        if PKG not in self.dev.list_app():
            install(APK)
        start_app(PKG)
        stop_app(PKG)

    def test_snapshot(self):
        filename = DIR("./screen.png")
        if os.path.exists(filename):
            os.remove(filename)
        snapshot(filename=filename)
        self.assertTrue(os.path.exists(filename))

    def test_wake(self):
        wake()

    def test_home(self):
        home()

    def test_touch_pos(self):
        touch((1, 1))

    def test_swipe(self):
        swipe((0, 0), (10, 10))

    def test_text(self):
        text("input")

    # def test_wait_and_exist(self):
    #     if TEST_PKG not in self.dev.list_app():
    #         install(TEST_APK)
    #     amstop(TEST_PKG)
    #     amstart(TEST_PKG)
        
    #     wait(TARGET_PIC, resolution=(1536, 2048))

    #     exists(TARGET_PIC, resolution=(1536, 2048))

    #     pos = assert_exists(TARGET_PIC, resolution=(1536, 2048))
    #     self.assertIsNotNone(pos)

    # def test_assert_equal(self):
    #     with self.assertRaises(AssertionError):
    #         assert_equal(1, 2)

    #     assert_equal(1, 1)

    # def test_assert_not_equal(self):
    #     with self.assertRaises(AssertionError):
    #         assert_not_equal(1, 1)

    #     assert_not_equal(1, 2)

    # def test_touch_pic(self):
    #     if TEST_PKG not in self.dev.list_app():
    #         install(TEST_APK)
    #     amstop(TEST_PKG)
    #     amstart(TEST_PKG)
    #     touch(TARGET_PIC, resolution=(1536, 2048))

    #     # no base dir specified
    #     with self.assertRaises(Exception):
    #         touch("test.png", resolution=(1536, 2048))

    #     with self.assertRaises(RuntimeError):
    #         touch("/test.png", resolution=(1536, 2048))

    # def test_logcat(self):
    #     for i in logcat("nimei", "V", read_timeout=2):
    #         print (i)

    # # todo need fix "AttributeError: 'module' object has no attribute 'DEVICE'"
    # def _test_set_current(self):
    #     set_current(0)
    #     self.assertIs(main.DEVICE, main.DEVICE_LIST[0])

    #     with self.assertRaises(IndexError):
    #         set_current(10)


if __name__ == '__main__':
    unittest.main()
