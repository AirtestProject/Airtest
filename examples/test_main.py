# -*- coding: utf-8 -*-
from moa.core.main import *


def test_android():
    set_serialno()
    # set_serialno('9ab171d')
    # set_basedir('../taskdata/1433820164')
    home()
    add_device()
    home()

    # touch('target.png')
    # touch([100, 200])
    # swipe([100, 500], [800, 600])
    # exec_script(script.decode('string-escape'))
    # import urllib
    # serialno, base_dir, script = sys.argv[1: 4]
    # # print sys.argv[1: 4]
    # set_serialno(serialno)
    # set_basedir(base_dir)
    # set_serialno()
    # snapshot()
    # set_basedir()
    # set_logfile('run.log')
    # touch('fb.png', rect=(10, 10, 500, 500))
    # time.sleep(1)
    # home()
    # time.sleep(1)
    # swipe('sm.png', vector=(0, 0.3))
    # time.sleep(1)
    # swipe('vp.jpg', 'cal.jpg')
    # img = MoaText(u"你妹").img
    # img.show()
    # install(r"C:\Users\game-netease\Desktop\netease.apk")
    # uninstall("com.example.netease")
    # amstart("com.netease.my", "AppActivity")
    # amstart("com.netease.my")


def test_win():
    set_windows(window_title="Chrome")
    touch("win.png")
    time.sleep(1)
    add_device()
    time.sleep(1)
    touch("win.png")
    time.sleep(1)
    set_current(0)
    time.sleep(1)
    set_current(1)
    time.sleep(1)
    # set_current(1)
    # set_windows()
    # touch("win.png")
    # # swipe("win.png", (300, 300))
    # # sleep(1.0)
    # # swipe("win.png", vector=(0.3, 0.3))


def test_ios():
    basedir = os.path.dirname(os.path.abspath(__file__))
    new_ipaname = resign(os.path.join(basedir, "ios/mhxy_mobile2016-05-20-09-58_265402_resign.ipa"))
    print new_ipaname
    udid = set_udid()
    print udid
    install(new_ipaname)
    # amstart("com.netease.devtest")
    # screen_filename = os.path.join(basedir,'tmp.png')
    # snapshot(screen_filename)
    # uninstall("com.netease.devtest")


if __name__ == '__main__':
    # test_android()
    # test_ios()
    test_win()
