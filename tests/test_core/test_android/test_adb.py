# encoding=utf-8
import sys
sys.path.append("..\\..\\..\\")
import os

from airtest.core.android.android import ADB, AdbError, DEFAULT_ADB_SERVER, AirtestError, AdbShellError
from airtest.core.android.android import apkparser

from airtest.core.utils.compat import str_class

import unittest
import subprocess
import mock
from mock import patch, Mock, PropertyMock
from new_test.adbmock import adbmock

TEST_APK = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Rabbit.apk')
TEST_PKG = "org.cocos.Rabbit"


class TestADB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()
        cls.adbmock = adbmock()


    def test_default_server(self):
        host, port = self.adb.default_server()
        self.assertEqual(host, DEFAULT_ADB_SERVER[0])
        self.assertIsInstance(int(port), int)

    # add aato make it run first so the serialno will be set
    def test_aaset_serialno(self):
        self.assertEqual(self.adb.serialno, None)

        no, content  = self.adb.devices()[0]
        print(no)
        serialno = no

        self.adb.set_serialno(serialno)
        self.assertEqual(self.adb.serialno, serialno)

    def test_adb_server(self):
        self.assertIsInstance(self.adb.adb_server_addr, tuple)

    def test_adb_devices(self):
        devices = self.adb.devices()
        self.assertIsInstance(devices, list)

    def test_start_server(self):
        self.assertIn(self.adb.start_server(), [0, 1])

    def test_start_cmd(self):
        proc = self.adb.start_cmd("devices", device=False)
        proc.kill()
        self.assertIsInstance(proc, subprocess.Popen)

        # should raise error when no serialno
        with mock.patch.object(self.adb, 'serialno', new=None):
            with self.assertRaises(RuntimeError):
                self.adb.start_cmd("wtf", device=True)

    def test_cmd(self):
        output = self.adb.cmd("devices", device=False)
        self.assertIsInstance(output, str_class)

        with self.assertRaises(AdbError):
            self.adb.cmd("wtf", device=False)

        with self.assertRaises(RuntimeError):
            self.adb.cmd("start-server")

    def test_version(self):
        self.assertIsInstance(self.adb.version(), str_class)

    def test_devices(self):
        self.assertIsInstance(self.adb.devices(), list)
        # need mock to test other cases



    # new_test usemock
    def test_devices_mock(self):
        # print self.adb.devices()
        self.adbmock.set_cmd_enable("devices", 0)
        with mock.patch.object(self.adb, 'cmd', side_effect=self.adbmock.cmd):
            self.assertIsInstance(self.adb.devices(), list)

    def test_connect_mock(self):
        with mock.patch.object(self.adb, 'cmd', side_effect=self.adbmock.cmd):
            #the logic could be only run in ip port from
            with mock.patch.object(self.adb, 'serialno', new="192.168.1.1:4233"):
                self.adb.connect()
                self.assertEqual(self.adb.cmd.called, True)

        # test force = True case
        with mock.patch.object(self.adb, 'cmd', side_effect=self.adbmock.cmd):
            # the logic could be only run in ip port from
            with mock.patch.object(self.adb, 'serialno', new="192.168.1.1:4233"):
                self.adb.connect(True)
                self.assertEqual(self.adb.cmd.called, True)

    # test disconnect
    def test_disconnect_mock(self):
        with mock.patch.object(self.adb, 'cmd', side_effect=self.adbmock.cmd):
            # the logic could be only run in ip port from
            with mock.patch.object(self.adb, 'serialno', new="192.168.1.1:4233"):
                self.adb.disconnect()
                self.assertEqual(self.adb.cmd.called, True)

    # need real phone
    def test_get_status(self):
        self.assertIsNotNone(self.adb.get_status())

    # need real phone
    def test_wait_for_device(self):
        self.adb.wait_for_device()
    
    # TODO : should test in different sdk version
    def _test_shell_mock(self):
        # test wait
        # TODO : should test in different sdk version
        with mock.patch.object(self.adb, 'raw_shell', return_value="test_final \n 0"):
            self.assertEqual(self.adb.shell("wait"), "test_final \n 0")

        # test not wait status,TODO: mock self.sdk_version and test
        with mock.patch.object(self.adb, 'raw_shell', return_value="start_cmd"):
            self.assertEqual(self.adb.shell("not wait", not_wait=True), "start_cmd")

    # need real phone
    def test_shell(self):
        # test not wait
        output = self.adb.shell("time", not_wait=True)
        stdout, stderr = output.communicate()
        self.assertIsInstance(stdout, str_class)
        # test wait
        output = self.adb.shell("time", not_wait=False)
        self.assertIsInstance(stdout, str_class)

    #need real phone
    def test_getprop(self):
        output=self.adb.getprop("wifi.interface")
        print ("output")
        print  (output)
        print  (type(output))
        print ("DDDDDDDDDDDD")
        self.assertIsInstance(output,str_class)

    # need real phone 
    def test_sdk_version(self):
        output=self.adb.sdk_version
        self.assertIsInstance(output,int)

    # need real phone 
    def test_pull(self):
        self.adb.cmd("push ./runtest.bat /mnt/sdcard/")
        self.adb.pull("/mnt/sdcard/runtest.bat","./runtest.bat")

    # need real phone 
    def test_get_forwards(self):
        self.adb.get_forwards()

    # need real phone
    # remove_forward
    def test_remove_forward(self):
        self.adb.remove_forward()

        # set a remote and remove it
        self.adb.forward(local='tcp:6100', remote="tcp:7100")
        self.adb.remove_forward(local='tcp:6100')


    # need real phone
    def test_install(self):

        try:
            # uninstall first
            self.adb.uninstall_app(TEST_PKG)
        except AdbShellError as e:
            pass


        self.adb.install_app(TEST_APK)
        self.adb.install_app(TEST_APK, overinstall=True)
        with self.assertRaises(RuntimeError):
            self.adb.install_app("sdfasdfsf")


    # need real phone
    def test_uninstall(self):
        output=self.adb.uninstall_app(TEST_PKG)
        self.assertIsInstance(output, str_class)
        #self.cmd.devices()

    # need real phone
    def test_snapshot(self):
        self.adb.snapshot()

    # need real phone
    def test_touch(self):
        self.adb.touch((0, 0))

    # need real phone
    def test_swipe(self):
        self.adb.swipe((0, 0), (10, 10))

        # TODO try to mock sdk_version:
        '''
        with self.assertRaises(AirtestError):
            with mock.patch.object(self.adb,'sdk_version', new=PropertyMock(return_value=15)):
                self.adb.swipe((0, 0), (10, 10))

        with mock.patch.object(self.adb,'sdk_version', new=PropertyMock(return_value=17)):
            self.adb.swipe((0, 0), (10, 10))


        with mock.patch.object(self.adb,'sdk_version', new=PropertyMock(return_value=19)):
            self.adb.swipe((0, 0), (10, 10))'''
      



    # need real phone
    def test_logcat(self):
        times=0
        for line in self.adb.logcat() :
            print ( line )
            self.assertIsInstance(line,str_class)
            times=times+1
            if times > 2 :
                break
        self.assertGreater(times,0)
            





#class kkk():



if __name__ == '__main__':
    unittest.main()