# encoding=utf-8
from airtest.core.win import Windows
import os
import time
import numpy
import unittest


class TestWindows(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.windows = Windows()

    @classmethod
    def tearDownClass(self):
        self.windows.stop_app(image="calc.exe")

    def test_shell(self):
        cmds = "ping -n 1 localhost"
        ret = self.windows.shell(cmds)
        self.assertIn("Ping", ret)

    def test_snapshot(self):
        screen = self.windows.snapshot(filename="test.png")
        self.assertIsInstance(screen, numpy.ndarray)
        self.assertIs(os.path.exists("test.png"), True)
        os.remove("test.png")

    def test_start_app(self):
        ret = self.windows.start_app("calc")
        self.assertEqual(ret, 0)

    def test_keyevent(self):
        self.windows.start_app("calc")
        time.sleep(1)
        self.windows.find_window("计算器")
        self.windows.keyevent("1")

    def test_text(self):
        self.windows.start_app("calc")
        time.sleep(1)
        self.windows.find_window("计算器")
        self.windows.text("12")

    def test_stop_app(self):
        # self.windows.stop_app(title="计算器")
        self.windows.stop_app(image="calc.exe")




if __name__ == '__main__':
    unittest.main()
