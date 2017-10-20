# encoding=utf-8
import sys
sys.path.append("..\\..\\")


from airtest.core.main import *
from airtest.core import main
from airtest.core.helper import G
from requests import ConnectionError
import unittest
import mock
from mock import patch,Mock
import win32gui
import numpy
import time


TEST_APK = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Rabbit.apk')

TEST_PKG = "org.cocos.Rabbit"
TARGET_PIC = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'target.png')
SCREEN_PIC = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screen.png')

class TestAirtestOnWindows(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        set_windows()
        self.dev = G.DEVICE

    # these method is not useful in win
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
        screen = snapshot(filename=SCREEN_PIC)
        #self.assertIsInstance(screen, numpy.ndarray)
        self.assertTrue(os.path.exists(SCREEN_PIC))
        os.remove(SCREEN_PIC)

    # mouse touch
    def test_touch(self):
        touch((1, 1), right_click=True)
        touch((1, 1))

        touch((1, 1), offset={'percent': False, 'x': 2, 'y': 2})


    def test_swipe(self):
        swipe((0, 0), (10, 10))


    def test_operate(self):
        operate((1, 1), route=[(0, 0, 1)])

    def test_keyevent(self):
        keyevent("a")

    def test_sleep(self):
        sleep()

class Teststrange(unittest.TestCase):


    def test_1(self):
        with self.assertRaises(RuntimeError) as pe:
            set_emulator()

        # make sure is right exception
        self.assertEqual(
         'Emulator module available on Windows only',
         str(pe.exception)
        )

    def test_2(self):
        with self.assertRaises(ConnectionError):
            set_udid("http://65535/status")

    def test_3(self):
        set_device("Android")


if __name__ == '__main__':
    unittest.main()
    # suite = unittest.TestSuite()
    # suite.addTest(TestAirtestOnAndroid("test_touch_pic"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)
