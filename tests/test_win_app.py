# encoding=utf-8
from tkinter import W
from airtest.core.win import Windows
import unittest
import numpy
import time
from testconf import try_remove

import os
import cv2

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

    def test_record(self):
        self.windows.start_recording(output="test_10s.mp4")
        time.sleep(10+4)
        self.windows.stop_recording()
        time.sleep(2)
        self.assertEqual(os.path.exists("test_10s.mp4"), True)
        duration = 0
        cap = cv2.VideoCapture("test_10s.mp4")
        if cap.isOpened():
            rate = cap.get(5)
            frame_num = cap.get(7)
            duration = frame_num/rate
        self.assertEqual(duration >= 10, True)

    @classmethod
    def tearDownClass(cls):
        cls.windows.app.kill()
        try_remove('test_10s.mp4')
        try_remove('test_cv_10s.mp4')


if __name__ == '__main__':
    unittest.main()
