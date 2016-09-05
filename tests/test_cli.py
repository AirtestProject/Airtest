import os
import time
import unittest
import axmlparserpy.apk as apkparser
from airtest.core.main import *
from airtest.core import main


TEST_APK = os.path.join(os.path.dirname(__file__), 'Rabbit.apk')
TEST_PKG = apkparser.APK(TEST_APK).get_package()
TARGET_PIC = os.path.join(os.path.dirname(__file__), 'target.png')

class TestMoaOnAndroid(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        set_serialno()
        self.dev = main.DEVICE

    def test_shell(self):
        output = shell("nimei")
        self.assertIn("nimei: not found", output)

    def test_install(self):
        install(TEST_APK)
        self.assertIn(TEST_PKG, self.dev.amlist())

    def test_uninstall(self):
        if TEST_PKG not in self.dev.amlist():
            install(TEST_APK)
        uninstall(TEST_PKG)

    def test_amstart(self):
        if TEST_PKG not in self.dev.amlist():
            install(TEST_APK)
        amstart(TEST_PKG)

    def test_amclear(self):
        if TEST_PKG not in self.dev.amlist():
            install(TEST_APK)
        amstart(TEST_PKG)
        amclear(TEST_PKG)

    def test_amstop(self):
        if TEST_PKG not in self.dev.amlist():
            install(TEST_APK)
        amstart(TEST_PKG)
        amstop(TEST_PKG)

    def test_snapshot(self):
        import numpy
        screen = snapshot()
        self.assertIsInstance(screen, numpy.ndarray)
        self.assertTrue(os.path.exists("screen.png"))
        os.remove("screen.png")
        screen2 = snapshot("test.png")
        self.assertTrue(os.path.exists("test.png"))
        os.remove("test.png")

    def test_wake(self):
        wake()

    def test_home(self):
        home()

    def test_touch_pos(self):
        touch((1, 1))

    def test_touch_pic(self):
        if TEST_PKG not in self.dev.amlist():
            install(TEST_APK)
        amstart(TEST_PKG)

        touch(TARGET_PIC)
        self.assertTrue(os.path.exists("screen.png"))
        os.remove("screen.png")

        with self.assertRaises(RuntimeError):
            touch("test.png")

    def test_logcat(self):
        for i in logcat("nimei", "V", read_timeout=2):
            print i


if __name__ == '__main__':
    unittest.main()
    # suite = unittest.TestSuite()
    # suite.addTest(TestMoaOnAndroid("test_touch_pic"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)
