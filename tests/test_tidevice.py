import unittest
import threading
import time
from airtest.core.ios.ios import TIDevice


class TIDeviceTests(unittest.TestCase):

    def setUp(self):
        devices_list = TIDevice.devices()
        self.udid = devices_list[0]

    def test_devices(self):
        devices_list = TIDevice.devices()
        self.assertIsInstance(devices_list, list)
        if len(devices_list) > 0:
            print(devices_list)
            self.assertIsInstance(devices_list[0], str)
            self.udid = devices_list[0]

    def test_list_app(self):
        app_list = TIDevice.list_app(self.udid)
        print(app_list)
        self.assertIsInstance(app_list, list)
        if len(app_list) > 0:
            self.assertEqual(len(app_list[0]), 3)

    def test_list_app_type(self):
        app_list = TIDevice.list_app(self.udid, app_type='system')
        print(app_list)
        self.assertIsInstance(app_list, list)
        if len(app_list) > 0:
            self.assertEqual(len(app_list[0]), 3)

        app_list_all = TIDevice.list_app(self.udid, app_type='all')
        self.assertGreater(len(app_list_all), len(app_list))

    def test_list_wda(self):
        wda_list = TIDevice.list_wda(self.udid)
        print(wda_list)
        self.assertIsInstance(wda_list, list)

    def test_device_info(self):
        device_info = TIDevice.device_info(self.udid)
        print(device_info)
        self.assertIsInstance(device_info, dict)

    def test_start_app(self):
        TIDevice.start_app(self.udid, "com.apple.mobilesafari")

    def test_stop_app(self):
        TIDevice.stop_app(self.udid, "com.apple.mobilesafari")

    def test_ps(self):
        ps = TIDevice.ps(self.udid)
        print(ps)
        self.assertIsInstance(ps, list)

    def test_ps_wda(self):
        ps_wda = TIDevice.ps_wda(self.udid)
        print(ps_wda)
        self.assertIsInstance(ps_wda, list)

    def test_xctest(self):
        wda_bundle_id = TIDevice.list_wda(self.udid)[0]
        # 创建一个线程，执行xctest
        t = threading.Thread(target=TIDevice.xctest, args=(self.udid, wda_bundle_id), daemon=True)
        t.start()
        time.sleep(5)
        ps_wda = TIDevice.ps_wda(self.udid)
        print(ps_wda)
        self.assertIn(wda_bundle_id, ps_wda)
        time.sleep(5)
        # 终止线程
        t.join(timeout=3)



if __name__ == '__main__':
    unittest.main()
