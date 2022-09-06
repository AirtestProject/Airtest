# encoding=utf-8
from airtest.core.api import *
from airtest.core.helper import G
from airtest.core.android.android import Android, CAP_METHOD
from airtest.core.error import TargetNotFoundError, AdbShellError
from .testconf import APK, PKG, TPL, TPL2, DIR
import unittest


class TestMainOnAndroid(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not isinstance(G.DEVICE, Android):
            connect_device("Android:///")
        ST.CVSTRATEGY = ['tpl']  # 'tpl' is enough for these tests
        cls.dev = G.DEVICE

    def test_connect(self):
        old = len(G.DEVICE_LIST)
        d = connect_device("Android://localhost:5037/?cap_method=JAVACAP")
        self.assertEqual(len(G.DEVICE_LIST) - old, 1)
        self.assertIs(d, G.DEVICE)
        self.assertEqual(d.cap_method, CAP_METHOD.JAVACAP)
        set_current(0)

    def test_device(self):
        d = device()
        self.assertIs(d, G.DEVICE)

    def test_set_current(self):
        set_current(0)
        self.assertIs(G.DEVICE, G.DEVICE_LIST[0])

        with self.assertRaises(IndexError):
            set_current(len(G.DEVICE_LIST))

    def test_shell(self):
        output = shell("pwd")
        self.assertIn("/", output)

    def test_shell_error(self):
        with self.assertRaises(AdbShellError):
            output = shell("nimeqi")
            self.assertIn("nimei: not found", output)

    def test_install(self):
        if PKG in self.dev.list_app():
            uninstall(PKG)
        install(APK)
        self.assertIn(PKG, self.dev.list_app())

    def test_uninstall(self):
        if PKG not in self.dev.list_app():
            install(APK)
        uninstall(PKG)
        self.assertNotIn(PKG, self.dev.list_app())

    def test_start_app(self):
        if PKG not in self.dev.list_app():
            install(APK)
        start_app(PKG)

    def test_clear_app(self):
        if PKG not in self.dev.list_app():
            install(APK)
        clear_app(PKG)

    def test_stop_app(self):
        if PKG not in self.dev.list_app():
            install(APK)
        start_app(PKG)
        stop_app(PKG)

    def test_snapshot(self):
        filename = DIR("./screen.png")
        if os.path.exists(filename):
            os.remove(filename)
        snapshot(filename=filename)
        self.assertTrue(os.path.exists(filename))

    def test_wake(self):
        wake()

    def test_home(self):
        home()

    def test_touch_pos(self):
        touch((1, 1))

    def test_swipe(self):
        swipe((0, 0), (10, 10))
        swipe((0, 0), (10, 10), fingers=1)
        swipe((0, 0), (10, 10), fingers=2)
        with self.assertRaises(Exception):
            swipe((0, 0), (10, 10), fingers=3)

    def test_pinch(self):
        pinch()

    def test_keyevent(self):
        keyevent("HOME")

    def test_text(self):
        text("input")

    def test_touch_tpl(self):
        self._start_apk_main_scene()
        touch(TPL)

        self._start_apk_main_scene()
        with self.assertRaises(TargetNotFoundError):
            touch(TPL2)

    def test_wait(self):
        self._start_apk_main_scene()
        pos = wait(TPL)
        self.assertIsInstance(pos, (tuple, list))

        with self.assertRaises(TargetNotFoundError):
            wait(TPL2, timeout=5)

    def test_exists(self):
        self._start_apk_main_scene()
        pos = exists(TPL)
        self.assertIsInstance(pos, (tuple, list))
        self.assertFalse(exists(TPL2))

    def _start_apk_main_scene(self):
        if PKG not in self.dev.list_app():
            install(APK)
        stop_app(PKG)
        start_app(PKG)

    def test_log(self):
        log("hello world")
        log({"key": "value"}, timestamp=time.time(), desc="log dict")
        try:
            1 / 0
        except Exception as e:
            log(e)


if __name__ == '__main__':
    unittest.main()
