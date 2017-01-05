# _*_ coding:UTF-8 _*_

import sys
import subprocess
import win32process
import win32com.client
from PIL import ImageGrab

from airtest.aircv import aircv
from airtest.core.device import Device

from winsendkey import SendKeys
from keyboard import key_input
from mouse import mouse_click, mouse_drag, mouse_down, mouse_up, mouse_move
from window_mgr import WindowMgr, get_screen_shot, get_resolution, get_window_pos


class Windows(Device):
    """Windows Client"""
    def __init__(self, handle=None):
        self.winmgr = WindowMgr()
        self.handle = handle
        self.window_title = None

    def shell(self, cmd):
        return subprocess.check_output(cmd, shell=True)

    def snapshot(self, filename=None):
        """default not write into file."""
        # # 将回放脚本时的截图方式，换成ImageGrab()
        # screen = get_screen_shot(output=None)
        # # screen = ImageGrab.grab()
        # screen = aircv.pil_2_cv2(screen)
        screen = get_screen_shot()
        if filename:
            aircv.imwrite(filename, screen)
        return screen

    def snapshot_by_hwnd(self, filename="tmp.png", hwnd_to_snap=None, use_crop_screen=True):
        """
            根据窗口句柄进行截图，如果发现窗口句柄已经不在则直接返回None.
            返回值还包括窗口左上角的位置.
        """
        # 如果当前的hwnd不存在，直接返回None
        hwnd_list = self.find_all_hwnd()
        if hwnd_to_snap not in hwnd_list:
            raise Exception("hwnd not exist in system !")
        else:
            # print "snapshot_by_hwnd in win.py", hwnd, filename
            if use_crop_screen:  # 小马电脑上有问题，暂时启用crop_screen_by_hwnd=True：
                screen = get_screen_shot()
                img = self.winmgr.crop_screen_by_hwnd(screen, hwnd=hwnd_to_snap, filename=filename)
            else:
                img = self.winmgr.snapshot_by_hwnd(hwnd=hwnd_to_snap, filename=filename)

            if filename:
                aircv.imwrite(filename, img)
            return img

    def get_wnd_pos_by_hwnd(self, hwnd, use_crop_screen=True):
        """ 根据窗口句柄，返回窗口左上角的位置. """
        # 如果使用的是use_crop_screen的方法，计算wnd_pos时就不能有负数了：
        #     否则在窗口左边在屏幕外时，将会有实际操作的左偏移：
        wnd_pos = self.winmgr.get_wnd_pos_by_hwnd(hwnd, use_crop_screen=use_crop_screen)
        return wnd_pos

    def get_childhwnd_list_by_hwnd(self, hwnd, child_hwnd_list, w_h):
        # 传入当前的child_hwnd_list，去除当前已经不在hwnd内的child_hwnd
        #     如果发现全都不在了，那么就使用w_h进行查找新的child_hwnd_list
        #     如果发现w_h的也不在了，那么就按照w_h的比例相同的原则进行查找，还没有，就报错...
        new_child_hwnd_list = self.winmgr.get_childhwnd_list_by_hwnd(hwnd, child_hwnd_list, w_h)
        return new_child_hwnd_list

    def keyevent(self, keyname, escape=False, combine=None):
        key_input(keyname, escape, combine)

    def text(self, text, with_spaces=True, with_tabs=False, with_newlines=False):
        SendKeys(text.decode("utf-8"), with_spaces=with_spaces, with_tabs=with_tabs, with_newlines=with_newlines)

    def touch(self, pos, right_click=False, duration=None): # 暂时添加了duration接口，但是并无对应的响应
        mouse_click(pos, right_click)

    def swipe(self, p1, p2, duration=0.8):
        mouse_drag(p1, p2, duration=duration)  # windows拖拽时间固定为0.8s

    def find_window(self, wildcard):
        """
        遍历所有window按re.match来查找wildcard，并设置为当前handle
        """
        self.window_title = wildcard
        return self.winmgr.find_window_wildcard(wildcard)

    def find_hwnd_title(self, hwnd):
        """
        获取指定hwnd的title.
        """
        title = self.winmgr.find_hwnd_title(hwnd)
        # print "in win.py : find_hwnd_title()", title.encode("utf8")
        return title

    def find_all_hwnd(self):
        """
        获取当前的所有窗口队列.
        """
        hwnd_list = self.winmgr.find_all_hwnd()  # 获取所有的窗口句柄
        # print "in win.py : find_hwnd_title()", title.encode("utf8")
        return hwnd_list

    def find_window_list(self, wildcard):
        self.window_title = wildcard
        return self.winmgr.find_window_list(wildcard)

    def set_handle(self, handle):
        self.handle = handle
        self.winmgr.handle = handle

    def set_foreground(self):
        self.winmgr.set_foreground()
        self.set_hwnd_focus()

    def set_hwnd_focus(self):
        """根据handle获取窗口焦点，使得键盘事件对该窗口生效."""
        if self.handle:
            _, pid = win32process.GetWindowThreadProcessId(self.handle)
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.AppActivate('Console2')
            shell.SendKeys('{UP}{ENTER}')
            shell.AppActivate(pid)

    def get_window_pos(self):
        return self.winmgr.get_window_pos()

    def set_window_pos(self, (x, y)):
        self.winmgr.set_window_pos(x, y)

    def getCurrentScreenResolution(self):
        return get_resolution()

    def operate(self, args):
        if args["type"] == "down":
            mouse_down(pos=(args['x'], args['y']))
        elif args["type"] == "move":
            mouse_move(int(args['x']), int(args['y']))
        elif args["type"] == "up":
            mouse_up()
        else:
            raise RuntimeError("invalid operate args: %s" % args)

    def start_app(self, path):
        return subprocess.call('start "" "%s"' % path, shell=True)

    def stop_app(self, title=None, pid=None, image=None):
        if title:
            cmd = 'taskkill /FI "WINDOWTITLE eq %s"' % title
        elif pid:
            cmd = 'taskkill /PID %s' % pid
        elif image:
            cmd = 'taskkill /IM %s' % image
        return subprocess.check_output(cmd, shell=True)


#if __name__ == '__main__':
#    import time
#    w = Windows()
#    # w.snapshot()
#    # w.keyevent("enter", escape=True)
#    # w.text("nimei")
#    # w.touch((10, 10))
#    # w.swipe((10,10), (200,200))
#    w.set_handle(w.find_window(u"QA平台"))
#    w.set_foreground()
#    print w.get_window_pos()
#    time.sleep(1)
#    # w.set_window_pos((0, 0))
#    w2 = Windows()
#    w.set_handle(w2.find_window("GitHub"))
#    w2.set_foreground()
#    time.sleep(1)
#    w.set_foreground()
#    time.sleep(1)
#    w2.set_foreground()
