# encoding=utf-8
import sys
sys.path.append("..\\..\\..\\")

from airtest.core.android.android import ADB, AdbError, DEFAULT_ADB_SERVER, MoaError
from airtest.core.android.android import Minitouch
import unittest
import subprocess
import mock
from mock import patch,Mock
from new_test.adbmock import adbmock


class TestMiniTouch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb=ADB()
        devicelist=cls.adb.devices()
        if devicelist:
            no,content=devicelist[0]
            serialno = no
            cls.adb.set_serialno(serialno)
            cls.minitouch = Minitouch(serialno=serialno,adb=cls.adb,size={"physical_width":600,"physical_height":400,"rotation":0})
        else:
            with mock.patch.object(cls.adb,'getprop',return_value="17"):
                with mock.patch.object(cls.adb,'cmd',return_value="cmd"):
                    with mock.patch.object(cls.adb,'shell',return_value="cmd"):
                        cls.minitouch = Minitouch("",size="112",adb=cls.adb)

        cls.adbmock=adbmock()


    # need real phone
    def test_install(self):
        self.minitouch.install()
        self.minitouch.install(reinstall=True)


    def test_setup_server(self):
        with self.assertRaises(AdbError):
            proc = self.minitouch.setup_server()
            proc.kill()
            self.assertIsInstance(proc, subprocess.Popen)



    def setup_client(self):
        pass
        # Todo

    def test_setup_client_backend(self):
        #self.minitouch.setup_client_backend()
        #stop the process
        pass

        # Todo "KeyError: 'width'" These two function can't be call derictly now
    def test_pinch(self):
        with self.assertRaises(KeyError):
            self.minitouch.pinch()

    def test_pinch_out(self):
        with self.assertRaises(KeyError):        
            self.minitouch.pinch(in_or_out='out')

    def tearDown(self):
        self.minitouch.teardown()

#class kkk():



if __name__ == '__main__':
    unittest.main()
