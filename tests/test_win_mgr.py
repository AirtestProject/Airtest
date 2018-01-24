# encoding=utf-8
import sys
sys.path.append("..\\..\\..\\")

from airtest.core.win import Windows
from airtest.core.win.window_mgr import WindowMgr,get_resolution,get_window_pos
from airtest.core.win.winsendkey import main as winsendkeymain
import unittest
import mock
from mock import patch,Mock
import win32gui
import numpy
import time

# should move in class
window=[]
def handcallback(hwnd,exc):
    window.append(hwnd)

class TestWinmgr(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        case = ""
        cls.windowmgr = WindowMgr()
        cls.window = Windows()

        win32gui.EnumWindows(handcallback, "")

        cls.window.start_app("calc")
        cls.calchand = cls.windowmgr.find_window_wildcard("计算器")   


    @classmethod
    def tearDownClass(self):
        self.window.stop_app(image="calc.exe")




    def test_snapshot_by_hwnd(self):
        #print window



        result = self.windowmgr.snapshot_by_hwnd(window[2])
        self.assertIsInstance(result,numpy.ndarray)

    def test_crop_screen_by_hwnd(self):
        #print window
        # change match method
        result = self.windowmgr.snapshot_by_hwnd(window[2])
        self.assertIsInstance(result,numpy.ndarray)


        # TODO FIX this case
        # with self.assertRaises(Exception):
        #    result2 = self.windowmgr.crop_screen_by_hwnd(result[0:10, 0:10], window[2])

    def test_get_wnd_pos_by_hwnd(self):
        result = self.windowmgr.get_wnd_pos_by_hwnd(window[2])
        self.assertIsNotNone(result)

    def test_get_childhwnd_list_by_hwnd(self):
        hwnd_list = self.windowmgr.get_childhwnd_list_by_hwnd(0, [], (100, 100))
        self.assertIsInstance(hwnd_list, list)


    def test_find_window(self):
        self.windowmgr.find_window("cmd")
        self.assertIsNotNone(self.windowmgr._handle)

    # return is unicode should test in py3
    def test_find_hwnd_title(self):
        result=self.windowmgr.find_hwnd_title(window[3])
        #print type(result)
        # py3
        try:
            self.assertIsInstance(result,unicode)

            # NameError: name 'unicode' is not defined
        except NameError:
            self.assertIsInstance(result,str)            

    def test_find_all_hwnd(self):
        result=self.windowmgr.find_all_hwnd()
        #print result
        self.assertIsInstance(result,list)  

    def test_find_window_wildcard(self):
        
        result=self.windowmgr.find_window_wildcard(u"开始")
        self.assertIsInstance(result,int)
 
    def test_find_window_list(self):
        
        result=self.windowmgr.find_window_list(u"开始")
        #print result
        self.assertIsInstance(result,list)


    # when having self handle
    def test_set_foreground(self):
        #when handle is none
        self.windowmgr.get_window_pos()
        pass

    def test_get_window_pos(self):
        #when handle is none
        with mock.patch.object(self.windowmgr,'handle',new=window[2]):
            result=self.windowmgr.get_window_pos()
            self.assertIsNotNone(result)
        with mock.patch.object(self.windowmgr,'handle',new=None):
            result=self.windowmgr.get_window_pos()
            self.assertIsNone(result)

    def test_set_window_pos(self):
        #when handle is none
        with mock.patch.object(self.windowmgr,'handle',new=window[2]):
            self.windowmgr.set_window_pos(0,0)
            pass
            #method has no return value 

    def test_get_window_title(self):
        #when handle is none
        with mock.patch.object(self.windowmgr,'handle',new=window[2]):
            result=self.windowmgr.get_window_title()
            self.assertIsNotNone(result)
        with mock.patch.object(self.windowmgr,'handle',new=None):
            result =self.windowmgr.get_window_title()
            self.assertIsNone(result)

    #out of class
    def test_get_resolution(self):
        result1=get_resolution(window[2])
        self.assertIsInstance(result1,tuple)
        result2=get_resolution()
        self.assertIsInstance(result2,tuple)

    def test_get_window_pos(self):
        result=get_window_pos(u"开始")
        self.assertIsNotNone(result)
        # wrong title
        with self.assertRaises(Exception):
            get_window_pos("sdfsfdfsdfsdf")



    def test_extra(self):
        winsendkeymain()



# todo be better
#class kkk():
#numpy.ndarray


if __name__ == '__main__':
    unittest.main()



