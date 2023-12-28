# encoding=utf-8
import os
import time
import numpy
import unittest
from threading import Thread
from airtest.core.android.android import Android, ADB, Minicap, Minitouch, IME_METHOD, CAP_METHOD, TOUCH_METHOD
from airtest.core.error import AirtestError
from .testconf import APK, PKG, try_remove
import warnings
warnings.simplefilter("always")


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
        self.assertIsInstance(self.android.adb.display_info, dict)
        print(self.android.display_info)
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

        for i in (CAP_METHOD.ADBCAP, CAP_METHOD.MINICAP, CAP_METHOD.JAVACAP):
            filename = "./screen.png"
            if os.path.exists(filename):
                os.remove(filename)
            self.android.cap_method = i
            self.android.wake()
            screen = self.android.snapshot(filename=filename)
            self.assertIsInstance(screen, numpy.ndarray)
            self.assertTrue(os.path.exists(filename))
            os.remove(filename)

    def test_snapshot_thread(self):

        def assert_exists_and_remove(filename):
            self.assertTrue(os.path.exists(filename))
            os.remove(filename)

        class ScreenshotThread(Thread):
            def __init__(self, dev, assert_true):
                self.dev = dev
                self._running = True
                self.assert_true = assert_true
                super(ScreenshotThread, self).__init__()
                self.dev.snapshot("screen_thread.jpg")
                assert_exists_and_remove("screen_thread.jpg")

            def terminate(self):
                self._running = False

            def run(self):
                while self._running:
                    filename = "screen_thread.jpg"
                    self.dev.snapshot(filename)
                    assert_exists_and_remove(filename)
                    time.sleep(2)

        task = ScreenshotThread(self.android, self.assertTrue)
        task.daemon = True
        task.start()

        for i in range(10):
            self.android.snapshot("screen.jpg")
            assert_exists_and_remove("screen.jpg")
            time.sleep(2)

        task.terminate()

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

    def test_clipboard(self):
        for i in range(10):
            text1 = "test clipboard" + str(i)
            self.android.set_clipboard(text1)
            self.assertEqual(self.android.get_clipboard(), text1)
            self.android.paste()

        self.android.paste()

        # test escape special char
        text2 = "test clipboard with $pecial char #@!#%$#^&*()'"
        self.android.set_clipboard(text2)
        self.assertEqual(self.android.get_clipboard(), text2)
        self.android.paste()

    def test_touch(self):
        for i in (TOUCH_METHOD.ADBTOUCH, TOUCH_METHOD.MINITOUCH, TOUCH_METHOD.MAXTOUCH):
            self.android.touch_method = i
            self.android.touch((100, 100))

    def test_touch_percentage(self):
        for i in (TOUCH_METHOD.ADBTOUCH, TOUCH_METHOD.MINITOUCH, TOUCH_METHOD.MAXTOUCH):
            self.android.touch_method = i
            self.android.touch((0.5, 0.5))
            time.sleep(2)
            self.android.keyevent("BACK")

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

    def test_swipe_percentage(self):
        for i in (TOUCH_METHOD.ADBTOUCH, TOUCH_METHOD.MINITOUCH, TOUCH_METHOD.MAXTOUCH):
            self.android.touch_method = i
            self.android.swipe((0.6, 0.5), (0.4, 0.5))
            self.android.swipe((0.3, 0.5), (0.6, 0.5), fingers=1)
            self.android.swipe((0.1, 0.1), (0.3, 0.3), fingers=2)

        with self.assertRaises(Exception):
            self.android.swipe((0.1, 0.1), (0.3, 0.3), fingers=3)

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

    def test_swipe_along_percentage(self):
        coordinates_list = [(0.1, 0.3), (0.7, 0.3), (0.1, 0.7), (0.8, 0.8)]
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

    def test_two_findger_swipe_percentage(self):
        for i in (TOUCH_METHOD.MINITOUCH, TOUCH_METHOD.MAXTOUCH):
            self.android.touch_method = i
            self.android.two_finger_swipe((0.1, 0.1), (0.2, 0.2))
            self.android.two_finger_swipe((0.1, 0.1), (0.2, 0.2), duration=3, steps=10)
            self.android.two_finger_swipe((0.1, 0.1), (0.2, 0.2), offset=(-0.02, 0.1))
            self.android.two_finger_swipe((0.1, 0.1), (0.2, 0.2), offset=(-0.2, 0.1))
        self.android.touch_method = TOUCH_METHOD.ADBTOUCH
        with self.assertRaises(Exception):
            self.android.two_finger_swipe((0.1, 0.1), (0.2, 0.2))

    def test_disconnect(self):
        self.android.snapshot()
        self.android.touch((100, 100))
        self.android.disconnect()
        # 检查是否将所有forward的端口都断开了
        self.assertEqual(len(self.android.adb._forward_local_using), 0)
        # 断开后，如果再次连接也仍然可以正常使用，并且要正确地在退出时进行清理（检查log中没有warning）
        self.android.snapshot()
        self.assertEqual(len(self.android.adb._forward_local_using), 1)


if __name__ == '__main__':
    unittest.main()
