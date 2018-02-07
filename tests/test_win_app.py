# encoding=utf-8
from airtest.core.win import Windows
import unittest
import numpy
import time
from testconf import try_remove


SNAPSHOT = "win_snapshot.png"


class TestWin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        w = Windows()
        w.start_app("calc")
        time.sleep(1)
        cls.windows = Windows(title_re=".*计算器.*".decode("utf-8"))

    def test_snapshot(self):
        try_remove(SNAPSHOT)
        result = self.windows.snapshot(filename=SNAPSHOT)
        self.assertIsInstance(result, numpy.ndarray)
        try_remove(SNAPSHOT)

    def test_touch(self):
        self.windows.touch((11, 11))

    def test_swipe(self):
        self.windows.swipe((11, 11), (100, 100))

    @classmethod
    def tearDownClass(cls):
        cls.windows.app.kill()


if __name__ == '__main__':
    unittest.main()
