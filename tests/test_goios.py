import os
import unittest
import threading
import time
from airtest.core.ios.goios_helper import GOIOSHelper


class GOIOSTests(unittest.TestCase):

    def setUp(self):
        devices_list = GOIOSHelper.devices()
        self.udid = devices_list[0]

    def test_device_info(self):
        device_info = GOIOSHelper.device_info(self.udid)
        print(device_info)
        self.assertIsInstance(device_info, dict)

    def test_start_app(self):
        GOIOSHelper.start_app(self.udid, "com.apple.mobilesafari")

    def test_stop_app(self):
        GOIOSHelper.stop_app(self.udid, "com.apple.mobilesafari")

    def test_ps(self):
        ps = GOIOSHelper.ps(self.udid)
        print(ps)
        self.assertIsInstance(ps, list)

    def test_ps_wda(self):
        ps_wda = GOIOSHelper.ps_wda(self.udid)
        print(ps_wda)
        self.assertIsInstance(ps_wda, list)

    def test_xctest(self):
        wda_bundle_id = GOIOSHelper.list_wda(self.udid)[0]
        # 创建一个线程，执行xctest
        t = threading.Thread(target=GOIOSHelper.xctest, args=(self.udid, wda_bundle_id), daemon=True)
        t.start()
        time.sleep(5)
        ps_wda = GOIOSHelper.ps_wda(self.udid)
        print(ps_wda)
        self.assertIn(wda_bundle_id, ps_wda)
        time.sleep(5)
        # 终止线程
        t.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
