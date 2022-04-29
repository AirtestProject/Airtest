# encoding=utf-8
import os
import time
import unittest
from airtest.core.android.android import Android
from airtest.core.android.recorder import Recorder
from airtest.core.error import AirtestError
from .testconf import try_remove
import warnings
warnings.simplefilter("always")


class TestAndroidRecorder(unittest.TestCase):
    """Test Android screen recording function"""
    @classmethod
    def setUpClass(cls):
        cls.android = Android()
        cls.filepath = "screen.mp4"

    @classmethod
    def tearDownClass(cls):
        try_remove('screen.mp4')

    def tearDown(self):
        try_remove("screen.mp4")

    def test_recording(self):
        if self.android.sdk_version >= 19:
            self.android.start_recording(max_time=30, bit_rate=500000)
            time.sleep(10)
            self.android.stop_recording()
            self.assertTrue(os.path.exists(self.filepath))
            time.sleep(2)
            # Record the screen with the lower quality
            os.remove(self.filepath)
            self.android.start_recording(bit_rate_level=1)
            time.sleep(10)
            self.android.stop_recording()
            self.assertTrue(os.path.exists(self.filepath))
            os.remove(self.filepath)
            time.sleep(2)
            self.android.start_recording(bit_rate_level=0.5)
            time.sleep(10)
            self.android.stop_recording()
            self.assertTrue(os.path.exists(self.filepath))

    def test_recording_two_recorders(self):
        """测试用另外一个Recorder结束录制"""
        self.android.start_recording(max_time=30)
        time.sleep(6)
        recorder = Recorder(self.android.adb)
        recorder.stop_recording()
        self.assertTrue(os.path.exists(self.filepath))

    def test_start_recording_error(self):
        """测试多次调用start_recording"""
        if self.android.sdk_version >= 19:
            with self.assertRaises(AirtestError):
                self.android.start_recording(max_time=30)
                time.sleep(6)
                self.android.start_recording(max_time=30)

    def test_stop_recording_error(self):
        with self.assertRaises(AirtestError):
            self.android.stop_recording()

    def test_interrupt_recording(self):
        """测试中断录屏但不导出文件"""
        self.android.start_recording(max_time=30)
        time.sleep(3)
        self.android.stop_recording(is_interrupted=True)
        self.assertFalse(os.path.exists(self.filepath))

    def test_pull_last_recording_file(self):
        self.android.start_recording(max_time=30)
        time.sleep(3)
        self.android.stop_recording(is_interrupted=True)
        self.android.recorder.pull_last_recording_file()
        self.assertTrue(os.path.exists(self.filepath))

