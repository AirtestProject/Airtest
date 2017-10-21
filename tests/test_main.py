# encoding=utf-8
from airtest.core.main import *
from airtest.core.helper import G
from airtest.core.android import Android
from airtest.core.error import TargetNotFoundError, AdbShellError
from testconf import APK, PKG, TPL, TPL2, DIR
import unittest


class TestMainOnAndroid(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        if not isinstance(G.DEVICE, Android):
            connect_device("Android:///")
        self.dev = G.DEVICE

    def test_connect(self):
        d = connect_device("Android://localhost:5037/?cap_method=javacap")
        self.assertEqual(len(G.DEVICE_LIST), 2)
        self.assertIs(d, G.DEVICE)
        self.assertEqual(d.cap_method, "javacap")

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
            uninstall(APK)
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

    def test_amclear(self):
        if PKG not in self.dev.list_app():
            install(APK)
        clear_app(PKG)

    def test_amstop(self):
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

    def test_assert_exists(self):
        self._start_apk_main_scene()
        assert_exists(TPL)

        with self.assertRaises(AssertionError):
            assert_exists(TPL2)

    def test_assert_not_exists(self):
        self._start_apk_main_scene()
        assert_not_exists(TPL2)

        with self.assertRaises(AssertionError):
            assert_not_exists(TPL)

    def test_assert_equal(self):
        with self.assertRaises(AssertionError):
            assert_equal(1, 2)

        assert_equal(1, 1)

    def test_assert_not_equal(self):
        with self.assertRaises(AssertionError):
            assert_not_equal(1, 1)

        assert_not_equal(1, 2)

    def _start_apk_main_scene(self):
        if PKG not in self.dev.list_app():
            install(APK)
        stop_app(PKG)
        start_app(PKG)


if __name__ == '__main__':
    unittest.main()
