# encoding=utf-8
from airtest.core.win import Windows
import subprocess
import unittest
import numpy


class TestWin(unittest.TestCase):   

    @classmethod
    def setUpClass(cls):
        cls.windows = Windows()

    def test_shell(self):
        result=self.windows.shell("dir")
        self.assertIn(".", result)
        self.assertIn("..", result)

    def test_snapshot(self):
        result = self.windows.snapshot(filename="win_snapshot.png") 
        self.assertIsInstance(result, numpy.ndarray)

    def test_keyevent(self):
        self.windows.keyevent("abc{ENTER}")

    def test_text(self):
        self.windows.text("abc")

    def test_touch(self):
        self.windows.touch((11, 11))

    def test_swipe(self):
        self.windows.swipe((11, 11), (100, 100))


if __name__ == '__main__':
    unittest.main()



