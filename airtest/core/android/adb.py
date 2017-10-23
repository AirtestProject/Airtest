# -*- coding: utf-8 -*-
import subprocess
import threading
import platform
import warnings
import random
import time
import sys
import os
import re
from airtest.core.error import AirtestError, AdbError, AdbShellError, DeviceConnectionError
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.logger import get_logger
from airtest.utils.retry import retries
from airtest.utils.snippet import reg_cleanup, split_cmd, get_std_encoding
from airtest.core.android.constant import SDK_VERISON_NEW, DEFAULT_ADB_PATH, IP_PATTERN
LOGGING = get_logger('adb')


class ADB(object):
    """adb client"""

    status_device = "device"
    status_offline = "offline"
    SHELL_ENCODING = "utf-8"

    def __init__(self, serialno=None, adb_path=None, server_addr=None):
        self.serialno = serialno
        self.adb_path = adb_path or self.builtin_adb_path()
        self._set_cmd_options(server_addr)
        self.connect()
        self._sdk_version = None
        self._line_breaker = None
        self._display_info = None
        self._display_info_lock = threading.Lock()
        self._forward_local_using = []
        reg_cleanup(self._cleanup_forwards)

    @staticmethod
    def builtin_adb_path():
        """get airtest built-in adb executable path"""
        system = platform.system()
        adb_path = DEFAULT_ADB_PATH[system]
        # overwrite uiautomator adb
        if "ANDROID_HOME" in os.environ:
            del os.environ["ANDROID_HOME"]
        os.environ["PATH"] = os.path.dirname(adb_path) + os.pathsep + os.environ["PATH"]
        return adb_path

    def _set_cmd_options(self, server_addr=None):
        """set adb cmd options -H -P"""
        self.host = server_addr[0] if server_addr else "127.0.0.1"
        self.port = server_addr[1] if server_addr else 5037
        self.cmd_options = [self.adb_path]
        if self.host not in ("localhost", "127.0.0.1"):
            self.cmd_options += ['-H', self.host]
        if self.port != 5037:
            self.cmd_options += ['-P', str(self.port)]

    def start_server(self):
        """adb start-server"""
        return self.cmd("start-server", device=False)

    def version(self):
        """adb version 1.0.39"""
        return self.cmd("version", device=False).strip()

    def start_cmd(self, cmds, device=True):
        """
        start a subprocess to run adb cmd
        device: specify -s serialno if True
        """
        if device:
            if not self.serialno:
                raise RuntimeError("please set serialno first")
            cmd_options = self.cmd_options + ['-s', self.serialno]
        else:
            cmd_options = self.cmd_options

        cmds = cmd_options + split_cmd(cmds)
        LOGGING.debug(" ".join(cmds))

        cmds = [c.encode(get_std_encoding(sys.stdin)) for c in cmds]
        proc = subprocess.Popen(
            cmds,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return proc

    def cmd(self, cmds, device=True, ensure_unicode=True):
        """
        get adb cmd output
        device: specify -s serialno if True
        """
        proc = self.start_cmd(cmds, device)
        stdout, stderr = proc.communicate()

        if ensure_unicode:
            stdout = stdout.decode(get_std_encoding(sys.stdout))
            stderr = stderr.decode(get_std_encoding(sys.stderr))

        if proc.returncode > 0:
            # adb connection error
            if re.search(DeviceConnectionError.DEVICE_CONNECTION_ERROR, stderr):
                raise DeviceConnectionError(stderr)
            else:
                raise AdbError(stdout, stderr)
        return stdout

    def devices(self, state=None):
        """adb devices"""
        patten = re.compile(r'^[\w\d.:-]+\t[\w]+$')
        device_list = []
        # self.start_server()
        output = self.cmd("devices", device=False)
        for line in output.splitlines():
            line = line.strip()
            if not line or not patten.match(line):
                continue
            serialno, cstate = line.split('\t')
            if state and cstate != state:
                continue
            device_list.append((serialno, cstate))
        return device_list

    def connect(self, force=False):
        """adb connect, if remote devices, connect first"""
        if self.serialno and ":" in self.serialno and (force or self.get_status() != "device"):
            connect_result = self.cmd("connect %s" % self.serialno)
            LOGGING.info(connect_result)

    def disconnect(self):
        """adb disconnect"""
        if ":" in self.serialno:
            self.cmd("disconnect %s" % self.serialno)

    def get_status(self):
        """get device's adb status"""
        proc = self.start_cmd("get-state")
        stdout, stderr = proc.communicate()

        stdout = stdout.decode(get_std_encoding(sys.stdout))
        stderr = stderr.decode(get_std_encoding(sys.stdout))

        if proc.returncode == 0:
            return stdout.strip()
        elif "not found" in stderr:
            return None
        else:
            raise AdbError(stdout, stderr)

    def wait_for_device(self, timeout=5):
        """
        adb wait-for-device
        if timeout, raise AirtestError
        """
        proc = self.start_cmd("wait-for-device")
        timer = threading.Timer(timeout, proc.kill)
        timer.start()
        ret = proc.wait()
        if ret == 0:
            timer.cancel()
        else:
            raise DeviceConnectionError("device not ready")

    def start_shell(self, cmds):
        cmds = ['shell'] + split_cmd(cmds)
        return self.start_cmd(cmds)

    def raw_shell(self, cmds, ensure_unicode=True):
        cmds = ['shell'] + split_cmd(cmds)
        out = self.cmd(cmds, ensure_unicode=False)
        if not ensure_unicode:
            return out
        # use shell encoding to decode output
        try:
            return out.decode(self.SHELL_ENCODING)
        except UnicodeDecodeError:
            warnings.warn("shell output decode {} fail. repr={}".format(self.SHELL_ENCODING, repr(out)))
            return unicode(repr(out))

    def shell(self, cmd):
        """
        adb shell
        """
        if self.sdk_version < SDK_VERISON_NEW:
            # for sdk_version < 25, adb shell do not raise error
            # https://stackoverflow.com/questions/9379400/adb-error-codes
            cmd = split_cmd(cmd) + [";", "echo", "---$?---"]
            out = self.raw_shell(cmd).rstrip()
            m = re.match("(.*)---(\d+)---$", out, re.DOTALL)
            if not m:
                warnings.warn("return code not matched")
                stdout = out
                returncode = 0
            else:
                stdout = m.group(1)
                returncode = int(m.group(2))
            if returncode > 0:
                raise AdbShellError("", stdout)
            return stdout
        else:
            try:
                out = self.raw_shell(cmd)
            except AdbError as err:
                raise AdbShellError(err.stdout, err.stderr)
            else:
                return out

    def keyevent(self, keyname):
        self.shell(["input", "keyevent", keyname.upper()])

    def getprop(self, key, strip=True):
        """adb shell getprop"""
        prop = self.raw_shell(['getprop', key])
        if strip:
            prop = prop.rstrip('\r\n')
        return prop

    @property
    def sdk_version(self):
        """adb shell get sdk version"""
        if self._sdk_version is None:
            keyname = 'ro.build.version.sdk'
            self._sdk_version = int(self.getprop(keyname))
        return self._sdk_version

    def push(self, local, remote):
        """adb push"""
        self.cmd(["push", local, remote])

    def pull(self, remote, local):
        """adb pull"""
        self.cmd(["pull", remote, local])

    def forward(self, local, remote, no_rebind=True):
        """adb forward"""
        cmds = ['forward']
        if no_rebind:
            cmds += ['--no-rebind']
        self.cmd(cmds + [local, remote])
        # register for cleanup atexit
        if local not in self._forward_local_using:
            self._forward_local_using.append(local)

    def get_forwards(self):
        """adb forward --list"""
        out = self.cmd(['forward', '--list'])
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            cols = line.split()
            if len(cols) != 3:
                continue
            serialno, local, remote = cols
            yield serialno, local, remote

    @classmethod
    def get_available_forward_local(cls):
        """
        random a forward local port, use forward --no-rebind to try forward
        """
        return random.randint(11111, 20000)

    @retries(3)
    def setup_forward(self, device_port):
        """
        setup adb forward with a random local port, try bind at most 3 times
        device_port can be a string or a function(localport)
        eg: "tcp:5001" or "localabstract:{}".format
        """
        localport = self.get_available_forward_local()
        if callable(device_port):
            device_port = device_port(localport)
        self.forward("tcp:%s" % localport, device_port)
        return localport, device_port

    def remove_forward(self, local=None):
        """adb forward --remove"""
        if local:
            cmds = ["forward", "--remove", local]
        else:
            cmds = ["forward", "--remove-all"]
        self.cmd(cmds)
        # unregister for cleanup
        if local in self._forward_local_using:
            self._forward_local_using.remove(local)

    def install_app(self, filepath, replace=False):
        if not replace:
            cmds = ["install", filepath]
        else:
            cmds = ["install", "-r", filepath]
        out = self.cmd(cmds)
        return out

    def pm_install(self, filepath, replace=False):
        """adb push & pm install, compatibility is better than adb install"""
        filename = os.path.basename(filepath)
        device_dir = "/data/local/tmp"
        # 如果apk名称包含空格，需要用引号括起来
        device_path = '\"%s/%s\"' % (device_dir, filename)

        out = self.cmd(["push", filepath, device_dir])
        print(out)

        if not replace:
            self.shell(['pm', 'install', device_path])
        else:
            self.shell(['pm', 'install', '-r', device_path])

    def uninstall_app(self, package):
        """adb uninstall"""
        return self.cmd(['uninstall', package])

    def pm_uninstall(self, package, keepdata=False):
        cmd = ['pm', 'uninstall', package]
        if keepdata:
            cmd.append('-k')
        self.shell(cmd)

    def snapshot(self):
        """take a screenshot"""
        raw = self.cmd('shell screencap -p', ensure_unicode=False)
        return raw.replace(self.line_breaker, b"\n")

    # PEP 3113 -- Removal of Tuple Parameter Unpacking
    # https://www.python.org/dev/peps/pep-3113/
    def touch(self, tuple_xy):
        """touch screen"""
        x, y = tuple_xy
        self.shell('input tap %d %d' % (x, y))
        time.sleep(0.1)

    def swipe(self, tuple_x0y0, tuple_x1y1, duration=500):
        """swipe screen"""
        # prot python 3
        x0, y0 = tuple_x0y0
        x1, y1 = tuple_x1y1

        version = self.sdk_version
        if version <= 15:
            raise AirtestError('swipe: API <= 15 not supported (version=%d)' % version)
        elif version <= 17:
            self.shell('input swipe %d %d %d %d' % (x0, y0, x1, y1))
        else:
            self.shell('input touchscreen swipe %d %d %d %d %d' % (x0, y0, x1, y1, duration))

    def logcat(self, grep_str="", extra_args="", read_timeout=10):
        cmds = "shell logcat"
        if extra_args:
            cmds += " " + extra_args
        if grep_str:
            cmds += " | grep " + grep_str
        logcat_proc = self.start_cmd(cmds)
        nbsp = NonBlockingStreamReader(logcat_proc.stdout, print_output=False)
        while True:
            line = nbsp.readline(read_timeout)
            if line is None:
                break
            else:
                yield line
        nbsp.kill()
        logcat_proc.kill()
        return

    def exists_file(self, filepath):
        try:
            out = self.shell(["ls", filepath])
        except AdbShellError:
            return False
        else:
            return not("No such file or directory" in out)

    def _cleanup_forwards(self):
        for local in self._forward_local_using[:]:
            self.remove_forward(local)

    @property
    def line_breaker(self):
        if not self._line_breaker:
            if platform.system() == "Windows":
                if self.sdk_version >= SDK_VERISON_NEW:
                    line_breaker = b"\r\n"
                else:
                    line_breaker = b"\r\r\n"
            else:
                if self.sdk_version >= SDK_VERISON_NEW:
                    line_breaker = b"\n"
                else:
                    line_breaker = b"\r\n"
            self._line_breaker = line_breaker
        return self._line_breaker

    @property
    def display_info(self):
        self._display_info_lock.acquire()
        if not self._display_info:
            self._display_info = self.get_display_info()
        self._display_info_lock.release()
        return self._display_info

    def get_display_info(self):
        display_info = self.getPhysicalDisplayInfo()
        display_info["orientation"] = self.getDisplayOrientation()
        display_info["rotation"] = display_info["orientation"] * 90
        display_info["max_x"], display_info["max_y"] = self._getMaxXY()
        return display_info

    def _getMaxXY(self):
        ret = self.shell('getevent -p').split('\n')
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
        if self.serialno in special_device_list:
            # 上面已经确保了宽小于高，现在反过来->宽大于高
            info["height"], info["width"] = info["width"], info["height"]
            info["physical_width"], info["physical_height"] = info["physical_height"], info["physical_width"]
        return info

    def _getRestrictedScreen(self):
        """Get mRestrictedScreen from 'adb -s sno shell dumpsys window' """
        # 获取设备有效内容的分辨率(屏幕内含有软按键、S6 Edge等设备，进行黑边去除.)
        result = None
        # 根据设备序列号拿到对应的mRestrictedScreen参数：
        dumpsys_info = self.shell("dumpsys window")
        match = re.search(r'mRestrictedScreen=.+', dumpsys_info)
        if match:
            infoline = match.group(0).strip()  # like 'mRestrictedScreen=(0,0) 720x1184'
            resolution = infoline.split(" ")[1].split("x")
            if isinstance(resolution, list) and len(resolution) == 2:
                result = int(str(resolution[0])), int(str(resolution[1]))

        return result

    def _getPhysicalDisplayInfo(self):
        phyDispRE = re.compile('.*PhysicalDisplayInfo{(?P<width>\d+) x (?P<height>\d+), .*, density (?P<density>[\d.]+).*')
        out = self.shell('dumpsys display')
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
        m = phyDispRE.search(self.shell('wm size; wm density'))
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
        out = self.shell('dumpsys window')
        m = phyDispRE.search(out, 0)
        if not m:
            m = dispWHRE.search(out, 0)
        if m:
            displayInfo = {}
            for prop in ['width' , 'height']:
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
            return float(d) / BASE_DPI
        d = self.getprop('qemu.sf.lcd_density', strip)
        if d:
            return float(d) / BASE_DPI
        return -1.0

    def getDisplayOrientation(self):
        # another way to get orientation, for old sumsung device(sdk version 15) from xiaoma
        SurfaceFlingerRE = re.compile('orientation=(\d+)')
        output = self.shell('dumpsys SurfaceFlinger')
        m = SurfaceFlingerRE.search(output)
        if m:
            return int(m.group(1))

        # Fallback method to obtain the orientation
        # See https://github.com/dtmilano/AndroidViewClient/issues/128
        surfaceOrientationRE = re.compile('SurfaceOrientation:\s+(\d+)')
        output = self.shell('dumpsys input')
        m = surfaceOrientationRE.search(output)
        if m:
            return int(m.group(1))

        # We couldn't obtain the orientation
        # Guess by height > width
        return 0 if self.display_info["height"] > self.display_info['width'] else 1

    def get_top_activity(self):
        dat = self.shell('dumpsys activity top')
        activityRE = re.compile('\s*ACTIVITY ([A-Za-z0-9_.]+)/([A-Za-z0-9_.]+) \w+ pid=(\d+)')
        m = activityRE.search(dat)
        if m:
            return (m.group(1), m.group(2), m.group(3))
        else:
            raise AirtestError("Can not get top activity, output:%s" % dat)

    def is_keyboard_shown(self):
        dim = self.shell('dumpsys input_method')
        if dim:
            return "mInputShown=true" in dim
        return False

    def is_screenon(self):
        screenOnRE = re.compile('mScreenOnFully=(true|false)')
        m = screenOnRE.search(self.shell('dumpsys window policy'))
        if m:
            return (m.group(1) == 'true')
        raise AirtestError("Couldn't determine screen ON state")

    def is_locked(self):
        """not work on xiaomi 2s"""
        lockScreenRE = re.compile('mShowingLockscreen=(true|false)')
        m = lockScreenRE.search(self.shell('dumpsys window policy'))
        if not m:
            raise AirtestError("Couldn't determine screen lock state")
        return (m.group(1) == 'true')

    def unlock(self):
        """not work on many devices"""
        self.shell('input keyevent MENU')
        self.shell('input keyevent BACK')

    def get_package_version(self, package):
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
            -d: filter to only show disabled packages.
            -e: filter to only show enabled packages.
            -s: filter to only show system packages.
            -3: filter to only show third party packages.
            -i: see the installer for the packages.
            -u: also include uninstalled packages.
        """
        cmd = ["pm", "list", "packages"]
        if third_only:
            cmd.append("-3")
        output = self.shell(cmd)
        packages = output.splitlines()
        # remove all empty string; "package:xxx" -> "xxx"
        packages = [p.split(":")[1] for p in packages if p]
        return packages

    def path_app(self, package):
        try:
            output = self.shell(['pm', 'path', package])
        except AdbShellError:
            output = ""
        if 'package:' not in output:
            raise AirtestError('package not found, output:[%s]' % output)
        return output.split(":")[1].strip()

    def check_app(self, package):
        output = self.shell(['dumpsys', 'package', package]).strip()
        if package not in output:
            raise AirtestError('package "{}" not found'.format(package))
        return True

    def start_app(self, package, activity=None):
        if not activity:
            self.shell(['monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1'])
        else:
            self.shell(['am', 'start', '-n', '%s/%s.%s' % (package, package, activity)])

    def stop_app(self, package):
        self.shell(['am', 'force-stop', package])

    def clear_app(self, package):
        self.shell(['pm', 'clear', package])

    def get_ip_address(adb):
        try:
            res = adb.shell('netcfg | grep wlan0')
        except AdbShellError:
            res = ''
        matcher = re.search(r' ((\d+\.){3}\d+)/\d+', res)
        if matcher:
            return matcher.group(1)
        else:
            try:
                res = adb.shell('ifconfig')
            except AdbShellError:
                res = ''
            matcher = re.search(r'wlan0.*?inet addr:((\d+\.){3}\d+)', res, re.DOTALL)
            if matcher:
                return matcher.group(1)
            else:
                try:
                    res = adb.shell('getprop dhcp.wlan0.ipaddress')
                except AdbShellError:
                    res = ''
                matcher = IP_PATTERN.search(res)
                if matcher:
                    return matcher.group(0)
        return None

    def get_gateway_address(self):
        ip2int = lambda ip: reduce(lambda a, b: (a << 8) + b, map(int, ip.split('.')), 0)
        int2ip = lambda n: '.'.join([str(n >> (i << 3) & 0xFF) for i in range(0, 4)[::-1]])
        try:
            res = self.shell('getprop dhcp.wlan0.gateway')
        except AdbShellError:
            res = ''
        matcher = IP_PATTERN.search(res)
        if matcher:
            return matcher.group(0)
        ip = self.get_ip_address()
        if not ip:
            return None
        mask_len = self._get_subnet_mask_len()
        gateway = (ip2int(ip) & (((1 << mask_len) - 1) << (32 - mask_len))) + 1
        return int2ip(gateway)

    def _get_subnet_mask_len(self):
        try:
            res = self.shell('netcfg | grep wlan0')
        except AdbShellError:
            pass
        else:
            matcher = re.search(r' (\d+\.){3}\d+/(\d+) ', res)
            if matcher:
                return int(matcher.group(2))
        # 获取不到网段长度就默认取17
        print('[iputils WARNING] fail to get subnet mask len. use 17 as default.')
        return 17
