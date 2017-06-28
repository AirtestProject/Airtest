# encoding=utf-8
import sys
sys.path.append("..\\..\\..\\")

from airtest.core.android.android import ADB, AdbError, DEFAULT_ADB_SERVER, MoaError
from airtest.core.android.android import Minicap
import unittest
import subprocess
import mock
from mock import patch,Mock
from new_test.adbmock import adbmock


class TestMiniCap(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adb=ADB()
        devicelist=cls.adb.devices()
        if devicelist:
            no,content=devicelist[0]
            serialno = no
            cls.adb.set_serialno(serialno)
            cls.minicap = Minicap(serialno=serialno,adb=cls.adb,stream=False,size={"physical_width":600,"physical_height":400,"rotation":0})
        else:
            with mock.patch.object(cls.adb,'getprop',return_value="17"):
                with mock.patch.object(cls.adb,'cmd',return_value="cmd"):
                    with mock.patch.object(cls.adb,'shell',return_value="cmd"):
                        cls.minicap = Minicap("",size="112",adb=cls.adb,stream=False)

        cls.adbmock=adbmock()


    # need real phone
    def test_install(self):
        self.minicap.install()
        self.minicap.install(reinstall=True)

    # mock install 
    def test_install_install(self):
        # test not wait status
        with mock.patch.object(self.minicap.adb,'getprop',return_value="17"):
            with mock.patch.object(self.minicap.adb,'cmd',return_value="cmd"):
                with mock.patch.object(self.minicap.adb,'shell',return_value="cmd"):
                    self.minicap.install()
                    self.assertEqual(self.minicap.adb.getprop.called, True) 
                    self.assertEqual(self.minicap.adb.cmd.called, True) 
                    self.assertEqual(self.minicap.adb.shell.called, True)
 
    #need real phone 
    def test_get_display_info(self):
        info=self.minicap.get_display_info() 
        self.assertIsInstance(info,dict)       




    #need real phone 
    def test_get_frame(self):
        temp = {"physical_width":600,"physical_height":400,"rotation":0}
        with mock.patch.dict(self.minicap.size,temp,clear=True):
            frame=self.minicap.get_frame()
            #print frame
            try:
                self.assertIsInstance(frame,str)
            except AssertionError:
                self.assertIsInstance(frame,bytes)
    def test_get_frames(self):
        pass
        # Todo
    # Todo fix this cases
    def test_resetup(self):
        with self.assertRaises(KeyError):
            self.minicap._setup()




#class kkk():



if __name__ == '__main__':
    unittest.main()
