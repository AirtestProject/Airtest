# encoding=utf-8
import os
import time
import unittest
import numpy
from airtest.core.ios.ios import IOS, wda
from airtest.core.ios.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD
from airtest.core.error import AirtestError
from testconf import APK, PKG, try_remove


class TestIos(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.ios = IOS()

    @classmethod
    def tearDownClass(self):
        try_remove('screen.png')

    def test_session(self):
        self.assertIsNotNone(self.ios.session)

    def test_wda(self):
        self.assertIsInstance(self.ios.driver, wda.Client)

    """def test_display_info(self):
        self.assertIs(self.android.display_info, self.android.adb.display_info)
        self.assertIn("width", self.android.display_info)
        self.assertIn("height", self.android.display_info)
        self.assertIn("orientation", self.android.display_info)
        self.assertIn("rotation", self.android.display_info)

    def test_minicap(self):
        minicap = self.android.minicap
        self.assertIsInstance(minicap, Minicap)
        self.assertIs(minicap.adb.display_info, self.android.display_info)"""

    def test_snapshot(self):
        
        #  CAP_METHOD.MINICAP, CAP_METHOD.MINICAP_STREAM
        for i in (CAP_METHOD.WDACAP,):
            filename = "./screen.png"
            if os.path.exists(filename):
                os.remove(filename)
            self.ios.cap_method = i

            screen = self.ios.snapshot(filename=filename)
            self.assertIsInstance(screen, numpy.ndarray)
            self.assertTrue(os.path.exists(filename))
            os.remove(filename)

    def test_keyevent(self):
        self.ios.keyevent("BACK")

#    def test_wake(self):
#        self.android.wake()

#    def test_screenon(self):
#        self.assertIn(self.android.is_screenon(), (True, False))

    def test_home(self):
        self.ios.home()

    def test_text(self):
        self.ios.ime_method = IME_METHOD.WDAIME
        self.ios.text('test text')

#        self.android.ime_method = IME_METHOD.YOSEMITEIME
#        self.android.text(u'你好')

    def test_touch(self):
        for i in (TOUCH_METHOD.WDATOUCH,):
            self.ios.touch_method = i
            self.ios.touch((100, 100))

    def test_swipe(self):
        for i in (TOUCH_METHOD.WDATOUCH,):
            self.ios.touch_method = i
            self.ios.swipe((100, 100), (300, 300))

    def test_recording(self):
        pass

    def test_start_recording_error(self):
        pass

    def test_stop_recording_error(self):
        pass
#        with self.assertRaises(AirtestError):
#            self.android.stop_recording()

    def test_interrupt_recording(self):
        pass

    def test_startapp(self):
        self.ios.start_app('com.apple.mobilesafari')

    def test_stopapp(self):
        self.ios.stop_app('com.apple.mobilesafari')

#    def test_is_locked(self):
#        self.android.is_locked()

#    def test_unlock(self):
#        self.android.unlock()



if __name__ == '__main__':
    unittest.main()
