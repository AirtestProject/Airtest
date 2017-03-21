# -*- coding: utf-8 -*-
"""
    api definition
"""
import os
import time
import fnmatch
# import aircv
from airtest.core import android
from airtest.core.error import MoaError, MoaNotFoundError
from airtest.core.utils import is_str
from airtest.core.settings import Settings as ST
from airtest.core.cv import loop_find, device_snapshot
from airtest.core.helper import G, MoaPic, MoaText, log_in_func, logwrap, moapicwrap, \
    get_platform, platform, register_device, delay_after_operation
try:
    from airtest.core import win
except ImportError as e:
    win = None
try:
    from airtest.core import ios
except ImportError as e:
    ios = None


"""
Environment initialization
"""


def set_serialno(sn=None, minicap=True, minitouch=True, addr=None):
    '''
    auto set if only one device
    support filepath match pattern, eg: c123*
    '''
    addr = addr or ST.ADDRESS

    def get_available_sn(sn):
        devs = android.ADB(server_addr=addr).devices(state='device')
        if not sn:
            # if len(devs) > 1:
            #     print("more than one device, auto choose one, to specify serialno: set_serialno(sn)")
            # elif len(devs) == 0:
            if len(devs) == 0:
                raise MoaError("no device, please check your adb connection")
            devs = [d[0] for d in devs]
            devs_in_moa = [d.serialno for d in G.DEVICE_LIST]
            try:
                another_sn = (set(devs) - set(devs_in_moa)).pop()
            except KeyError:
                raise MoaError("no more device to add")
            sn = another_sn
        else:
            for (serialno, st) in devs:
                if not fnmatch.fnmatch(serialno, sn):
                    continue
                if st != 'device':
                    raise MoaError("Device status not good: %s" % (st,))
                sn = serialno
                break
            if sn is None:
                raise MoaError("Device[%s] not found in %s" % (sn, addr))
        return sn
    sn = get_available_sn(sn)
    dev = android.Android(sn, addr=addr, minicap=minicap, minitouch=minitouch)
    register_device(dev)
    ST.CVSTRATEGY = ST.CVSTRATEGY or ST.CVSTRATEGY_ANDROID
    return sn


def set_emulator(emu_name='bluestacks', sn=None, addr=None):
    '''
    auto set if only one device
    support filepath match pattern, eg: c123*
    '''
    if not android.Emulator:
        raise RuntimeError("Emulator module available on Windows only")
    addr = addr or ST.ADDRESS
    if not sn:
        devs = android.ADB(server_addr=addr).devices(state='device')
        if len(devs) > 1:
            ("more than one device, auto choose one, to specify serialno: set_serialno(sn)")
        elif len(devs) == 0:
            raise MoaError("no device, please check your adb connection")
        sn = devs[0][0]
    else:
        for (serialno, st) in android.ADB(server_addr=addr).devices(state='device'):
            if not fnmatch.fnmatch(serialno, sn):
                continue
            if st != 'device':
                raise MoaError("Device status not good: %s" % (st,))
            sn = serialno
            break
        if sn is None:
            raise MoaError("Device[%s] not found in %s" % (sn, addr))
    #dev = android.Android(sn, addr=addr, minicap=minicap, minitouch=minitouch)
    if not emu_name:
        emu_name = 'bluestacks'
    dev = android.Emulator(emu_name, sn, addr=addr)
    register_device(dev)
    ST.CVSTRATEGY = ST.CVSTRATEGY or ST.CVSTRATEGY_ANDROID
    return sn


def set_udid(udid):
    '''
    auto set if only one device
    support filepath match patten, eg: c123*
    '''
    dev = ios.client.IOS(udid)
    register_device(dev)
    ST.CVSTRATEGY = ST.CVSTRATEGY or ST.CVSTRATEGY_ANDROID


def set_windows(handle=None, window_title=None):
    if win is None:
        raise RuntimeError("win module is not available")
    window_title = window_title or ST.WINDOW_TITLE
    dev = win.Windows()
    if handle:
        dev.set_handle(int(handle))
    elif window_title:
        devs = dev.find_window_list(window_title)
        if not devs:
            raise MoaError("no window found with title: '%s'" % window_title)
        devs_in_moa = [d.handle for d in G.DEVICE_LIST]
        try:
            another_dev = (set(devs) - set(devs_in_moa)).pop()
        except KeyError:
            raise MoaError("no more device to add")
        dev.set_handle(another_dev)
    else:
        G.LOGGING.info("handle not set, use entire screen")
    if dev.handle:
        dev.set_foreground()
    register_device(dev)

    ST.CVSTRATEGY = ST.CVSTRATEGY or ST.CVSTRATEGY_WINDOWS
    # set no resize on windows as default
    ST.RESIZE_METHOD = ST.RESIZE_METHOD or aircv.no_resize


@platform(on=["Android", "Windows", "IOS"])
def set_current(index):
    try:
        G.DEVICE = G.DEVICE_LIST[index]
    except IndexError:
        raise IndexError("device index out of range: %s/%s" % (index, len(G.DEVICE_LIST)))
    if win and get_platform() == "Windows":
        G.DEVICE.set_foreground()


def keep_capture(flag=True):
    G.KEEP_CAPTURE = flag


"""
Device operation
"""


@logwrap
@platform(on=["Android"])
def shell(cmd):
    return G.DEVICE.shell(cmd)


@logwrap
@platform(on=["Android", "IOS"])
def amstart(package, activity=None):
    G.DEVICE.start_app(package, activity)


@logwrap
@platform(on=["Android", "IOS"])
def amstop(package):
    G.DEVICE.stop_app(package)


@logwrap
@platform(on=["Android", "IOS"])
def amclear(package):
    G.DEVICE.clear_app(package)


@logwrap
@platform(on=["Android", "IOS"])
def install(filepath, package):
    return G.DEVICE.install_app(filepath, package)


@logwrap
@platform(on=["Android", "IOS"])
def uninstall(package):
    return G.DEVICE.uninstall_app(package)


@logwrap
def snapshot(filename=None, windows_hwnd=None):
    """capture device screen and save it into file."""
    screen = device_snapshot()
    if filename is None:
        filepath = G.RECENT_CAPTURE_PATH
    else:
        filepath = os.path.join(ST.LOG_DIR, ST.SAVE_SCREEN, filename)
    aircv.imwrite(filepath, screen)


@logwrap
@platform(on=["Android", "IOS"])
def wake():
    G.DEVICE.wake()


@logwrap
@platform(on=["Android", "IOS"])
def home():
    G.DEVICE.home()


@logwrap
@moapicwrap
@platform(on=["Android", "Windows", "IOS"])
def touch(v, timeout=0, delay=0, offset=None, if_exists=False, times=1, right_click=False, duration=0.01):
    '''
    @param if_exists: touch only if the target pic exists
    @param offset: {'x':10,'y':10,'percent':True}
    '''
    timeout = timeout or ST.FIND_TIMEOUT
    if is_str(v) or isinstance(v, (MoaPic, MoaText)):
        try:
            pos = _loop_find(v, timeout=timeout)
        except MoaNotFoundError:
            if if_exists:
                return False
            raise
    else:
        pos = v
        # 互通版需求：点击npc，传入FIND_INSIDE参数作为touch位置矫正(此时的v非img_name_str、非MoaPic、MoaText)
        if ST.FIND_INSIDE and get_platform() == "Windows" and G.DEVICE.handle:
            wnd_pos = G.DEVICE.get_wnd_pos_by_hwnd(G.DEVICE.handle)
            # 操作坐标 = 窗口坐标 + 有效画面在窗口内的偏移坐标 + 传入的有效画面中的坐标
            pos = (wnd_pos[0] + ST.FIND_INSIDE[0] + pos[0],
                   wnd_pos[1] + ST.FIND_INSIDE[1] + pos[1])

    if offset:
        if offset['percent']:
            w, h = G.DEVICE.size['width'], G.DEVICE.size['height']
            pos = (pos[0] + offset['x'] * w / 100,
                   pos[1] + offset['y'] * h / 100)
        else:
            pos = (pos[0] + offset['x'], pos[1] + offset['y'])
        G.LOGGING.debug('touchpos after offset %s', pos)
    else:
        G.LOGGING.debug('touchpos: %s', pos)

    kwargs = {'times': times, 'duration': duration}
    if right_click:
        kwargs['right_click'] = right_click
    G.DEVICE.touch(pos, **kwargs)
    delay_after_operation(delay)


@logwrap
@moapicwrap
@platform(on=["Android", "Windows", "IOS"])
def swipe(v1, v2=None, delay=0, vector=None, target_poses=None, duration=0.5):
    if target_poses:
        if len(target_poses) == 2 and isinstance(target_poses[0], int) and isinstance(target_poses[1], int):
            v1.target_pos = target_poses[0]
            pos1 = _loop_find(v1)
            v1.target_pos = target_poses[1]
            pos2 = _loop_find(v1)
        else:
            raise Exception("invalid params for swipe")
    else:
        if is_str(v1) or isinstance(v1, MoaPic) or isinstance(v1, MoaText):
            pos1 = _loop_find(v1)
        else:
            pos1 = v1

        if v2:
            if (is_str(v2) or isinstance(v2, MoaText)):
                keep_capture()
                pos2 = _loop_find(v2)
                keep_capture(False)
            else:
                pos2 = v2
        elif vector:
            if (vector[0] <= 1 and vector[1] <= 1):
                w, h = ST.SRC_RESOLUTION or G.DEVICE.getCurrentScreenResolution()
                vector = (int(vector[0] * w), int(vector[1] * h))
            pos2 = (pos1[0] + vector[0], pos1[1] + vector[1])
        else:
            raise Exception("no enouph params for swipe")
    G.DEVICE.swipe(pos1, pos2, duration=duration)
    delay_after_operation(delay)


@logwrap
@moapicwrap
@platform(on=["Android", "Windows"])
def operate(v, route, timeout=ST.FIND_TIMEOUT, delay=0):
    if is_str(v) or isinstance(v, MoaPic) or isinstance(v, MoaText):
        pos = _loop_find(v, timeout=timeout)
    else:
        pos = v

    G.DEVICE.operate({"type": "down", "x": pos[0], "y": pos[1]})
    for vector in route:
        if (vector[0] <= 1 and vector[1] <= 1):
            w, h = ST.SRC_RESOLUTION or G.DEVICE.getCurrentScreenResolution()
            vector = [vector[0] * w, vector[1] * h, vector[2]]
        pos2 = (pos[0] + vector[0], pos[1] + vector[1])
        G.DEVICE.operate({"type": "move", "x": pos2[0], "y": pos2[1]})
        time.sleep(vector[2])
    G.DEVICE.operate({"type": "up"})
    delay_after_operation(delay)


@logwrap
@platform(on=["Android"])
def pinch(in_or_out='in', center=None, percent=0.5, delay=0):
    G.DEVICE.pinch(in_or_out=in_or_out, center=center, percent=percent)
    delay_after_operation(delay)


@logwrap
@platform(on=["Android", "Windows", "IOS"])
def keyevent(keyname, escape=False, combine=None, delay=0, times=1, shift=False, ctrl=False):
    """模拟设备的按键功能, times为点击次数. """
    key_temp = keyname.lower()
    for i in range(times):
        if keyname == "-delete":
            text(keyname)
            continue
        # 如果是非 -delete 的输入，则按照之前的逻辑进行设备输入:
        if get_platform() == "Windows":
            G.DEVICE.keyevent(keyname, escape, combine, shift, ctrl)
        else:
            G.DEVICE.keyevent(keyname)
    delay_after_operation(delay)


@logwrap
@platform(on=["Android", "Windows", "IOS"])
def text(text, delay=0, clear=False, enter=True):
    text_temp = text.lower()
    if clear is True:
        if get_platform() == "Windows":
            for i in range(20):
                G.DEVICE.keyevent('backspace', escape=True)
        else:
            G.DEVICE.shell(" && ".join(["input keyevent KEYCODE_DEL"] * 30))

    if text_temp == "-delete":
        # 如果文本是“-delete”，那么删除一个字符
        if get_platform() == "Windows":
            G.DEVICE.keyevent('backspace', escape=True)
        else:
            G.DEVICE.keyevent('KEYCODE_DEL')
    else:
        # 如果是android设备，则传入enter参数( 输入后是否执行enter操作 )
        if get_platform() == "Windows":
            G.DEVICE.text(text)
        else:
            G.DEVICE.text(text, enter=enter)

    delay_after_operation(delay)


@logwrap
def sleep(secs=1.0):
    time.sleep(secs)


@logwrap
@moapicwrap
def wait(v, timeout=0, interval=0.5, intervalfunc=None):
    timeout = timeout or ST.FIND_TIMEOUT
    pos = _loop_find(
        v, timeout=timeout, interval=interval, intervalfunc=intervalfunc)
    return pos


@logwrap
@moapicwrap
def exists(v, timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT_TMP
    try:
        pos = _loop_find(v, timeout=timeout)
        return pos
    except MoaNotFoundError as e:
        return False


@logwrap
@moapicwrap
def find_all(v, timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT_TMP
    try:
        return _loop_find(v, timeout=timeout, find_all=True)
    except MoaNotFoundError:
        return []


@logwrap
@platform(on=["Android"])
def logcat(grep_str="", extra_args="", read_timeout=10):
    return G.DEVICE.logcat(grep_str, extra_args, read_timeout)


@logwrap
def add_watcher(name, func):
    G.WATCHER[name] = func


@logwrap
def remove_watcher(name):
    G.WATCHER.pop(name)


"""
Assert functions
"""


@logwrap
@moapicwrap
def assert_exists(v, msg="", timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT
    try:
        pos = _loop_find(v, timeout=timeout, threshold=ST.THRESHOLD_STRICT)
        return pos
    except MoaNotFoundError:
        raise AssertionError("%s does not exist in screen" % v)


@logwrap
@moapicwrap
def assert_not_exists(v, msg="", timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT_TMP
    try:
        pos = _loop_find(v, timeout=timeout)
        raise AssertionError("%s exists unexpectedly at pos: %s" % (v, pos))
    except MoaNotFoundError:
        pass


@logwrap
def assert_equal(first, second, msg=""):
    if first != second:
        raise AssertionError("%s and %s are not equal" % (first, second))


@logwrap
def assert_not_equal(first, second, msg=""):
    if first == second:
        raise AssertionError("%s and %s are equal" % (first, second))


if __name__ == '__main__':
    set_windows()
