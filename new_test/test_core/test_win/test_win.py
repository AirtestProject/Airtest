# encoding=utf-8
import sys
sys.path.append("..\\..\\..\\")

from airtest.core.win import Windows
from airtest.core.win.winsendkey import handle_code, parse_keys, KeyAction
from airtest.core.win.mouse import get_mouse_point, mouse_dclick, mouse_click, mouse_down, mouse_up
import unittest
import mock
from mock import patch,Mock
import win32gui
import numpy
import time


try:
    str_class = basestring

    def enforce_unicode(text):
        return unicode(text)
except NameError:
    str_class = str

    def enforce_unicode(text):
        return text


# should move in class
window = []
def handcallback(hwnd,exc):
    window.append(hwnd)

class TestWin(unittest.TestCase):   

    @classmethod
    def setUpClass(cls):
        case=""
        cls.window=Windows()
        win32gui.EnumWindows(handcallback,"")

    @classmethod
    def tearDownClass(self):
        self.window.stop_app(image="calc.exe")

                
    def test_shell(self):
        #print window
        result=self.window.shell("dir")
        print(type(result))
        self.assertIsInstance(result,str_class)


    def test_snapshot(self):
        with mock.patch.object(self.window,'handle',new=window[2]):
            with mock.patch.object(self.window,'snapshot_by_hwnd',return_value="666"):
                result=self.window.snapshot() 
                self.assertEqual(result,"666")
                self.assertEqual(self.window.snapshot_by_hwnd.called,True)


        result=self.window.snapshot(filename="win_snapshot.png") 
        self.assertIsInstance(result,numpy.ndarray)

    def test_snapshot_by_hwnd(self):
        with self.assertRaises(Exception):
            self.window.snapshot_by_hwnd(hwnd_to_snap=0)

        # try both method
        result1=self.window.snapshot_by_hwnd(hwnd_to_snap=window[2],use_crop_screen=True)
        self.assertIsInstance(result1,numpy.ndarray)
        result2=self.window.snapshot_by_hwnd(hwnd_to_snap=window[2],use_crop_screen=False)
        self.assertIsInstance(result2,numpy.ndarray)

    def test_get_wnd_pos_by_hwnd(self):
        all_hwnd_list = self.window.find_all_hwnd()
        hwnd_to_snap = all_hwnd_list[0]
        wnd_pos = self.window.get_wnd_pos_by_hwnd(hwnd_to_snap)
        self.assertIsInstance(wnd_pos, tuple)




    def test_get_childhwnd_list_by_hwnd(self):
        hwnd_list = self.window.get_childhwnd_list_by_hwnd(0, [], (100, 100))
        self.assertIsInstance(hwnd_list, list)

    '''
        start test input things
    '''
    def test_keyevent(self):
        self.window.start_app("calc")
        time.sleep(1)
        self.window.find_window("计算器")
        self.window.keyevent("1")
        # 输入特殊字符，走入特定逻辑
        self.window.keyevent("A", escape=True)
        self.window.keyevent(" ")
        self.window.keyevent("~")
        self.window.keyevent("A")
        self.window.keyevent("a", combine="ctrl", escape=True)


    def test_text(self):
        self.window.start_app("calc")
        time.sleep(1)
        self.window.find_window("计算器")
        self.window.text("12")
        self.window.text("(123)")


    def test_touch(self):
        self.window.touch((0,0),True)
        self.window.touch((0,0),False)

    def test_swipe(self):
        self.window.swipe((0,0),(10,10))

    '''
        find window stuff
    '''
    def test_find_window(self):
        result=self.window.find_window(u"开始")
        self.assertIsInstance(result,int)
    def test_find_hwnd_title(self):
        result=self.window.find_hwnd_title(window[1])
        self.assertIsInstance(result,unicode)

    def test_find_all_hwnd(self):
        result=self.window.find_all_hwnd()
        self.assertIsInstance(result,list)

    #todo find_window_list




    def test_getCurrentScreenResolution(self):
        resolution = self.window.getCurrentScreenResolution()
        self.assertIsInstance(resolution, tuple)


    # mock handle
    def test_set_foreground(self):
        with mock.patch.object(self.window,'handle',new=window[2]):
            with mock.patch.object(self.window.winmgr,'handle',new=window[2]):
                self.window.set_foreground()

    def test_get_window_pos(self):
        with mock.patch.object(self.window.winmgr,'handle',new=window[2]):
            result=self.window.get_window_pos()
            self.assertIsNotNone(result)

    def test_operate(self):
        with self.assertRaises(Exception):
            self.window.oprate({"type": "strange"})
        self.window.operate({"type": "down", "x": 10, "y": 10})
        self.window.operate({"type": "move", "x": 10, "y": 10})
        self.window.operate({"type": "up", "x": 10, "y": 10})

    # test start process
    def test_start_app(self):
        ret = self.window.start_app("calc")
        self.assertEqual(ret, 0)

    def test_stop_app(self):
        # self.windows.stop_app(title="计算器")
        self.window.stop_app(image="calc.exe")


class TestSendKey(unittest.TestCase):

    def test_handle_code(self):
        code_keys = handle_code("{(asd)asd}")
        self.assertIsInstance(code_keys, list)

    def test_parse_keys(self):
        code_keys = parse_keys("{(asd)asd+-}")
        self.assertIsInstance(code_keys, list)


class TestMouse(unittest.TestCase):

    def test_get_mouse_point(self):
        mouse_point = get_mouse_point()
        self.assertIsInstance(mouse_point, tuple)

    def test_mouse_dclick(self):
        mouse_dclick(x=0, y=0)

    def test_mouse_click(self):
        mouse_click([10, 0], right_click=True)
        mouse_click([0, 0], shift=True, duration=0.05)

        mouse_dclick(x=0, y=0)


    def test_mouse_down_up(self):
        mouse_down(pos=[2, 0], right_click=True)
        mouse_up(right_click=True)
        mouse_down(pos=[0, 0])
        mouse_up()

        # close right click
        mouse_dclick(x=0, y=0)


###############################################







# todo be better
#class kkk():
#numpy.ndarray


if __name__ == '__main__':
    unittest.main()



