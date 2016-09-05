# encoding=utf-8
from airtest.core.android.android import ADB, AdbError, DEFAULT_ADB_SERVER, MoaError
import unittest
import subprocess


class TestADB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb = ADB()

    def test_default_server(self):
        host, port = self.adb.default_server()
        self.assertEqual(host, DEFAULT_ADB_SERVER[0])
        self.assertIsInstance(int(port), int)

    def test_set_serialno(self):
        self.assertEqual(self.adb.serialno, None)
        serialno = "abcdwtf"
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

    def test_cmd(self):
        output = self.adb.cmd("devices", device=False)
        self.assertIsInstance(output, str)

        with self.assertRaises(AdbError):
            self.adb.cmd("wtf", device=False)

        with self.assertRaises(RuntimeError):
            self.adb.cmd("start-server")

    def test_version(self):
        self.assertIsInstance(self.adb.version(), str)

    def test_devices(self):
        self.assertIsInstance(self.adb.devices(), list)
        # need mock to test other cases


class TestADBWithDevice(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        adb = ADB()
        serialno = adb.devices(state=ADB.status_device)[0][0]
        adb.set_serialno(serialno)
        cls.adb = adb

    def test_wait_for_device(self):
        self.adb.wait_for_device()

        with self.assertRaises(MoaError):
            ADB("wtf").wait_for_device()

    def test_connect(self):
        pass

    def test_disconnect(self):
        pass

    def test_get_status(self):
        self.assertIn(self.adb.get_status(), [ADB.status_device, ADB.status_offline])

        serialno_wtf = "abcdwtf"
        self.assertIs(ADB(serialno_wtf).get_status(), None)

    def test_shell(self):
        ret = self.adb.shell("ls")
        self.assertIsInstance(ret, str)
        self.assertIn("\n", ret)
        self.assertIn("data", ret)

        proc = self.adb.shell("ls", not_wait=True)
        proc.kill()
        self.assertIsInstance(proc, subprocess.Popen)

    def test_getprop(self):
        self.assertGreater(len(self.adb.getprop("ro.serialno")), 0)
        self.assertEqual(self.adb.getprop("wtf"), "")

    def test_sdk_version(self):
        self.assertGreater(self.adb.sdk_version, 10)


if __name__ == '__main__':
    unittest.main()
