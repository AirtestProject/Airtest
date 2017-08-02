#! /usr/bin/env python
# -*- coding: utf-8 -*-
import re
import warnings
import threading
import aircv
from airtest.core.device import Device
from airtest.core.error import MoaError, AdbShellError
from airtest.core.utils import NonBlockingStreamReader, reg_cleanup, get_logger
from airtest.core.android.ime_helper import YosemiteIme
from airtest.core.android.constant import YOSEMITE_APK, YOSEMITE_PACKAGE, PROJECTIONRATE
from airtest.core.android.adb import ADB
from airtest.core.android.minicap import Minicap
from airtest.core.android.minitouch import Minitouch
from airtest.core.android.javacap import Javacap
from airtest.core.utils.compat import apkparser
LOGGING = get_logger('android')


class Android(Device):

    """Android Client"""

    _props_tmp = "/data/local/tmp/moa_props.tmp"

    def __init__(self, serialno=None, cap_method="minicap_stream", shell_ime=True):
        super(Android, self).__init__()
        self.serialno = serialno or ADB().devices(state="device")[0][0]
        self.adb = ADB(self.serialno)
        self.adb.start_server()
        self.adb.wait_for_device()
        self.sdk_version = self.adb.sdk_version
        self._init_requirement_apk(YOSEMITE_APK, YOSEMITE_PACKAGE)
        self._size = None
        self._init_cap(cap_method)
        self._init_touch(True)
        self.shell_ime = shell_ime

    def _init_cap(self, cap_method):
        self.cap_method = cap_method
        if cap_method == "minicap":
            self.minicap = Minicap(self.serialno, size=self.size, adb=self.adb, stream=False)
            self.orientationWatcher()
        elif cap_method == "minicap_stream":
            self.minicap = Minicap(self.serialno, size=self.size, adb=self.adb, stream=True)
            self.orientationWatcher()
        elif cap_method == "javacap":
            self.javacap = Javacap(self.serialno, adb=self.adb)
        else:
            print("cap_method %s not found, use adb screencap" % cap_method)
            self.cap_method = None

    def _init_touch(self, minitouch=True):
        self.minitouch = Minitouch(self.serialno, size=self.size, adb=self.adb) if minitouch else None

    def _init_requirement_apk(self, apk_path, package):
        apk_version = apkparser.version(apk_path)
        installed_version = self._get_installed_apk_version(package)
        LOGGING.info("local version code is {}, installed version code is {}".format(apk_version, installed_version))
        if not installed_version or apk_version > installed_version:
            self.install_app(apk_path, package, overinstall=True)

    def _get_installed_apk_version(self, package):
        package_info = self.shell(['dumpsys', 'package', package])
        matcher = re.search(r'versionCode=(\d+)', package_info)
        if matcher:
            return int(matcher.group(1))
        return None

    def list_app(self, third_only=False):
        """
        pm list packages: prints all packages, optionally only
          those whose package name contains the text in FILTER.  Options:
            -f: see their associated file.
            -d: filter to only show disbled packages.
            -e: filter to only show enabled packages.
            -s: filter to only show system packages.
            -3: filter to only show third party packages.
            -i: see the installer for the packages.
            -u: also include uninstalled packages.
        """
        cmd = ["pm", "list", "packages"]
        if third_only:
            cmd.append("-3")
        output = self.adb.shell(cmd)
        packages = output.splitlines()
        # remove all empty string; "package:xxx" -> "xxx"
        packages = [p.split(":")[1] for p in packages if p]
        return packages

    def path_app(self, package):
        try:
            output = self.adb.shell(['pm', 'path', package])
        except AdbShellError:
            output = ""
        if 'package:' not in output:
            raise MoaError('package not found, output:[%s]' % output)
        return output.split(":")[1].strip()

    def check_app(self, package):
        if '.' not in package:
            raise MoaError('invalid package "{}"'.format(package))
        output = self.shell(['dumpsys', 'package', package]).strip()
        if package not in output:
            raise MoaError('package "{}" not found'.format(package))
        return 'package:{}'.format(package)

    def start_app(self, package, activity=None):
        self.check_app(package)
        if not activity:
            self.adb.shell(['monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1'])
        else:
            self.adb.shell(['am', 'start', '-n', '%s/%s.%s' % (package, package, activity)])

    def stop_app(self, package):
        self.check_app(package)
        self.adb.shell(['am', 'force-stop', package])

    def clear_app(self, package):
        self.check_app(package)
        self.adb.shell(['pm', 'clear', package])

    def uninstall_app_pm(self, package, keepdata=False):
        cmd = ['pm', 'uninstall', package]
        if keepdata:
            cmd.append('-k')
        self.adb.shell(cmd)

    def enable_accessibility_service(self):
        self.adb.shell('settings put secure enabled_accessibility_services com.netease.accessibility/com.netease.accessibility.MyAccessibilityService:com.netease.testease/com.netease.testease.service.MyAccessibilityService')
        self.adb.shell('settings put secure accessibility_enabled 1')

    def disable_accessibility_service(self):
        self.adb.shell('settings put secure accessibility_enabled 0')
        self.adb.shell('settings put secure enabled_accessibility_services 0')

    def install_app(self, filepath, package=None, **kwargs):
        """
        安装应用
        overinstall: 不管应用在不在，直接覆盖安装；
        reinstall: 如果在则先卸载再安装，不在则直接安装。
        """
        package = package or apkparser.packagename(filepath)
        reinstall = kwargs.get('reinstall', False)
        overinstall = kwargs.get('overinstall', False)
        check = kwargs.get('check', True)

        # 先解析apk，看是否存在已安装的app
        packages = self.list_app()
        if package in packages and not overinstall:
            # 如果reinstall=True，先卸载掉之前的apk，防止签名不一致导致的无法覆盖
            if reinstall:
                LOGGING.info("package:%s already exists, uninstall first", package)
                self.uninstall_app(package)
            # 否则直接return True
            else:
                LOGGING.info("package:%s already exists, skip reinstall", package)
                return True

        # 唤醒设备
        self.wake()
        # 用accessibility点掉所有安装确认窗口
        self.enable_accessibility_service()

        # rm all apks in /data/local/tmp to get enouph space
        self.adb.shell("rm -f /data/local/tmp/*.apk")
        if not overinstall:
            self.adb.install(filepath)
        else:
            self.adb.install(filepath, overinstall=overinstall)
        if check:
            self.check_app(package)

        # rm all apks in /data/local/tmp to free space
        self.adb.shell("rm -f /data/local/tmp/*.apk")

    def uninstall_app(self, package):
        return self.adb.uninstall(package)

    def snapshot(self, filename=None, ensure_orientation=True):
        """default not write into file."""
        if self.cap_method == "minicap_stream":
            screen = self.minicap.get_frame_from_stream()
        elif self.cap_method == "minicap":
            screen = self.minicap.get_frame()
        elif self.cap_method == "javacap":
            screen = self.javacap.get_frame()
        else:
            screen = self.adb.snapshot()
        # 输出cv2对象
        screen = aircv.utils.string_2_img(screen)

        # 保证方向是正的
        if ensure_orientation and self.size["orientation"]:
            # minicap截图根据sdk_version不一样
            if self.cap_method in ("minicap", "minicap_stream") and self.sdk_version <= 16:
                h, w = screen.shape[:2]  # cv2的shape是高度在前面!!!!
                if w < h:  # 当前是横屏，但是图片是竖的，则旋转，针对sdk<=16的机器
                    screen = aircv.rotate(screen, self.size["orientation"] * 90, clockwise=False)
            # adb 截图总是要根据orientation旋转
            elif self.cap_method is None:
                screen = aircv.rotate(screen, self.size["orientation"] * 90, clockwise=False)
        if filename:
            aircv.imwrite(filename, screen)
        return screen

    def shell(self, *args, **kwargs):
        return self.adb.shell(*args, **kwargs)

    def keyevent(self, keyname):
        keyname = keyname.upper()
        self.adb.shell(["input", "keyevent", keyname])

    def wake(self):
        self.home()
        self.adb.shell(['am', 'start', '-a', 'com.netease.nie.yosemite.ACTION_IDENTIFY'])
        self.home()

    def home(self):
        self.keyevent("HOME")

    def text(self, text, enter=True):
        if self.shell_ime:
            # shell_ime用于输入中文
            if not hasattr(self, "ime"):

                # 开启shell_ime
                self.toggle_shell_ime()
            self.ime.text(text)
        else:
            self.adb.shell(["input", "text", text])

        # 游戏输入时，输入有效内容后点击Enter确认，如不需要，enter置为False即可。
        if enter:
            self.adb.shell(["input", "keyevent", "ENTER"])

    def toggle_shell_ime(self, on=True):
        """切换到shell的输入法，用于text"""
        self.shell_ime = True
        if not hasattr(self, "ime"):
            self.ime = YosemiteIme(self)
        if on:
            self.ime.start()
            reg_cleanup(self.ime.end)
        else:
            self.ime.end()

    def touch(self, pos, times=1, duration=0.01):
        pos = map(lambda x: x / PROJECTIONRATE, pos)
        pos = self._transformPointByOrientation(pos)
        for _ in range(times):
            if self.minitouch:
                self.minitouch.touch(pos, duration=duration)
            else:
                self.adb.touch(pos)

    def swipe(self, p1, p2, duration=0.5, steps=5):
        p1 = self._transformPointByOrientation(p1)
        p2 = self._transformPointByOrientation(p2)
        if self.minitouch:
            self.minitouch.swipe(p1, p2, duration=duration, steps=steps)
        else:
            duration *= 1000  # adb的swipe操作时间是以毫秒为单位的。
            self.adb.swipe(p1, p2, duration=duration)

    def operate(self, tar):
        x, y = tar.get("x"), tar.get("y")
        if (x, y) != (None, None):
            x, y = self._transformPointByOrientation((x, y))
            tar.update({"x": x, "y": y})
        self.minitouch.operate(tar)

    def start_recording(self, max_time=180, savefile="/sdcard/screen.mp4"):
        if getattr(self, "recording_proc", None):
            raise MoaError("recording_proc has already started")
        p = self.adb.shell(["screenrecord", savefile, "--time-limit", str(max_time)], not_wait=True)
        nbsp = NonBlockingStreamReader(p.stdout)
        info = nbsp.read(0.5)
        LOGGING.debug(info)
        nbsp.kill()
        if p.poll() is not None:
            LOGGING.error("start_recording error:%s", p.communicate())
            return
        self.recording_proc = p
        self.recording_file = savefile

    def stop_recording(self, output="screen.mp4"):
        if not getattr(self, "recording_proc", None):
            raise MoaError("start_recording first")
        self.recording_proc.kill()
        self.recording_proc.wait()
        self.recording_proc = None
        self.adb.pull(self.recording_file, output)

    def get_top_activity_name_and_pid(self):
        dat = self.adb.shell('dumpsys activity top')
        activityRE = re.compile('\s*ACTIVITY ([A-Za-z0-9_.]+)/([A-Za-z0-9_.]+) \w+ pid=(\d+)')
        m = activityRE.search(dat)
        if m:
            return (m.group(1), m.group(2), m.group(3))
        else:
            warnings.warn("NO MATCH:" + dat)
            return None

    def get_top_activity_name(self):
        tanp = self.get_top_activity_name_and_pid()
        if tanp:
            return tanp[0] + '/' + tanp[1]
        else:
            return None

    def is_keyboard_shown(self):
        dim = self.adb.shell('dumpsys input_method')
        if dim:
            return "mInputShown=true" in dim
        return False

    def is_screenon(self):
        screenOnRE = re.compile('mScreenOnFully=(true|false)')
        m = screenOnRE.search(self.adb.shell('dumpsys window policy'))
        if m:
            return (m.group(1) == 'true')
        raise MoaError("Couldn't determine screen ON state")

    def is_locked(self):
        """not work on xiaomi 2s"""
        lockScreenRE = re.compile('mShowingLockscreen=(true|false)')
        m = lockScreenRE.search(self.adb.shell('dumpsys window policy'))
        if not m:
            raise MoaError("Couldn't determine screen lock state")
        return (m.group(1) == 'true')

    def unlock(self):
        """not work on many devices"""
        self.adb.shell('input keyevent MENU')
        self.adb.shell('input keyevent BACK')

    @property
    def size(self):
        if self._size is None:
            self._size = self.get_display_info()
        return self._size

    def getprop(self, key, strip=True):
        return self.adb.getprop(key, strip)

    def get_display_info(self):
        size = self.getPhysicalDisplayInfo()
        size["orientation"] = self.getDisplayOrientation()
        size["rotation"] = size["orientation"] * 90
        size["max_x"], size["max_y"] = self.getEventInfo()
        return size

    def getEventInfo(self):
        ret = self.adb.shell('getevent -p').split('\n')
        max_x, max_y = None, None
        for i in ret:
            if i.find("0035") != -1:
                patten = re.compile(r'max [0-9]+')
                ret = patten.search(i)
                if ret:
                    max_x = int(ret.group(0).split()[1])

            if i.find("0036") != -1:
                patten = re.compile(r'max [0-9]+')
                ret = patten.search(i)
                if ret:
                    max_y = int(ret.group(0).split()[1])
        return max_x, max_y

    def getCurrentScreenResolution(self):
        w, h = self.size["width"], self.size["height"]
        if self.size["orientation"] in [1, 3]:
            w, h = h, w
        return w, h

    def getPhysicalDisplayInfo(self):
        """维护了两套分辨率：
            (physical_width, physical_height)为设备的物理分辨率， (minitouch点击坐标转换要用这个)
            (width, height)为屏幕的有效内容分辨率. (游戏图像适配的分辨率要用这个)
            (max_x, max_y)为点击范围的分辨率。
        """
        info = self._getPhysicalDisplayInfo()
        # 记录物理屏幕的宽高(供屏幕映射使用)：
        if info["width"] > info["height"]:
            info["physical_height"], info["physical_width"] = info["width"], info["height"]
        else:
            info["physical_width"], info["physical_height"] = info["width"], info["height"]
        # 获取屏幕有效显示区域分辨率(比如带有软按键的设备需要进行分辨率去除):
        mRestrictedScreen = self._getRestrictedScreen()
        if mRestrictedScreen:
            info["width"], info["height"] = mRestrictedScreen
        # 因为获取mRestrictedScreen跟设备的横纵向状态有关，所以此处进行高度、宽度的自定义设定:
        if info["width"] > info["height"]:
            info["height"], info["width"] = info["width"], info["height"]
        # WTF???????????????????????????????????????????
        # 如果是特殊的设备，进行特殊处理：
        special_device_list = ["5fde825d043782fc", "320496728874b1a5"]
        if self.adb.serialno in special_device_list:
            # 上面已经确保了宽小于高，现在反过来->宽大于高
            info["height"], info["width"] = info["width"], info["height"]
            info["physical_width"], info["physical_height"] = info["physical_height"], info["physical_width"]
        return info

    def _getRestrictedScreen(self):
        """Get mRestrictedScreen from 'adb -s sno shell dumpsys window' """
        # 获取设备有效内容的分辨率(屏幕内含有软按键、S6 Edge等设备，进行黑边去除.)
        result = None
        # 根据设备序列号拿到对应的mRestrictedScreen参数：
        dumpsys_info = self.adb.shell("dumpsys window")
        match = re.search(r'mRestrictedScreen=.+', dumpsys_info)
        if match:
            infoline = match.group(0).strip()  # like 'mRestrictedScreen=(0,0) 720x1184'
            resolution = infoline.split(" ")[1].split("x")
            if isinstance(resolution, list) and len(resolution) == 2:
                result = int(str(resolution[0])), int(str(resolution[1]))

        return result

    def _getPhysicalDisplayInfo(self):
        phyDispRE = re.compile('.*PhysicalDisplayInfo{(?P<width>\d+) x (?P<height>\d+), .*, density (?P<density>[\d.]+).*')
        out = self.adb.shell('dumpsys display')
        m = phyDispRE.search(out)
        if m:
            displayInfo = {}
            for prop in ['width','height']:
                displayInfo[prop] = int(m.group(prop))
            for prop in ['density']:
                # In mPhysicalDisplayInfo density is already a factor, no need to calculate
                displayInfo[prop] = float(m.group(prop))
            return displayInfo

        ''' Gets C{mPhysicalDisplayInfo} values from dumpsys. This is a method to obtain display dimensions and density'''
        phyDispRE = re.compile('Physical size: (?P<width>\d+)x(?P<height>\d+).*Physical density: (?P<density>\d+)', re.S)
        m = phyDispRE.search(self.adb.shell('wm size; wm density'))
        if m:
            displayInfo = {}
            for prop in [ 'width', 'height' ]:
                displayInfo[prop] = int(m.group(prop))
            for prop in [ 'density' ]:
                displayInfo[prop] = float(m.group(prop))
            return displayInfo

        # This could also be mSystem or mOverscanScreen
        phyDispRE = re.compile('\s*mUnrestrictedScreen=\((?P<x>\d+),(?P<y>\d+)\) (?P<width>\d+)x(?P<height>\d+)')
        # This is known to work on older versions (i.e. API 10) where mrestrictedScreen is not available
        dispWHRE = re.compile('\s*DisplayWidth=(?P<width>\d+) *DisplayHeight=(?P<height>\d+)')
        out = self.adb.shell('dumpsys window')
        m = phyDispRE.search(out, 0)
        if not m:
            m = dispWHRE.search(out, 0)
        if m:
            displayInfo = {}
            for prop in ['width','height']:
                displayInfo[prop] = int(m.group(prop))
            for prop in ['density']:
                d = self.__getDisplayDensity(None, strip=True)
                if d:
                    displayInfo[prop] = d
                else:
                    # No available density information
                    displayInfo[prop] = -1.0
            return displayInfo

    def __getDisplayDensity(self, key, strip=True):
        BASE_DPI = 160.0
        d = self.getprop('ro.sf.lcd_density', strip)
        if d:
            return float(d)/BASE_DPI
        d = self.getprop('qemu.sf.lcd_density', strip)
        if d:
            return float(d)/BASE_DPI
        return -1.0

    def getDisplayOrientation(self):
        # another way to get orientation, for old sumsung device(sdk version 15) from xiaoma
        SurfaceFlingerRE = re.compile('orientation=(\d+)')
        output = self.adb.shell('dumpsys SurfaceFlinger')
        m = SurfaceFlingerRE.search(output)
        if m:
            return int(m.group(1))

        # Fallback method to obtain the orientation
        # See https://github.com/dtmilano/AndroidViewClient/issues/128
        surfaceOrientationRE = re.compile('SurfaceOrientation:\s+(\d+)')
        output = self.adb.shell('dumpsys input')
        m = surfaceOrientationRE.search(output)
        if m:
            return int(m.group(1))

        # We couldn't obtain the orientation
        # return -1
        return 0 if self.size["height"] > self.size['width'] else 1

    def _transformPointByOrientation(self, tuple_xy):

        x, y = tuple_xy
        """图片坐标转换为物理坐标，即相对于手机物理左上角的坐标(minitouch点击的是物理坐标)."""
        x, y = XYTransformer.up_2_ori(
            (x, y),
            (self.size["physical_width"], self.size["physical_height"]),
            self.size["orientation"]
        )
        return x, y

    def refreshOrientationInfo(self, ori=None):
        """
        update dev orientation
        if ori is assigned, set to it(useful when running a orientation monitor outside)
        """
        if ori is None:
            ori = self.getDisplayOrientation()
        LOGGING.debug("refreshOrientationInfo:%s", ori)
        self.size["orientation"] = ori
        self.size["rotation"] = ori * 90
        if getattr(self, "minicap", None):
            self.minicap.update_rotation(self.size["rotation"])

    def _initOrientationWatcher(self):
        try:
            apk_path = self.path_app(ROTATIONWATCHER_PACKAGE)
        except MoaError:
            self.install_app(ROTATIONWATCHER_APK, ROTATIONWATCHER_PACKAGE)
            apk_path = self.path_app(ROTATIONWATCHER_PACKAGE)
        p = self.adb.shell('export CLASSPATH=%s;exec app_process /system/bin jp.co.cyberagent.stf.rotationwatcher.RotationWatcher' % apk_path, not_wait=True)
        if p.poll() is not None:
            raise RuntimeError("orientationWatcher setup error")
        return p

    def orientationWatcher(self):

        def _refresh_by_ow():
            line = self.ow_proc.stdout.readline()
            if line == b"":
                if LOGGING is not None:  # may be None atexit
                    LOGGING.error("orientationWatcher has ended")
                return None

            ori = int(line) / 90
            self.refreshOrientationInfo(ori)
            return ori

        def _refresh_orientation(self):
            self.ow_proc = self._initOrientationWatcher()
            reg_cleanup(self.ow_proc.kill)
            while True:
                ori = _refresh_by_ow()
                if ori is None:
                    break
                if getattr(self, "ow_callback", None):
                    self.ow_callback(ori, *self.ow_callback_args)

        # _refresh_by_ow()  # do not refresh blockingly
        self._t = threading.Thread(target=_refresh_orientation, args=(self, ))
        self._t.daemon = True
        self._t.start()

    def reg_ow_callback(self, ow_callback, *ow_callback_args):
        """方向变化的时候的回调函数，第一个参数一定是ori，如果断掉了，ori传None"""
        self.ow_callback = ow_callback
        self.ow_callback_args = ow_callback_args

    def logcat(self, *args, **kwargs):
        return self.adb.logcat(*args, **kwargs)

    def pinch(self, *args, **kwargs):
        return self.minitouch.pinch(*args, **kwargs)


class XYTransformer(object):
    """
    transform xy by orientation
    upright<-->original
    """
    @staticmethod
    def up_2_ori(tuple_xy, tuple_wh, orientation):
        x, y = tuple_xy
        w, h = tuple_wh

        if orientation == 1:
            x, y = w - y, x
        elif orientation == 2:
            x, y = w - x, h - y
        elif orientation == 3:
            x, y = y, h - x
        return x, y

    @staticmethod
    def ori_2_up(tuple_xy, tuple_wh, orientation):
        x, y = tuple_xy
        w, h = tuple_wh

        if orientation == 1:
            x, y = y, w - x
        elif orientation == 2:
            x, y = w - x, h - y
        elif orientation == 3:
            x, y = h - y, x
        return x, y
