# encoding=utf-8
import os
import time
import unittest
import numpy
from airtest.core.ios.ios import IOS, wda
from airtest.core.ios.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD
from airtest.core.error import AirtestError
from testconf import APK, PKG, try_remove

text_flag = True # 控制是否运行text接口用例
alert_flag = True # 控制是否测试alert相关接口用例
addr="http://127.0.0.1:8100" # iOS设备连接参数

class TestIos(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.ios = IOS(addr=addr)


    @classmethod
    def tearDownClass(self):
        try_remove('screen.png')

    def test_session(self):
        print("test_session")
        self.assertIsNotNone(self.ios.session)

    def test_wda(self):
        print("test_wda")
        self.assertIsInstance(self.ios.driver, wda.Client)

    def test_display_info(self):
        print("test_display_info")
        device_infos = self.ios.display_info
        self.assertIn("width", device_infos)
        self.assertIn("height", device_infos)
        self.assertIn("orientation", device_infos)
        print(device_infos)

    def test_snapshot(self):
        print("test_snapshot")
        filename = "./screen.png"
        if os.path.exists(filename):
            os.remove(filename)
        
        screen = self.ios.snapshot(filename=filename)
        self.assertIsInstance(screen, numpy.ndarray)
        self.assertTrue(os.path.exists(filename))
        # os.remove(filename)

    def test_keyevent_home(self):
        print("test_keyevent_home")
        self.ios.keyevent("home")
    
    def test_keyevent_volume_up(self):
        print("test_keyevent_volume_up")
        self.ios.keyevent("voluMeup")
    
    def test_keyevent_volume_down(self):
        print("test_keyevent_volume_down")
        self.ios.keyevent("voluMeDown")


    def test_home(self):
        print("test_home")
        self.ios.home()

    @unittest.skipIf(text_flag, "demonstrating skipping test_text")
    def test_text(self):
        self.ios.text('test text')

    def test_touch(self):
        # 位置参数可为：相对于设备的百分比坐标或者实际的逻辑位置坐标
        print("test_touch")
        self.ios.touch((100, 100))

    def test_swipe(self):
        # 位置参数只能为：相对于设备的百分比坐标
        print("test_swipe")
        self.ios.swipe((0.1, 0.1), (0.3, 0.3))


    def test_startapp(self):
        print("test_startapp")
        self.ios.start_app('com.apple.mobilesafari')

    def test_stopapp(self):
        print("test_stopapp")
        self.ios.stop_app('com.apple.mobilesafari')
    
    def test_lock(self):
        print("test_lock")
        self.ios.lock()

    def test_is_locked(self):
        print("test_is_locked")
        print(self.ios.is_locked())

    def test_unlock(self):
        print("test_unlock")
        self.ios.unlock()

    def test_get_render_resolution(self):
        print("test_get_render_resolution")
        self.ios.get_render_resolution()

    def test_double_click(self):
        print("test_double_click")
        self.ios.double_click(0.5, 0.5)

    def test_app_state(self):
        print("test_app_state")
        print(self.ios.app_state('com.apple.mobilesafari'))

    def test_app_current(self):
        print("test_app_current")
        print(self.ios.app_current())
    
    def test_get_ip_address(self):
        print("test_get_ip_address")
        print(self.ios.get_ip_address())

    def get_device_status(self):
        print("test_get_device_status")
        print(self.ios.device_status())

    @unittest.skipIf(alert_flag, "demonstrating skipping get_alert_exists")
    def get_alert_exists(self):
        print("test_get_alert_exists")
        print(self.ios.alert_exists())

    @unittest.skipIf(alert_flag, "demonstrating skipping get_alert_accept")
    def get_alert_accept(self):
        print("test_get_alert_accept")
        self.ios.alert_accept()

    @unittest.skipIf(alert_flag, "demonstrating skipping get_alert_dismiss")
    def get_alert_dismiss(self):
        print("test_get_alert_dismiss")
        self.ios.alert_dismiss()

    @unittest.skipIf(alert_flag, "demonstrating skipping get_alert_buttons")
    def get_alert_buttons(self):
        print("test_get_alert_buttons")
        print(self.ios.alert_buttons())

    @unittest.skipIf(alert_flag, "demonstrating skipping get_alert_click")
    def get_alert_click(self):
        print("test_get_alert_click")
        self.ios.alert_click(['允许', '好'])

    def test_device_info(self):
        print("test_device_info")
        print(self.ios.device_info())

    def test_home_interface(self):
        print("test_home_interface")
        print(self.ios.home_interface())



if __name__ == '__main__':
    # unittest.main()
    #构造测试集
    suite = unittest.TestSuite()
    # 初始化相关信息
    suite.addTest(TestIos("test_session"))
    suite.addTest(TestIos("test_wda"))
    suite.addTest(TestIos("test_display_info"))
    suite.addTest(TestIos("test_device_info"))
    suite.addTest(TestIos("test_get_ip_address"))
    suite.addTest(TestIos("get_device_status"))
    # 常用接口
    suite.addTest(TestIos("test_snapshot"))
    suite.addTest(TestIos("test_keyevent_home"))
    suite.addTest(TestIos("test_keyevent_volume_up"))
    suite.addTest(TestIos("test_keyevent_volume_down"))
    suite.addTest(TestIos("test_home"))
    suite.addTest(TestIos("test_home_interface"))
    suite.addTest(TestIos("test_touch"))
    suite.addTest(TestIos("test_swipe"))
    # 联合接口，顺序测试：解锁屏、应用启动关闭
    suite.addTest(TestIos("test_is_locked"))
    suite.addTest(TestIos("test_lock"))
    suite.addTest(TestIos("test_is_locked"))
    suite.addTest(TestIos("test_unlock"))
    suite.addTest(TestIos("test_is_locked"))

    suite.addTest(TestIos("test_app_state"))
    suite.addTest(TestIos("test_app_current"))
    suite.addTest(TestIos("test_startapp"))
    suite.addTest(TestIos("test_app_state"))
    suite.addTest(TestIos("test_app_current"))
    suite.addTest(TestIos("test_stopapp"))
    suite.addTest(TestIos("test_app_state"))
    suite.addTest(TestIos("test_app_current"))

    # 特定条件下的测试: 文本输入、弹窗
    suite.addTest(TestIos("test_text"))

    suite.addTest(TestIos("get_alert_exists"))
    suite.addTest(TestIos("get_alert_buttons"))
    suite.addTest(TestIos("get_alert_dismiss"))
    suite.addTest(TestIos("get_alert_accept"))
    suite.addTest(TestIos("get_alert_click"))

    #执行测试
    runner = unittest.TextTestRunner()
    runner.run(suite)
