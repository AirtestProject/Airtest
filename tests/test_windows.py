# encoding=utf-8
from airtest.core.win import Windows
from airtest.core.win.winsendkey import handle_code, parse_keys, KeyAction
from airtest.core.win.mouse import get_mouse_point, mouse_dclick, mouse_click, mouse_down, mouse_up
import os
import time
import numpy
import unittest


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

    def test_mouse_down_up(self):
        mouse_down(pos=[2, 0], right_click=True)
        mouse_up(right_click=True)
        mouse_down(pos=[0, 0])
        mouse_up()


class TestWindows(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.windows = Windows()

    @classmethod
    def tearDownClass(self):
        self.windows.stop_app(image="calc.exe")

    def test_shell(self):
        cmds = "ping -n 1 localhost"
        ret = self.windows.shell(cmds)
        self.assertIn("Ping", ret)

    def test_snapshot(self):
        screen = self.windows.snapshot(filename="test.png")
        self.assertIsInstance(screen, numpy.ndarray)
        self.assertIs(os.path.exists("test.png"), True)
        os.remove("test.png")

    def test_snapshot_by_hwnd(self):
        all_hwnd_list = self.windows.find_all_hwnd()
        hwnd_to_snap = all_hwnd_list[0]
        screen = self.windows.snapshot_by_hwnd(filename="test.png", hwnd_to_snap=hwnd_to_snap)
        self.assertIsInstance(screen, numpy.ndarray)
        self.assertIs(os.path.exists("test.png"), True)
        os.remove("test.png")
        screen = self.windows.snapshot_by_hwnd(filename="test.png", hwnd_to_snap=hwnd_to_snap, use_crop_screen=False)
        self.assertIsInstance(screen, numpy.ndarray)
        self.assertIs(os.path.exists("test.png"), True)
        os.remove("test.png")

        # screen = self.windows.snapshot_by_hwnd(filename="test.png")
        # self.assertIsInstance(screen, numpy.ndarray)
        #　self.assertIs(os.path.exists("test.png"), True)
        # os.remove("test.png")

    def test_get_wnd_pos_by_hwnd(self):
        all_hwnd_list = self.windows.find_all_hwnd()
        hwnd_to_snap = all_hwnd_list[0]
        wnd_pos = self.windows.get_wnd_pos_by_hwnd(hwnd_to_snap)
        self.assertIsInstance(wnd_pos, tuple)

    def test_get_childhwnd_list_by_hwnd(self):
        hwnd_list = self.windows.get_childhwnd_list_by_hwnd(0, [], (100, 100))
        self.assertIsInstance(hwnd_list, list)

    def test_find_hwnd_title(self):
        all_hwnd_list = self.windows.find_all_hwnd()
        hwnd_x = all_hwnd_list[0]
        title = self.windows.find_hwnd_title(hwnd_x)
        self.assertIsInstance(title, unicode)

    def test_find_window_list(self):
        self.windows.find_window_list(u"popo")

    def test_set_handle(self):
        self.windows.set_handle(0)

    def test_set_foreground(self):
        self.windows.set_foreground()

    # def test_get_wnd_pos(self):
    #     self.windows.get_window_pos()

    # def test_set_window_pos(self):
    #     self.windows.set_window_pos((0, 0))

    def test_getCurrentScreenResolution(self):
        resolution = self.windows.getCurrentScreenResolution()
        self.assertIsInstance(resolution, tuple)

    def test_start_app(self):
        ret = self.windows.start_app("calc")
        self.assertEqual(ret, 0)

    def test_keyevent(self):
        self.windows.start_app("calc")
        time.sleep(1)
        self.windows.find_window("计算器")
        self.windows.keyevent("1")
        # 输入特殊字符，走入特定逻辑
        self.windows.keyevent("A", escape=True)
        self.windows.keyevent(" ")
        self.windows.keyevent("~")
        self.windows.keyevent("A")
        self.windows.keyevent("a", combine="ctrl", escape=True)

    def test_text(self):
        self.windows.start_app("calc")
        time.sleep(1)
        self.windows.find_window("计算器")
        self.windows.text("12")
        self.windows.text("(123)")

    def test_touch(self):
        self.windows.touch([0, 0])

    def test_swipe(self):
        self.windows.swipe([0, 0], [0, 0])

    def test_operate(self):
        operate_arg = {"type": "down", "x":0, "y":0}
        self.windows.operate(operate_arg)
        operate_arg = {"type": "move", "x":0, "y":0}
        self.windows.operate(operate_arg)
        operate_arg = {"type": "up", "x":0, "y":0}
        self.windows.operate(operate_arg)

    def test_stop_app(self):
        # self.windows.stop_app(title="计算器")
        self.windows.stop_app(image="calc.exe")


if __name__ == '__main__':
    unittest.main()
