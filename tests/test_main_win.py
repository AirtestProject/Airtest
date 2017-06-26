import os
import unittest
import numpy
from airtest.core.main import *
from airtest.core import main


TEST_APK = os.path.join(os.path.dirname(__file__), 'Rabbit.apk')
TEST_PKG = "org.cocos.Rabbit"
TARGET_PIC = os.path.join(os.path.dirname(__file__), 'target.png')


class TestAirtestOnWindows(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        set_windows()
        self.dev = main.DEVICE

    def test_home(self):
        with self.assertRaises(NotImplementedError):
            home()

    def test_wake(self):
        with self.assertRaises(NotImplementedError):
            wake()

    def test_shell(self):
        with self.assertRaises(NotImplementedError):
            shell()

    def test_snapshot(self):
        main.SAVE_SCREEN = None
        screen = snapshot()
        self.assertIsInstance(screen, numpy.ndarray)
        self.assertTrue(os.path.exists("screen.png"))
        os.remove("screen.png")
        screen2 = snapshot("test.png")
        self.assertTrue(os.path.exists("test.png"))
        os.remove("test.png")

    def test_touch(self):
        touch((20, 20), right_click=True)
        touch((1, 1))


if __name__ == '__main__':
    unittest.main()
    # suite = unittest.TestSuite()
    # suite.addTest(TestAirtestOnAndroid("test_touch_pic"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)
