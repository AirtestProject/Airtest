# encoding=utf-8
import os
import shutil
import time
import unittest
import numpy
from airtest.core.api import *
from airtest.core.ios.ios import IOS, wda, CAP_METHOD
from airtest import aircv
from .testconf import try_remove
import cv2
import warnings
import tempfile
warnings.simplefilter("always")

text_flag = True # 控制是否运行text接口用例
skip_alert_flag = False  # 控制是否测试alert相关接口用例
DEFAULT_ADDR = "http://localhost:8100/"  # iOS设备连接参数
PKG_SAFARI = "com.apple.mobilesafari"
TEST_IPA_FILE_OR_URL = "" # IPA包体的路径或者url链接，测试安装
TEST_IPA_BUNDLE_ID = "" # IPA安装后app的bundleID，测试卸载

class TestIos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # cls.ios = IOS(addr=DEFAULT_ADDR, cap_method=CAP_METHOD.WDACAP)
        cls.ios = connect_device("iOS:///http+usbmux://")
        cls.TEST_FSYNC_APP = "" # 测试文件推送、同步的app的bundleID
        # 获取一个可以用于文件操作的app
        app_list = cls.ios.list_app(type="all")
        if len(app_list) > 0:
            cls.TEST_FSYNC_APP = app_list[0][0]

    @classmethod
    def tearDownClass(cls):
        try_remove('screen.png')
        try_remove('test_10s.mp4')
        try_remove('test_cv_10s.mp4')

    def test_wda(self):
        print("test_wda")
        self.assertIsInstance(self.ios.driver, wda.Client)
        print(self.ios.driver.session())

    def test_display_info(self):
        print("test_display_info")
        device_infos = self.ios.display_info
        self.assertIsInstance(device_infos["width"], int)
        self.assertIsInstance(device_infos["height"], int)
        self.assertIsInstance(device_infos["orientation"], str)
        print(device_infos)

    def test_window_size(self):
        print("test window size")
        window_size = self.ios.window_size()
        print(window_size)
        self.assertIsInstance(window_size.height, int)
        self.assertIsInstance(window_size.width, int)
        # 以下用例可能会因为wda更新而失败，到时候需要去掉 ios._display_info里的ipad横屏下的额外处理
        # 当ipad 在横屏+桌面的情况下，获取到的window_size的值为 height*height，没有width的值
        if self.ios.is_pad and self.client.orientation != 'PORTRAIT' and self.ios.home_interface():
            self.assertEqual(window_size.width, window_size.height)

    def test_using_ios_tagent(self):
        status = self.ios.driver.status()
        print(self.ios.using_ios_tagent)
        self.assertEqual('Version' in status, self.ios.using_ios_tagent)

    def test_snapshot(self):
        print("test_snapshot")
        filename = "./screen.png"
        if os.path.exists(filename):
            os.remove(filename)
        
        screen = self.ios.snapshot(filename=filename)
        self.assertIsInstance(screen, numpy.ndarray)
        self.assertTrue(os.path.exists(filename))

    def test_get_frames(self):
        frame = self.ios.get_frame_from_stream()
        frame = aircv.utils.string_2_img(frame)
        self.assertIsInstance(frame, numpy.ndarray)

    def test_keyevent_home(self):
        print("test_keyevent_home")
        self.ios.keyevent("home")

        with self.assertRaises(ValueError):
            self.ios.keyevent("home1")
    
    def test_keyevent_volume_up(self):
        print("test_keyevent_volume_up")
        self.ios.keyevent("voluMeup")
    
    def test_keyevent_volume_down(self):
        print("test_keyevent_volume_down")
        self.ios.keyevent("voluMeDown")

    def test_press(self):
        with self.assertRaises(ValueError):
            self.ios.press("home1")

        self.ios.press("home")
        self.ios.press("volumeUp")
        self.ios.press("volumeDown")

    def test_home(self):
        print("test_home")
        self.ios.home()
        self.assertTrue(self.ios.home_interface())

    def test_text(self):
        self.ios.start_app("com.apple.mobilenotes")
        self.ios.touch((0.5, 0.5))
        self.ios.text('test text')
        self.ios.text('中文')
        self.ios.stop_app("com.apple.mobilenotes")

    def test_touch(self):
        # 位置参数可为：相对于设备的百分比坐标或者实际的逻辑位置坐标
        print("test_touch")
        self.ios.touch((480, 350), duration=0.1)
        time.sleep(2)
        self.ios.home()
        time.sleep(2)
        self.ios.touch((0.3, 0.3))

    def test_swipe(self):
        print("test_swipe")
        # 右往左滑
        self.ios.swipe((1050, 1900), (150, 1900))
        time.sleep(2)
        # 左往右滑
        self.ios.swipe((0.2, 0.5), (0.8, 0.5))
        # 上往下滑，按住0.5秒后往下滑动
        self.ios.swipe((0.5, 0.1), (0.5, 0.5), duration=0.5)

    def test_lock(self):
        print("test_lock")
        self.ios.lock()

    def test_is_locked(self):
        print("test_is_locked")
        self.ios.unlock()
        self.assertTrue(not self.ios.is_locked())

    def test_unlock(self):
        print("test_unlock")
        self.ios.unlock()

    def test_get_render_resolution(self):
        print("test_get_render_resolution")
        self.ios.get_render_resolution()

    def test_double_click(self):
        print("test_double_click")
        self.ios.double_click((0.5, 0.5))
        time.sleep(1)
        self.ios.double_click((100, 100))

    def test_startapp(self):
        print("test_startapp")
        self.ios.start_app(PKG_SAFARI)

    def test_general_api(self):
        print("test_general_api")
        start_app(PKG_SAFARI)
        stop_app(PKG_SAFARI)
        start_app("com.apple.mobilenotes")
        set_clipboard("Legends never die.")
        cliboard_text = get_clipboard()
        self.assertEqual(cliboard_text, "Legends never die.")

    def test_stopapp(self):
        print("test_stopapp")
        self.ios.stop_app(PKG_SAFARI)
        stop_app(PKG_SAFARI)

    def test_app_state(self):
        print("test_app_state")
        self.ios.start_app(PKG_SAFARI)
        print(self.ios.app_state(PKG_SAFARI))
        self.assertEqual(self.ios.app_state(PKG_SAFARI)["value"], 4)
        time.sleep(1)
        self.ios.home()
        time.sleep(1)
        print(self.ios.app_state(PKG_SAFARI))
        self.assertEqual(self.ios.app_state(PKG_SAFARI)["value"], 3)
        self.ios.stop_app(PKG_SAFARI)
        time.sleep(1)
        print(self.ios.app_state(PKG_SAFARI))
        self.assertEqual(self.ios.app_state(PKG_SAFARI)["value"], 1)

    def test_app_current(self):
        print("test_app_current")
        self.ios.start_app(PKG_SAFARI)
        time.sleep(2)
        self.assertEqual(self.ios.app_current()["bundleId"], PKG_SAFARI)
        self.ios.stop_app(PKG_SAFARI)
    
    def test_get_ip_address(self):
        print("test_get_ip_address")
        print(self.ios.get_ip_address())

    def test_device_status(self):
        print("test_get_device_status")
        status = self.ios.device_status()
        print(status)
        self.assertIsInstance(status, dict)

    @unittest.skipIf(skip_alert_flag, "demonstrating skipping get_alert_exists")
    def test_alert_exists(self):
        # alert测试方法：手机开飞行模式断网，打开天气app，会弹出提示需要关闭飞行模式
        # 重复测试时，需要先关闭app-关闭飞行模式-开启app-关闭app，然后重新开飞行模式
        # 未安装手机sim卡时，在取消飞行模式的时候也会弹出一个“未安装SIM卡”的提示
        print("test_get_alert_exists")
        print(self.ios.alert_exists())

    @unittest.skipIf(skip_alert_flag, "demonstrating skipping get_alert_accept")
    def test_alert_accept(self):
        print("test_get_alert_accept")
        self.assertTrue(self.ios.alert_exists())
        print(self.ios.alert_accept())

    @unittest.skipIf(skip_alert_flag, "demonstrating skipping get_alert_dismiss")
    def test_alert_dismiss(self):
        print("test_get_alert_dismiss")
        self.ios.alert_dismiss()

    @unittest.skipIf(skip_alert_flag, "demonstrating skipping get_alert_buttons")
    def test_alert_buttons(self):
        print("test_get_alert_buttons")
        print(self.ios.alert_buttons())
        print(self.ios.driver.alert.text)

    @unittest.skipIf(skip_alert_flag, "demonstrating skipping get_alert_click")
    def test_alert_click(self):
        print("test_get_alert_click")
        self.ios.alert_click(['设置', '允许', '好'])

    @unittest.skipIf(skip_alert_flag, "demonstrating skipping get_alert_click")
    def test_alert_watch_and_click(self):
        with self.ios.alert_watch_and_click(['Cancel']):
            time.sleep(5)

        # default watch buttons are
        # ["使用App时允许", "好", "稍后", "稍后提醒", "确定", "允许", "以后"]
        with self.ios.alert_watch_and_click(interval=2.0):  # default check every 2.0s
            time.sleep(5)

    def test_device_info(self):
        print("test_device_info")
        print(self.ios.device_info)

    def test_home_interface(self):
        print("test_home_interface")
        self.ios.home()
        time.sleep(2)
        self.assertTrue(self.ios.home_interface())

    def test_touch_factor(self):
        """
        在部分特殊型号的设备上，可能默认的touch_factor不能正确点击对应的位置，因此需要修正
        Returns:

        """
        print("test touch factor")
        print("ios.driver.scale:", self.ios.driver.scale)
        print("display_info:", self.ios.display_info)
        print("default touch_factor:", self.ios.touch_factor)
        self.ios.touch((500, 500))
        self.ios.touch_factor = 1/3.3
        self.ios.touch((500, 500))

    def test_disconnect(self):
        print("test_disconnect")
        self.ios.cap_method = CAP_METHOD.MJPEG
        self.ios.get_frame_from_stream()
        self.ios.disconnect()
        self.assertEqual(len(self.ios.instruct_helper._port_using_func.keys()), 0)
    
    def test_record(self):
        self.ios.start_recording(output="test_10s.mp4")
        time.sleep(10+4)
        self.ios.stop_recording()
        time.sleep(2)
        self.assertEqual(os.path.exists("test_10s.mp4"), True)
        duration = 0
        cap = cv2.VideoCapture("test_10s.mp4")
        if cap.isOpened():
            rate = cap.get(5)
            frame_num = cap.get(7)
            duration = frame_num/rate
        self.assertEqual(duration >= 10, True)
        
    def test_list_app(self):
        print("test_list_app")
        app_list = self.ios.list_app(type="all")
        self.assertIsInstance(app_list, list)
        print(app_list)

    def test_install_app(self):
        print("test_install_app")
        self.ios.install_app(TEST_IPA_FILE_OR_URL)
    
    def test_uninstall_app(self):
        print("test_uninstall_app")
        self.ios.uninstall_app(TEST_IPA_BUNDLE_ID)

    def test_get_clipboard(self):
        print("test_get_clipboard")
        print(self.ios.get_clipboard())

    def test_set_clipboard(self):
        for i in range(10):
            text = "test_set_clipboard"+str(i)
            self.ios.set_clipboard(text)
            self.assertEqual(self.ios.get_clipboard(), text)
            self.ios.paste()

        text = "test clipboard with中文 $pecial char #@!#%$#^&*()'"
        self.ios.set_clipboard(text)
        self.assertEqual(self.ios.get_clipboard(), text)
        self.ios.paste()

    def test_ls(self):
        print("test ls")
        print(self.ios.ls("/Documents/", self.TEST_FSYNC_APP))
        
    def test_push(self):
        def _try_remove_ios(file_name, bundle_id=None):
            try:
                self.ios.rm(file_name, bundle_id)
                file_list = self.ios.ls(os.path.dirname(file_name), bundle_id)
                for file in file_list:
                    if file['name'] == file_name:
                        raise Exception(f"remove file {file_name} failed")
                print(f"file {file_name} not exist now.")
            except:
                pass

        def _test_file(file_name, dst="/Documents/", bundle_id=self.TEST_FSYNC_APP, target=None):
            try_remove(file_name)
            with open(file_name, 'w') as f:
                f.write('Test data')

            # 用来ls和rm的路径，没有将文件改名则默认为file_name
            if not target:
                tmp_dst = os.path.normpath(dst)
                if os.path.basename(tmp_dst) != file_name:
                    tmp_dst = os.path.join(tmp_dst, file_name)
                target = tmp_dst.replace('\\', '/')

            # 清理手机里的文件
            _try_remove_ios(target, bundle_id)
            self.ios.push(file_name, dst, bundle_id, timeout=60)
            time.sleep(1)
            file_list = self.ios.ls(target, bundle_id)
            # 验证结果
            self.assertEqual(len(file_list), 1)
            self.assertEqual(file_list[0]['name'], os.path.basename(target))
            self.assertEqual(file_list[0]['type'], 'File')
            self.ios.rm(target, bundle_id)
            time.sleep(1)

            # 清理
            try_remove(file_name)

        def _test_dir(dir_name, dst="/Documents/"):
            print(f"test push directory {dir_name}")
            # 用来ls和rm的路径
            tmp_dst = os.path.normpath(dst)
            if os.path.basename(tmp_dst) != dir_name:
                tmp_dst = os.path.join(tmp_dst, dir_name)
            target = tmp_dst.replace('\\', '/')

            # 创建文件夹和文件
            try_remove(dir_name)
            _try_remove_ios(target, self.TEST_FSYNC_APP)
            os.mkdir(dir_name)
            with open(f'{dir_name}/test_data', 'w') as f:
                f.write('Test data')

            self.ios.push(dir_name, dst, self.TEST_FSYNC_APP, timeout=60)
            time.sleep(1)

            dir_list = self.ios.ls(os.path.dirname(target), self.TEST_FSYNC_APP)
            print(dir_list)
            self.assertTrue(f"{dir_name}/" in [item['name'] for item in dir_list])
            file_list = self.ios.ls(f"{target}/test_data", self.TEST_FSYNC_APP)
            self.assertTrue("test_data" in [item['name'] for item in file_list])
            self.ios.rm(target, self.TEST_FSYNC_APP)
            time.sleep(1)

            try_remove(dir_name)

        # 执行得太快会报错,可能和wda的处理速度有关
        # 如果报错尝试单独执行那些用例
        _test_file("test_data_1.txt", "/Documents/")
        _test_file("test_data_2.txt", "/Documents/test_data_2.txt")
        _test_file("test_data_3.txt", "/Documents/test_data_3.txt/")
        #重命名文件
        _test_file("test_data_4.txt", "/Documents/test_data.txt/", target="/Documents/test_data.txt")
        _test_file("test_data.txt", "/Documents")
        _test_file("test_1.png", "/DCIM", None)
        _test_file("test_2.png", "/DCIM/", None)
        _test_file("test_3.png", "/DCIM/test_3.png", None)
        _test_file("test_4.png", "/DCIM/test_4.png/", None)
        _test_file("test_5.png", "/DCIM/test.png/", None, target="/DCIM/test.png")
        _test_file("test.png", "/DCIM/", None)
        _test_file("t e s t  d a t a.txt", "/Documents")
        _test_file("测试文件.txt", "/Documents")
        _test_file("测 试 文 件.txt", "/Documents")
        _test_file("(){}[]~'-_@!#$%&+,;=^.txt", "/Documents")
        _test_file("data", "/Documents")

        _test_dir('test_dir', "/Documents/")
        _test_dir('test_dir_1', "/Documents")
        _test_dir('t e s t  d i r', "/Documents")
        _test_dir("(){}[]~'-_@!#$%&+,;=^", "/Documents")
        _test_dir('测试文件夹', "/Documents/")
        _test_dir('测试文件夹_1', "/Documents")
        _test_dir('测 试 文 件 夹', "/Documents")
        
    def test_pull(self):
        def _test_file(file_name):
            print(f"test pull file {file_name}")
            self.ios.pull(f"/Documents/{file_name}", ".", self.TEST_FSYNC_APP, timeout=60)
            self.assertTrue(os.path.exists(file_name))
            try_remove(file_name)

        def _test_dir(dir_name):
            print(f"test pull directory {dir_name}")
            os.mkdir(dir_name)
            self.ios.pull(f"/Documents/{dir_name}", dir_name, self.TEST_FSYNC_APP, timeout=60)
            self.assertTrue(os.path.exists(f"{dir_name}/{dir_name}"))
            try_remove(dir_name)
        
        _test_file("test_data.txt")
        _test_file("测试文件.txt")
        _test_dir('test_dir')
        _test_dir('测试文件夹')

    def test_rm(self):
        def _test_file(file_name):
            print(f"test rm file {file_name}")
            file_list = self.ios.ls("/Documents/", self.TEST_FSYNC_APP)
            find_flag = False
            for item in file_list:
                if item['name'] == file_name:
                    print(f"find file {file_name}")
                    find_flag = True
                    break
            if not find_flag:
                print(f"not find file {file_name}")
                return
            self.ios.rm(f"/Documents/{file_name}", self.TEST_FSYNC_APP)
            file_list = self.ios.ls("/Documents/", self.TEST_FSYNC_APP)
            self.assertTrue(file_name not in [item['name'] for item in file_list])
        
        def _test_dir(dir_name):
            print(f"test rm directory {dir_name}")
            file_list = self.ios.ls("/Documents/", self.TEST_FSYNC_APP)
            find_flag = False
            for item in file_list:
                if item['name'] == f"{dir_name}/":
                    print(f"find dir {dir_name}")
                    find_flag = True
                    break
            if not find_flag:
                print(f"not find dir {dir_name}")
                return
            self.ios.rm(f"/Documents/{dir_name}", self.TEST_FSYNC_APP)
            file_list = self.ios.ls("/Documents/", self.TEST_FSYNC_APP)
            self.assertTrue(f"{dir_name}/" not in [item['name'] for item in file_list])

        _test_file("test_data.txt")
        _test_file("测试文件.txt")
        _test_dir('test_dir')
        _test_dir('测试文件夹')
    
    def test_mkdir(self):
        print("test mkdir")
        dir_name = "/Documents/test_dir"
        self.ios.mkdir(dir_name, self.TEST_FSYNC_APP)
        
        dirs = self.ios.ls("/Documents", self.TEST_FSYNC_APP)
        self.assertTrue(any(d['name'] == 'test_dir/' for d in dirs))
        self.ios.rm(dir_name, self.TEST_FSYNC_APP)


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
    suite.addTest(TestIos("test_double_click"))
    suite.addTest(TestIos("test_ls"))
    suite.addTest(TestIos("test_push"))
    suite.addTest(TestIos("test_pull"))
    suite.addTest(TestIos("test_mkdir"))
    suite.addTest(TestIos("test_rm"))
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
