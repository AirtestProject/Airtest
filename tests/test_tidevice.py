import os
import unittest
import threading
import time
from airtest.core.ios.tidevice_helper import TIDevice


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

    def test_install_app(self):
        ipa_path = os.path.join(os.path.dirname(__file__), "test_app.ipa")
        if not os.path.exists(ipa_path):
            raise FileNotFoundError(f"File {ipa_path} not found, add test_app.ipa by yourself.")
        TIDevice.install_app(self.udid, ipa_path)
        app_list = TIDevice.list_app(self.udid)
        app_bundle_list = [app[0] for app in app_list]
        self.assertIn("com.aijiasuinc.AiJiaSuClient", app_bundle_list)

    def test_uninstall_app(self):
        TIDevice.uninstall_app(self.udid, "com.aijiasuinc.AiJiaSuClient")
        app_list = TIDevice.list_app(self.udid)
        app_bundle_list = [app[0] for app in app_list]
        self.assertNotIn("com.aijiasuinc.AiJiaSuClient", app_bundle_list)

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

    def test_file_operation(self):
        self.file_operation("/DICM")

    def test_file_operation_with_bundle_id(self):
        self.file_operation("/Documents", bundle_id="com.ownbook.notes")

    def file_operation(self, root_dir, bundle_id=None):
        test_dir = root_dir + "/test_folder"
        test_file_name = "test_file.txt"
        local_test_file_name = "test_file_local.txt"
        test_file_content = "test content"
        # 创建一个文件夹
        TIDevice.mkdir(self.udid, test_dir, bundle_id=bundle_id)
        # 检查是否是目录
        self.assertTrue(TIDevice.is_dir(self.udid, test_dir, bundle_id=bundle_id))
        # 推送一个文件
        file_path = os.path.join(os.path.dirname(__file__), test_file_name)
        if not os.path.exists(file_path):  # 创建一个测试文件
            with open(file_path, "w") as f:
                f.write(test_file_content)
        TIDevice.push(self.udid, file_path, test_dir, bundle_id=bundle_id)
        # 列出文件夹
        file_list = TIDevice.ls(self.udid, test_dir, bundle_id=bundle_id)
        self.assertGreater(len(file_list), 0)
        self.assertEqual(file_list[0]["name"], test_file_name)
        # 拉取文件并检查内容
        local_file_path = os.path.join(os.path.dirname(__file__), local_test_file_name)
        TIDevice.pull(self.udid, test_dir + "/" + test_file_name, local_file_path, bundle_id=bundle_id)
        with open(local_file_path, "r") as f:
            self.assertEqual(f.read(), test_file_content)
        os.remove(local_file_path)  # 删除测试文件
        os.remove(file_path)
        # 删除文件并检查
        TIDevice.rm(self.udid, test_dir + "/" + test_file_name, bundle_id=bundle_id)
        file_list = TIDevice.ls(self.udid, test_dir, bundle_id=bundle_id)
        self.assertEqual(len(file_list), 0)
        # 删除文件夹并检查
        TIDevice.rm(self.udid, test_dir, bundle_id=bundle_id)
        file_list = TIDevice.ls(self.udid, root_dir, bundle_id=bundle_id)
        # 校验file_list中没有test_folder
        self.assertNotIn(test_dir, [file["name"] for file in file_list])


if __name__ == '__main__':
    unittest.main()
