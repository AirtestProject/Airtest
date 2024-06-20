# encoding=utf-8
from airtest.core.android.adb import ADB, AdbError, AdbShellError, DeviceConnectionError
from .testconf import IMG, APK, PKG, try_remove
from types import GeneratorType
import os
import shutil
import unittest
import subprocess
from six import text_type
import warnings
warnings.simplefilter("always")


class TestADBWithoutDevice(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()

    def test_adb_path(self):
        self.assertTrue(os.path.exists(self.adb.builtin_adb_path()))

    def test_start_server(self):
        self.adb.start_server()

    def test_version(self):
        self.assertIn("1.0.40", self.adb.version())

    def test_other_adb_server(self):
        adb = ADB(server_addr=("localhost", 5037))
        self.assertIn("1.0.40", adb.version())

    def test_start_cmd(self):
        proc = self.adb.start_cmd("devices", device=False)
        self.assertIsInstance(proc, subprocess.Popen)
        self.assertIsNotNone(proc.stdin)
        self.assertIsNotNone(proc.stdout)
        self.assertIsNotNone(proc.stderr)
        out, err = proc.communicate()
        self.assertIsInstance(out, str)
        self.assertIsInstance(err, str)

    def test_cmd(self):
        output = self.adb.cmd("devices", device=False)
        self.assertIsInstance(output, text_type)

        with self.assertRaises(AdbError):
            self.adb.cmd("wtf", device=False)

    def test_devices(self):
        all_devices = self.adb.devices()
        self.assertIsInstance(all_devices, list)


class TestADBWithDevice(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        devices = ADB().devices(state="device")
        if not devices:
            raise RuntimeError("At lease one adb device required")
        cls.adb = ADB(devices[0][0])

    def test_devices(self):
        online_devices = self.adb.devices(state=self.adb.status_device)
        self.assertEqual(online_devices[0][0], self.adb.serialno)
        self.assertEqual(online_devices[0][1], self.adb.status_device)

    def test_get_status(self):
        self.assertEqual(self.adb.get_status(), self.adb.status_device)

    def test_cmd(self):
        output = self.adb.cmd("shell whoami")
        self.assertIsInstance(output, text_type)

        with self.assertRaises(RuntimeError):
            self.adb.cmd("shell top", timeout=2)

    def test_wait_for_device(self):
        self.adb.wait_for_device()

        with self.assertRaises(DeviceConnectionError):
            ADB("some_impossible_serialno").wait_for_device(timeout=2)

    def test_start_shell(self):
        proc = self.adb.start_shell("time")
        self.assertIsInstance(proc, subprocess.Popen)
        out, err = proc.communicate()
        self.assertIsInstance(out, str)
        self.assertIsInstance(err, str)

    def test_raw_shell(self):
        output = self.adb.raw_shell("pwd")
        self.assertEqual(output.strip(), "/")
        self.assertIsInstance(output, text_type)

        self.assertIsInstance(self.adb.raw_shell("pwd", ensure_unicode=False), str)

    def test_shell(self):
        output = self.adb.shell("time")
        self.assertIsInstance(output, text_type)

        with self.assertRaises(AdbShellError):
            self.adb.shell("ls some_imposible_path")

    def test_getprop(self):
        output = self.adb.getprop("wifi.interface")
        self.assertIsInstance(output, text_type)

    def test_sdk_version(self):
        output = self.adb.sdk_version
        self.assertIsInstance(output, int)

    def test_exists_file(self):
        self.assertTrue(self.adb.exists_file("/"))

    def test_file_size(self):
        self.assertIsInstance(self.adb.file_size("/data/local/tmp/minicap"), int)

    def test_push(self):

        def test_push_file(file_path, des_path):
            des_file = self.adb.push(file_path, des_path)
            print(des_file)
            self.assertIsNotNone(des_file)
            self.assertTrue(self.adb.exists_file(des_file))
            self.adb.shell("rm -r \"" + des_file + "\"")

        tmpdir = "/data/local/tmp"
        test_push_file(IMG, tmpdir)

        imgname = os.path.basename(IMG)
        tmpimgpath = tmpdir + "/" + imgname
        test_push_file(IMG, tmpimgpath)
        test_push_file(IMG, tmpdir)

        # 测试空格+特殊字符+中文
        test_space_img = os.path.join(os.path.dirname(IMG), "space " + imgname)
        shutil.copy(IMG, test_space_img)
        test_push_file(test_space_img, tmpdir)
        test_push_file(test_space_img, tmpdir + "/" + os.path.basename(test_space_img))
        try_remove(test_space_img)

        test_img = os.path.join(os.path.dirname(IMG), imgname + "中文 (1)")
        shutil.copy(IMG, test_img)
        test_push_file(test_img, tmpdir)
        test_push_file(test_img, tmpdir + "/" + os.path.basename(test_img))
        try_remove(test_img)

        # 测试非临时目录（部分高版本手机有权限问题，不允许直接push）
        dst_path = "/sdcard/Android/data/com.netease.nie.yosemite/files"
        test_push_file(IMG, dst_path)
        test_img = os.path.join(os.path.dirname(IMG), imgname + "中文 (1)")
        shutil.copy(IMG, test_img)
        test_push_file(test_img, dst_path)

        # 推送文件夹 /test push 到 目标路径
        os.makedirs("test push", exist_ok=True)
        shutil.copy(IMG, "test push/" + imgname)
        test_push_file("test push", dst_path)
        test_push_file("test push", tmpdir)
        shutil.rmtree("test push")

        # 推送文件夹 /test push 到 目标路径/test push
        os.makedirs("test push", exist_ok=True)
        shutil.copy(IMG, "test push/" + imgname)
        test_push_file("test push", dst_path + "/test")
        shutil.rmtree("test push")

    def test_pull(self):
        tmpdir = "/data/local/tmp"
        imgname = os.path.basename(IMG)
        tmpimgpath = tmpdir + "/" + imgname
        dest_file = self.adb.push(IMG, tmpdir)

        try_remove(imgname)
        self.adb.pull(tmpimgpath, ".")
        self.assertTrue(os.path.exists(imgname))
        try_remove(imgname)

        # 测试空格+特殊字符+中文
        test_file_path = "test pull/g18/test中文 (1).png"
        os.makedirs(os.path.dirname(test_file_path))
        self.adb.pull(tmpimgpath, test_file_path)
        self.assertTrue(os.path.exists(test_file_path))
        try_remove("test pull")

        self.adb.shell("rm " + dest_file)

    def test_get_forwards(self):
        self.adb.remove_forward()
        self.adb.forward(local='tcp:6100', remote="tcp:7100")

        forwards = self.adb.get_forwards()
        self.assertIsInstance(forwards, GeneratorType)

        forwards = list(forwards)
        self.assertEqual(len(forwards), 1)
        sn, local, remote = forwards[0]
        self.assertEqual(sn, self.adb.serialno)
        self.assertEqual(local, 'tcp:6100')
        self.assertEqual(remote, 'tcp:7100')

    def test_remove_forward(self):
        self.adb.remove_forward()
        self.assertEqual(len(list(self.adb.get_forwards())), 0)

        # set a remote and remove it
        self.adb.forward(local='tcp:6100', remote="tcp:7100")
        self.adb.remove_forward(local='tcp:6100')
        self.assertEqual(len(list(self.adb.get_forwards())), 0)

    def test_cleanup_forwards(self):
        """
        Test that all forward ports have been removed
        测试所有forward的端口号都被remove了
        """
        for port in ['tcp:10010', 'tcp:10020', 'tcp:10030']:
            self.adb.forward(port, port)
        self.adb._cleanup_forwards()
        self.assertEqual(len(list(self.adb.get_forwards())), 0)

    def test_logcat(self):
        line_cnt = 0
        for line in self.adb.logcat():
            self.assertIsInstance(line, str)
            line_cnt += 1
            if line_cnt > 3:
                break
        self.assertGreater(line_cnt, 0)

    def test_pm_install(self):
        if PKG in self.adb.list_app():
            self.adb.pm_uninstall(PKG)

        self.adb.pm_install(APK, install_options=["-r", "-g"])
        self.assertIn(PKG, self.adb.list_app())

        # 安装完毕后，验证apk文件是否已删除
        tmpdir = "/data/local/tmp"
        tmp_files = self.adb.shell("ls " + tmpdir)
        self.assertNotIn(os.path.basename(APK), tmp_files, "The apk file in /data/local/tmp is not deleted!")

        self.adb.pm_uninstall(PKG)
        self.assertNotIn(PKG, self.adb.list_app())

        # 测试中文名+特殊字符的apk安装
        test_apk_name = "中文 (1).apk"
        shutil.copy(APK, test_apk_name)
        self.adb.pm_install(test_apk_name, install_options=["-r", "-g"])
        self.assertIn(PKG, self.adb.list_app())

        # 安装完毕后，验证apk文件是否已删除
        tmpdir = "/data/local/tmp"
        tmp_files = self.adb.shell("ls " + tmpdir)
        self.assertNotIn(os.path.basename(APK), tmp_files, "The apk file in /data/local/tmp is not deleted!")

        self.adb.pm_uninstall(PKG)
        self.assertNotIn(PKG, self.adb.list_app())
        try_remove(test_apk_name)

    def test_ip(self):
        ip = self.adb.get_ip_address()
        if ip:
            self.assertEqual(len(ip.split('.')), 4)

    def test_gateway(self):
        gateway = self.adb.get_gateway_address()
        if gateway:
            self.assertEqual(len(gateway.split('.')), 4)

    def test_text(self):
        self.adb.text("Hello World")
        self.adb.text("test123")


if __name__ == '__main__':
    unittest.main()
