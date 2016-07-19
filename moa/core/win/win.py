# _*_ coding:UTF-8 _*_
from winutils import mouse_click, mouse_drag, get_screen_shot, \
    key_input, WindowMgr, get_resolution, mouse_down, mouse_up, mouse_move
from winsendkey import SendKeys
from moa.aircv import aircv

from PIL import ImageGrab

class Windows(object):
    """Windows Client"""
    def __init__(self, handle=None):
        self.winmgr = WindowMgr()
        self.handle = handle
        self.window_title = None

    def snapshot(self, filename="tmp.png"):
        # # 将回放脚本时的截图方式，换成ImageGrab()
        # screen = get_screen_shot(output=None)
        # # screen = ImageGrab.grab()
        # screen = aircv.pil_2_cv2(screen)
        screen = get_screen_shot()
        # aircv.show(screen)
        if filename:
            aircv.imwrite(filename, screen)
        return screen

    def keyevent(self, keyname, escape=False, combine=None):
        key_input(keyname, escape, combine)

    def text(self, text, with_spaces=True, with_tabs=False, with_newlines=False):
        SendKeys(text.decode("utf-8"), with_spaces=with_spaces, with_tabs=with_tabs, with_newlines=with_newlines)

    def touch(self, pos, right_click=False, duration=None): # 暂时添加了duration接口，但是并无对应的响应
        mouse_click(pos, right_click)

    def swipe(self, p1, p2, duration=0.8):
        mouse_drag(p1, p2, duration=duration)  # windows拖拽时间固定为0.8s

    def snapshot_by_hwnd(self, hwnd, filename="tmp.png"):
        """
        根据窗口句柄进行截图，如果发现窗口句柄已经不在则直接返回None.
            返回值还包括窗口左上角的位置.
        """
        # 如果当前的hwnd不存在，直接返回None
        hwnd_list = self.find_all_hwnd()
        if hwnd not in hwnd_list:
            return None, (0, 0)
        else:
            print "snapshot_by_hwnd in win.py", hwnd, filename
            img, pos = self.winmgr.snapshot_by_hwnd(hwnd=hwnd, filename=filename)
            return img, pos

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


if __name__ == '__main__':
    import time
    w = Windows()
    # w.snapshot()
    # w.keyevent("enter", escape=True)
    # w.text("nimei")
    # w.touch((10, 10))
    # w.swipe((10,10), (200,200))
    print w.find_window(u"QA平台")
    w.set_foreground()
    print w.get_window_pos()
    time.sleep(1)
    # w.set_window_pos((0, 0))
    w2 = Windows()
    w2.find_window("GitHub")
    w2.set_foreground()
    time.sleep(1)
    w.set_foreground()
    time.sleep(1)
    w2.set_foreground()