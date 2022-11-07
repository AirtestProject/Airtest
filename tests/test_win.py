# encoding=utf-8
from airtest.core.win import Windows
import unittest
import numpy
import win32api
from testconf import try_remove

import time
import os
import cv2

SNAPSHOT = "win_snapshot.png"


class TestWin(unittest.TestCase):   

    @classmethod
    def setUpClass(cls):
        cls.windows = Windows()

    def test_shell(self):
        result=self.windows.shell("dir").decode('utf-8', 'ignore')
        self.assertIn(".", result)
        self.assertIn("..", result)

    def test_snapshot(self):
        try_remove(SNAPSHOT)
        result = self.windows.snapshot(filename=SNAPSHOT) 
        self.assertIsInstance(result, numpy.ndarray)
        try_remove(SNAPSHOT)

    def test_keyevent(self):
        self.windows.keyevent("abc{ENTER}")

    def test_text(self):
        self.windows.text("abc")

    def test_touch(self):
        self.windows.touch((11, 11))

    def test_swipe(self):
        self.windows.swipe((11, 11), (100, 100))

    def test_key_press_and_key_release(self):
        self.windows.key_press('L')
        self.windows.key_release('L')
        self.windows.key_press('S')
        self.windows.key_release('S')
        self.windows.key_press('ENTER')
        self.windows.key_release('ENTER')

    def test_mouse_move(self):
        self.windows.mouse_move((100, 100))
        self.assertTupleEqual(win32api.GetCursorPos(), (100, 100))
        self.windows.mouse_move((150, 50))
        self.assertTupleEqual(win32api.GetCursorPos(), (150, 50))

    def test_mouse_down_and_mouse_up(self):
        self.windows.mouse_down('left')
        self.windows.mouse_up('left')
        self.windows.mouse_down('middle')
        self.windows.mouse_up('middle')
        self.windows.mouse_down('right')
        self.windows.mouse_up('right')
        self.windows.mouse_down()
        self.windows.mouse_up()
    
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
        
        #test other params
        self.windows.start_recording(output="test_cv_10s.mp4", write_mode="cv2")
        time.sleep(10+4)
        self.windows.stop_recording()
        time.sleep(2)
        self.assertEqual(os.path.exists("test_cv_10s.mp4"), True)
        duration = 0
        cap = cv2.VideoCapture("test_cv_10s.mp4")
        if cap.isOpened():
            rate = cap.get(5)
            frame_num = cap.get(7)
            duration = frame_num/rate
        self.assertEqual(duration >= 10, True)

    @classmethod
    def tearDownClass(cls):
        try_remove('test_10s.mp4')
        try_remove('test_cv_10s.mp4')

if __name__ == '__main__':
    unittest.main()
