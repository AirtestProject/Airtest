# -*- coding: utf-8 -*-
import time
from airtest.core.android import ADB, Minicap, Minitouch, Android


def test_minicap(serialno):
    mi = Minicap(serialno, {"width": 854, "height": 480, "orientation": 0})
    gen = mi.get_frames()
    print '-' * 72
    print gen.next()
    # print repr(gen.next())
    frame = mi.get_frame()
    with open("test.jpg", "wb") as f:
        f.write(gen.next())

    
def test_minitouch(serialno):
    size = Android(serialno, minitouch=False, minicap=False).size
    mi = Minitouch(serialno, size=size, backend=False)
    # mi.touch((100,100))
    # time.sleep(1)
    # mi.swipe((100, 100), (1000, 100))
    # time.sleep(1)
    mi.operate({"type":"down", "x":100, "y":100})
    time.sleep(1)
    mi.operate({"type": "up"})
    time.sleep(1)
    mi.teardown()


def test_android():
    # serialno = "10.250.210.118:57217"
    # t = time.clock()
    serialno = None
    a = Android(serialno, minicap_stream=True)
    # gen = a.minicap.get_frames()
    print a.sdk_version
    # a.home()
    # a.amclear("com.netease.my")
    # for i in range(10):
    #     print "get next frame"
    #     # frame = gen.next()
    #     frame = a.snapshot()
    #     time.sleep(1)
    # a.amstart("com.netease.my")
    # header = gen.next()
    a.amclear("com.netease.my")
    a.amstart("com.netease.my")
    for i in range(1000):
        print "get next frame"
        # frame = gen.next()
        # screen = aircv.string_2_img(frame)
        # aircv.imwrite("tmp.png", screen)
        frame = a.snapshot()
        time.sleep(1)
    # # a.uninstall(RELEASELOCK_PACKAGE)
    # # a.wake()
    # a.amstart("com.netease.my")
    # t = time.clock()
    # a = Android(serialno, init_display=False, minicap=False, minitouch=False, init_ime=False)
    # # a.uninstall(RELEASELOCK_PACKAGE)
    # # a.wake()
    # a.amstart("com.netease.my")
    # def heihei(ori, nimei):
    #     print ori, nimei
    # a.reg_ow_callback(heihei, ({1: 2}, ))
    # time.sleep(100)
    # print a.amlist()
    # a.amuninstall("com.netease.kittycraft")
    # a.install(r"I:\init\moaworkspace\apk\g18\g18_netease_baidu_pc_pz_dev_1.79.0.apk", reinstall=True)
    # a.uninstall("com.netease.com")
    # print time.clock() - t, "111"
    # a.start_recording(max_time=3)
    # time.sleep(5)
    # a.stop_recording()
    # screen = a.adb.snapshot()
    # with open("screen.png", "wb") as f:
    #     f.write(screen)
    # a.touch((100, 100))
    # a.amstart("com.netease.my", "AppActivity")
    # import time
    # t = time.time()
    # print a.getDisplayOrientation()
    # print time.time() - t
    # print a.minicap.get_display_info()
    # print time.time() - t
    # gen = a.minicap.get_frames(adb_port=11314)
    # print gen.next()
    # print len(gen.next())
    # ret = a.adb.install(r"C:\Users\game-netease\Desktop\netease.apk")
    # ret = a.adb.uninstall("com.example.netease")
    # print repr(ret)
    # print a.size
    # print a.shell("ls")
    # a.wake()
    # return
    # print a.is_screenon()
    # a.keyevent("POWER")
    # a.snapshot('test.jpg')
    # a.snapshot('test1.jpg')
        
    # print a.get_top_activity_name()
    # print a.is_keyboard_shown()
    # print a.is_locked()
    # a.unlock()
    # print a.minicap.get_display_info()
    # print a.getDisplayOrientation()
    # a.touch((100, 100))
    # print a.minitouch.transform_xy(100,100)


if __name__ == '__main__':
    # serialno = adb_devices(state="device").next()[0]
    # print serialno
    # serialno = "192.168.40.111:7401"
    # adb = ADB(serialno)
    # print adb.getprop('ro.build.version.sdk')
    # test_minicap(serialno)
    # test_minitouch(serialno)
    # time.sleep(10)
    test_android()
