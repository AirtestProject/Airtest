# encoding=utf-8
import sys
sys.path.append("..\\..\\")


from airtest.core.main import *
from airtest.core import main
from airtest.core.helper import G

import unittest
import mock
from mock import patch, Mock
import win32gui
import numpy
import time
from airtest.core.error import AirtestError, AdbError, AdbShellError

TEST_APK = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Rabbit.apk')

TEST_PKG = "org.cocos.Rabbit"
TARGET_PIC = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'target.png')
SCREEN_PIC = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screen.png')



class TestAirtestOnAndroid(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        if not isinstance(G.DEVICE, main.android.Android):
            set_serialno()
        self.dev = G.DEVICE

    def test_shell(self):
        with self.assertRaises(AdbShellError):
            output = shell("nimeqi")

        # adb shell now have AdbShellError error

        #self.assertIn("nimei: not found", output)

    def test_install(self):
        install(TEST_APK)
        self.assertIn(TEST_PKG, self.dev.list_app())

    def test_uninstall(self):
        if TEST_PKG not in self.dev.list_app():
            install(TEST_APK)
        uninstall(TEST_PKG)

    def test_amstart(self):
        if TEST_PKG not in self.dev.list_app():
            install(TEST_APK)
        amstart(TEST_PKG)

    def test_amclear(self):
        if TEST_PKG not in self.dev.list_app():
            install(TEST_APK)
        amstart(TEST_PKG)
        amclear(TEST_PKG)

    def test_amstop(self):
        if TEST_PKG not in self.dev.list_app():
            install(TEST_APK)
        amstart(TEST_PKG)
        amstop(TEST_PKG)

    def test_snapshot(self):
        main.SAVE_SCREEN = None
        screen = snapshot(filename=SCREEN_PIC)
        #self.assertIsInstance(screen, numpy.ndarray)
        self.assertTrue(os.path.exists(SCREEN_PIC))
        os.remove(SCREEN_PIC)

    def test_wake(self):
        wake()

    def test_home(self):
        home()

    def test_touch_pos(self):
        touch((1, 1))

    def test_swipe(self):
        swipe((0, 0), (10, 10))

    def test_swipe(self):
        text("input")

    def test_wait_and_exist(self):
        if TEST_PKG not in self.dev.list_app():
            install(TEST_APK)
        amstop(TEST_PKG)
        amstart(TEST_PKG)
        
        wait(TARGET_PIC, resolution=(1536, 2048))

        exists(TARGET_PIC, resolution=(1536, 2048))

        pos = assert_exists(TARGET_PIC, resolution=(1536, 2048))
        self.assertIsNotNone(pos)

    def test_assert_equal(self):
        with self.assertRaises(AssertionError):
            assert_equal(1, 2)

        assert_equal(1, 1)

    def test_assert_not_equal(self):
        with self.assertRaises(AssertionError):
            assert_not_equal(1, 1)

        assert_not_equal(1, 2)



    def test_touch_pic(self):
        if TEST_PKG not in self.dev.list_app():
            install(TEST_APK)
        amstop(TEST_PKG)
        amstart(TEST_PKG)
        touch(TARGET_PIC, resolution=(1536, 2048))

        # no base dir specified
        with self.assertRaises(Exception):
            touch("test.png", resolution=(1536, 2048))

        with self.assertRaises(RuntimeError):
            touch("/test.png", resolution=(1536, 2048))

    def test_logcat(self):
        for i in logcat("nimei", "V", read_timeout=2):
            print (i)

    # todo need fix "AttributeError: 'module' object has no attribute 'DEVICE'"
    def _test_set_current(self):
        set_current(0)
        self.assertIs(main.DEVICE, main.DEVICE_LIST[0])

        with self.assertRaises(IndexError):
            set_current(10)


if __name__ == '__main__':
    unittest.main()
    #suite = unittest.TestSuite()
    #suite.addTest(TestAirtestOnAndroid("test_touch_pic"))
    #runner = unittest.TextTestRunner()
    #runner.run(suite)
