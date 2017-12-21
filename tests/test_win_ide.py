# encoding=utf-8
from airtest.core.win import Windows, WindowsInIDE
import unittest
import numpy


class TestWin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        w = Windows()
        w.start_app("calc")
        top_window = w.app.top_window().wrapper_object()
        cls.windows = WindowsInIDE(top_window.handle)

    def test_snapshot(self):
        result = self.windows.snapshot(filename="win_snapshot.png")
        self.assertIsInstance(result, numpy.ndarray)

    def test_touch(self):
        self.windows.touch((11, 11))

    def test_swipe(self):
        self.windows.swipe((11, 11), (100, 100))

    @classmethod
    def tearDownClass(cls):
        cls.windows.app.kill()


if __name__ == '__main__':
    unittest.main()
