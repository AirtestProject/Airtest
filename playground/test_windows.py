# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import time

from airtest.core.win import Windows


def test_windows():
    import time
    w = Windows() 
    # w.snapshot() 
    # w.keyevent("enter", escape=True) 
    # w.text("nimei") 
    # w.touch((10, 10)) 
    # w.swipe((10,10), (200,200)) 
    w.set_handle(w.find_window(u"QA平台")) 
    w.set_foreground() 
    print w.get_window_pos() 
    time.sleep(1) 
    # w.set_window_pos((0, 0)) 
    w2 = Windows() 
    w.set_handle(w2.find_window("GitHub")) 
    w2.set_foreground() 
    time.sleep(1) 
    w.set_foreground() 
    time.sleep(1) 
    w2.set_foreground()     
    


if __name__ == '__main__':

    test_windows()
