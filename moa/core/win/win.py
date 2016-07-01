# _*_ coding:UTF-8 _*_
from winutils import mouse_click, mouse_drag, get_screen_shot, \
    key_input, WindowMgr, get_resolution, mouse_down, mouse_up, mouse_move
from winsendkey import SendKeys
from moa.aircv import aircv

from PIL import ImageGrab

class Windows(object):
    """Windows Client"""
    def __init__(self):
        self.winmgr = WindowMgr()

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
        mouse_drag(p1, p2, duration=0.8)  # windows拖拽时间固定为0.8s

    def find_window(self, wildcard):
        """
        遍历所有window按re.match来查找wildcard，并设置为当前handle
        """
        return self.winmgr.find_window_wildcard(wildcard)

    def set_foreground(self, handle=None):
        if handle:
            self.winmgr._handle = handle
        self.winmgr.set_foreground()

    def get_window_pos(self, handle=None):
        if handle:
            self.winmgr._handle = handle
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
    w = Windows()
    # w.snapshot()
    # w.keyevent("enter", escape=True)
    # w.text("nimei")
    # w.touch((10, 10))
    # w.swipe((10,10), (200,200))
    print w.find_window(".*Sublime.*")
    w.set_foreground()
    print w.get_window_pos()
    w.set_window_pos((0, 0))
