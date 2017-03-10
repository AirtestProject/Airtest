from airtest.core.android.android import Android, ADB, Minicap, Minitouch
from airtest.core.error import MoaError
import axmlparserpy.apk as apkparser
import os
import time
import numpy
import unittest


TEST_APK = os.path.join(os.path.dirname(__file__), 'Rabbit.apk')
TEST_PKG = "org.cocos.Rabbit"


class TestAndroid(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.serialno = ADB().devices(state="device")[0][0]
        self.android = Android(self.serialno)

    def test_serialno(self):
        self.assertEqual(self.android.serialno, self.serialno)

    def test_adb(self):
        self.assertIsInstance(self.android.adb, ADB)

    def test_size(self):
        self.assertIn("width", self.android.size)
        self.assertIn("height", self.android.size)
        self.assertIn("orientation", self.android.size)
        self.assertIn("rotation", self.android.size)

    def test_minicap(self):
        minicap = self.android.minicap
        self.assertIsInstance(minicap, Minicap)
        self.assertIs(minicap.size, self.android.size)

    def test_minitouch(self):
        self.assertIsInstance(self.android.minitouch, Minitouch)

    def test_list_app(self):
        self.assertIsInstance(self.android.list_app(), list)
        self.assertIsInstance(self.android.list_app(third_only=True), list)

    def test_path_app(self):
        package = self.android.list_app()[0]
        self.assertIsInstance(self.android.path_app(package), str)

    def test_path_app_error(self):
        with self.assertRaises(MoaError):
            self.android.path_app('test_error')

    def test_check_app(self):
        package = self.android.list_app()[0]
        self.assertIsInstance(self.android.check_app(package), str)

    def test_check_app_error(self):
        with self.assertRaises(MoaError):
            self.android.check_app('test_error')

    def test_install_start_stop_uninstall(self):
        apk = apkparser.APK(TEST_APK)
        apk_package = apk.get_package()
        print apk.get_activities()
        if apk_package in self.android.list_app():
            self.android.uninstall_app(apk_package)
        self.android.install_app(TEST_APK, 'com.netease.test', check=False)
        self.android.start_app(apk_package, TEST_PKG)
        self.android.stop_app(apk_package)
        # test reinstall function
        self.android.install_app(TEST_APK, 'com.netease.test', reinstall=True)
        self.android.start_app(apk_package)
        self.android.stop_app(apk_package)
        self.android.uninstall_app(apk_package)

    def test_snapshot(self):
        screen = self.android.snapshot(filename="test.png")
        self.assertIsInstance(screen, numpy.ndarray)
        self.assertIs(os.path.exists("test.png"), True)
        os.remove("test.png") 

    def test_shell(self):
        self.assertIsInstance(self.android.shell('ls'), str)

    def test_keyevent(self):
        self.android.keyevent("BACK")

    def test_wake_screen_on(self):
        self.android.wake()
        self.assertIs(self.android.is_screenon(), True)

    def test_home(self):
        self.android.home()
    
    def test_text(self):
        self.android.text('test text')

    def test_toggle_shell_ime(self):
        self.android.toggle_shell_ime()
        self.android.toggle_shell_ime(on=False)

    def test_touch(self):
        self.android.touch((100, 100))

    def test_swipe(self):
        self.android.swipe((100, 100), (300, 300))

    def test_operate(self):
        self.android.operate({"type": "down", "x": 100, "y": 100})
        self.android.operate({"type": "move", "x": 200, "y": 200})
        self.android.operate({"type": "move", "x": 300, "y": 300})
        self.android.operate({"type": "up"})

    def test_start_recording(self):
        if self.android.adb.sdk_version >= 20:
            self.android.start_recording(max_time=30)
            time.sleep(3)
            self.android.stop_recording()
            self.assertIs(os.path.exists("screen.mp4"), True)
            os.remove("screen.mp4")

    def test_start_recording_error(self):
        if self.android.adb.sdk_version >= 20:
            try:
                self.android.start_recording(max_time=30)
                time.sleep(3)
                self.android.start_recording(max_time=30)
            except Exception, e:
                self.assertIsInstance(e, MoaError)
            finally:
                try:
                    self.android.stop_recording()
                    os.remove("screen.mp4")
                except:
                    pass

    def test_stop_recording_error(self):
        with self.assertRaises(MoaError):
            self.android.stop_recording()

    def test_get_top_activity_name_and_pid(self):
        res = self.android.get_top_activity_name_and_pid()
        if res:
            self.assertIsInstance(res, tuple)

    def test_get_top_activity_name(self):
        res = self.android.get_top_activity_name()
        if res:
            self.assertIsInstance(res, str)


if __name__ == '__main__':
    unittest.main()
