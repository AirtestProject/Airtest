# encoding=utf-8
import os
import time
import numpy
import unittest
from airtest.core.android.android import Android, ADB, Minicap, Minitouch, IME_METHOD, CAP_METHOD, TOUCH_METHOD
from airtest.core.error import AirtestError
from .testconf import APK, PKG, try_remove


class TestAndroid(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.android = Android()

    @classmethod
    def tearDownClass(self):
        try_remove('screen.mp4')

    def _install_test_app(self):
        if PKG not in self.android.list_app():
            self.android.install_app(APK)

    def test_serialno(self):
        self.assertIsNotNone(self.android.serialno)

    def test_adb(self):
        self.assertIsInstance(self.android.adb, ADB)

    def test_display_info(self):
        self.assertIs(self.android.display_info, self.android.adb.display_info)
        self.assertIn("width", self.android.display_info)
        self.assertIn("height", self.android.display_info)
        self.assertIn("orientation", self.android.display_info)
        self.assertIn("rotation", self.android.display_info)

    def test_minicap(self):
        minicap = self.android.minicap
        self.assertIsInstance(minicap, Minicap)
        self.assertIs(minicap.adb.display_info, self.android.display_info)

    def test_minitouch(self):
        self.assertIsInstance(self.android.minitouch, Minitouch)

    def test_list_app(self):
        self._install_test_app()
        self.assertIn(PKG, self.android.list_app())
        self.assertIn(PKG, self.android.list_app(third_only=True))

    def test_path_app(self):
        self._install_test_app()
        app_path = self.android.path_app(PKG)
        self.assertIn(PKG, app_path)
        self.assertTrue(app_path.startswith("/"))

        with self.assertRaises(AirtestError):
            self.android.path_app('com.netease.this.is.error')

    def test_check_app(self):
        self._install_test_app()
        self.assertTrue(self.android.check_app(PKG))

        with self.assertRaises(AirtestError):
            self.android.check_app('com.netease.this.is.error')

    def test_snapshot(self):
        self._install_test_app()

        for i in (CAP_METHOD.ADBCAP, CAP_METHOD.MINICAP, CAP_METHOD.MINICAP_STREAM, CAP_METHOD.JAVACAP):
            filename = "./screen.png"
            if os.path.exists(filename):
                os.remove(filename)
            self.android.cap_method = i
            self.android.wake()
            screen = self.android.snapshot(filename=filename)
            self.assertIsInstance(screen, numpy.ndarray)
            self.assertTrue(os.path.exists(filename))
            os.remove(filename)

    def test_shell(self):
        self.assertEqual(self.android.shell('echo nimei').strip(), 'nimei')

    def test_keyevent(self):
        self.android.keyevent("BACK")

    def test_wake(self):
        self.android.wake()

    def test_screenon(self):
        self.assertIn(self.android.is_screenon(), (True, False))

    def test_home(self):
        self.android.home()

    def test_text(self):
        self.android.ime_method = IME_METHOD.ADBIME
        self.android.text('test text')

        self.android.ime_method = IME_METHOD.YOSEMITEIME
        self.android.text(u'你好')

    def test_touch(self):
        for i in (TOUCH_METHOD.ADBTOUCH, TOUCH_METHOD.MINITOUCH, TOUCH_METHOD.MAXTOUCH):
            self.android.touch_method = i
            self.android.touch((100, 100))

    def test_swipe(self):
        for i in (TOUCH_METHOD.ADBTOUCH, TOUCH_METHOD.MINITOUCH, TOUCH_METHOD.MAXTOUCH):
            self.android.touch_method = i
            self.android.swipe((100, 100), (300, 300))
            self.android.swipe((100, 100), (300, 300), fingers=1)
            self.android.swipe((100, 100), (300, 300), fingers=2)        
        self.android.touch_method = TOUCH_METHOD.ADBTOUCH
        self.android.swipe((100, 100), (300, 300), fingers=3)
        self.android.touch_method = TOUCH_METHOD.MINITOUCH
        with self.assertRaises(Exception):
            self.android.swipe((100, 100), (300, 300), fingers=3)

    def test_recording(self):
        if self.android.sdk_version >= 19:
            filepath = "screen.mp4"
            if os.path.exists(filepath):
                os.remove(filepath)
            self.android.start_recording(max_time=30, bit_rate=500000, vertical=False)
            time.sleep(3)
            self.android.stop_recording()
            self.assertTrue(os.path.exists("screen.mp4"))

    def test_start_recording_error(self):
        if self.android.sdk_version >= 19:
            with self.assertRaises(AirtestError):
                self.android.start_recording(max_time=30)
                time.sleep(3)
                self.android.start_recording(max_time=30)
            self.android.stop_recording()

    def test_stop_recording_error(self):
        with self.assertRaises(AirtestError):
            self.android.stop_recording()

    def test_interrupt_recording(self):
        filepath = "screen.mp4"
        if os.path.exists(filepath):
            os.remove(filepath)
        self.android.start_recording(max_time=30)
        time.sleep(3)
        self.android.stop_recording(is_interrupted=True)
        self.assertFalse(os.path.exists(filepath))

    def test_get_top_activity(self):
        self._install_test_app()
        self.android.start_app(PKG)
        pkg, activity, pid = self.android.get_top_activity()
        self.assertEqual(pkg, PKG)
        self.assertEqual(activity, 'org.cocos2dx.javascript.AppActivity')
        self.assertIsInstance(int(pid), int)

    def test_is_keyboard_shown(self):
        self.android.is_keyboard_shown()

    def test_is_locked(self):
        self.android.is_locked()

    def test_unlock(self):
        self.android.unlock()

    def test_pinch(self):
        for i in (TOUCH_METHOD.MINITOUCH, TOUCH_METHOD.MAXTOUCH):
            self.android.touch_method = i
            self.android.pinch(in_or_out='in')
            self.android.pinch(in_or_out='out')
        self.android.touch_method = TOUCH_METHOD.ADBTOUCH
        with self.assertRaises(Exception):
            self.android.pinch(in_or_out='in')

    def test_swipe_along(self):
        coordinates_list = [(100, 300), (300, 300), (100, 500), (300, 600)]
        for i in (TOUCH_METHOD.MINITOUCH, TOUCH_METHOD.MAXTOUCH):
            self.android.touch_method = i
            self.android.swipe_along(coordinates_list)
            self.android.swipe_along(coordinates_list, duration=3, steps=10)
        self.android.touch_method = TOUCH_METHOD.ADBTOUCH
        with self.assertRaises(Exception):
            self.android.swipe_along(coordinates_list)

    def test_two_finger_swipe(self):
        for i in (TOUCH_METHOD.MINITOUCH, TOUCH_METHOD.MAXTOUCH):
            self.android.touch_method = i
            self.android.two_finger_swipe((100, 100), (200, 200))
            self.android.two_finger_swipe((100, 100), (200, 200), duration=3, steps=10)
            self.android.two_finger_swipe((100, 100), (200, 200), offset=(-20, 100))
            self.android.two_finger_swipe((100, 100), (200, 200), offset=(-1000, 100))
        self.android.touch_method = TOUCH_METHOD.ADBTOUCH
        with self.assertRaises(Exception):
            self.android.two_finger_swipe((100, 100), (200, 200))


if __name__ == '__main__':
    unittest.main()
