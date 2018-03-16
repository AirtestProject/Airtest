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
from airtest.utils.compat import PY3, decode_path
from airtest.core.android.constant import SDK_VERISON_NEW, DEFAULT_ADB_PATH, IP_PATTERN
# LOGGING = get_logger('adb')
LOGGING = get_logger(__name__)


class ADB(object):
    """adb client object class"""

    _instances = []
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
        self.__class__._instances.append(self)

    @staticmethod
    def builtin_adb_path():
        """
        Return built-in adb executable path

        Returns:
            adb executable path

        """
        system = platform.system()
        adb_path = DEFAULT_ADB_PATH[system]
        # overwrite uiautomator adb
        if "ANDROID_HOME" in os.environ:
            del os.environ["ANDROID_HOME"]
        return adb_path

    def _set_cmd_options(self, server_addr=None):
        """
        Set communication parameters (host and port) between adb server and adb client

        Args:
            server_addr: adb server address, default is 127.0.0.1:5037

        Returns:
            None

        """
        self.host = server_addr[0] if server_addr else "127.0.0.1"
        self.port = server_addr[1] if server_addr else 5037
        self.cmd_options = [self.adb_path]
        if self.host not in ("localhost", "127.0.0.1"):
            self.cmd_options += ['-H', self.host]
        if self.port != 5037:
            self.cmd_options += ['-P', str(self.port)]

    def start_server(self):
        """
        Perform `adb start-server` command to start the adb server

        Returns:
            None

        """
        return self.cmd("start-server", device=False)

    def kill_server(self):
        """
        Perform `adb kill-server` command to kill the adb server

        Returns:
            None

        """
        return self.cmd("kill-server", device=False)

    def version(self):
        """
        Perform `adb version` command and return the command output

        Returns:
            command output

        """
        return self.cmd("version", device=False).strip()

    def start_cmd(self, cmds, device=True):
        """
        Start a subprocess with adb command(s)

        Args:
            cmds: command(s) to be run
            device: if True, the device serial number must be specified by `-s serialno` argument

        Raises:
            RuntimeError: if `device` is True and serialno is not specified

        Returns:
            a subprocess

        """
        if device:
            if not self.serialno:
                raise RuntimeError("please set serialno first")
            cmd_options = self.cmd_options + ['-s', self.serialno]
        else:
            cmd_options = self.cmd_options

        cmds = cmd_options + split_cmd(cmds)
        LOGGING.debug(" ".join(cmds))

        if not PY3:
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
        Run the adb command(s) in subprocess and return the standard output

        Args:
            cmds: command(s) to be run
            device: if True, the device serial number must be specified by -s serialno argument
            ensure_unicode: encode/decode unicode of standard outputs (stdout, stderr)

        Raises:
            DeviceConnectionError: if any error occurs when connecting the device
            AdbError: if any other adb error occurs

        Returns:
            command(s) standard output (stdout)

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
        """
        Perform `adb devices` command and return the list of adb devices

        Args:
            state: optional parameter to filter devices in specific state

        Returns:
            list od adb devices

        """
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
        """
        Perform `adb connect` command, remote devices are preferred to connect first

        Args:
            force: force connection, default is False

        Returns:
            None

        """
        if self.serialno and ":" in self.serialno and (force or self.get_status() != "device"):
            connect_result = self.cmd("connect %s" % self.serialno)
            LOGGING.info(connect_result)

    def disconnect(self):
        """
        Perform `adb disconnect` command

        Returns:
            None

        """
        if ":" in self.serialno:
            self.cmd("disconnect %s" % self.serialno)

    def get_status(self):
        """
        Perform `adb get-state` and return the device status

        Raises:
            AdbError: if status cannot be obtained from the device

        Returns:
            None if status is `not found`, otherwise return the standard output from `adb get-state` command

        """
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
        Perform `adb wait-for-device` command

        Args:
            timeout: time interval in seconds to wait for device

        Raises:
            DeviceConnectionError: if device is not available after timeout

        Returns:
            None

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
        """
        Handle `adb shell` command(s)

        Args:
            cmds: adb shell command(s)

        Returns:
            None

        """
        cmds = ['shell'] + split_cmd(cmds)
        return self.start_cmd(cmds)

    def raw_shell(self, cmds, ensure_unicode=True):
        """
        Handle `adb shell` command(s) with unicode support

        Args:
            cmds: adb shell command(s)
            ensure_unicode: decode/encode unicode True or False, default is True

        Returns:
            command(s) output

        """
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
        Run the `adb shell` command on the device

        Args:
            cmd: a command to be run

        Raises:
            AdbShellError: if command return value is non-zero or if any other `AdbError` occurred

        Returns:
            command output

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
        """
        Perform `adb shell input keyevent` command on the device

        Args:
            keyname: key event name

        Returns:
            None

        """
        self.shell(["input", "keyevent", keyname.upper()])

    def getprop(self, key, strip=True):
        """
        Perform `adb shell getprop` on the device

        Args:
            key: key value for property
            strip: True or False to strip the return carriage and line break from returned string

        Returns:
            propery value

        """
        prop = self.raw_shell(['getprop', key])
        if strip:
            prop = prop.rstrip('\r\n')
        return prop

    @property
    def sdk_version(self):
        """
        Get the SDK version from the device

        Returns:
            SDK version
        """
        if self._sdk_version is None:
            keyname = 'ro.build.version.sdk'
            self._sdk_version = int(self.getprop(keyname))
        return self._sdk_version

    def push(self, local, remote):
        """
        Perform `adb push` command

        Args:
            local: local file to be copied to the device
            remote: destination on the device where the file will be copied

        Returns:
            None

        """
        self.cmd(["push", local, remote], ensure_unicode=False)

    def pull(self, remote, local):
        """
        Perform `adb pull` command
        Args:
            remote: remote file to be downloaded from the device
            local: local destination where the file will be downloaded from the device

        Returns:
            None
        """
        self.cmd(["pull", remote, local], ensure_unicode=False)

    def forward(self, local, remote, no_rebind=True):
        """
        Perform `adb forward` command

        Args:
            local: local tcp port to be forwarded
            remote: tcp port of the device where the local tcp port will be forwarded
            no_rebind: True or False

        Returns:
            None

        """
        cmds = ['forward']
        if no_rebind:
            cmds += ['--no-rebind']
        self.cmd(cmds + [local, remote])
        # register for cleanup atexit
        if local not in self._forward_local_using:
            self._forward_local_using.append(local)

    def get_forwards(self):
        """
        Perform `adb forward --list`command

        Yields:
            serial number, local tcp port, remote tcp port

        Returns:
            None

        """
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
        Generate a pseudo random number between 11111 and 20000 that will be used as local forward port

        Returns:
            integer between 11111 and 20000

        Note:
            use `forward --no-rebind` to check if port is available
        """
        return random.randint(11111, 20000)

    @retries(3)
    def setup_forward(self, device_port):
        """
        Generate pseudo random local port and check if the port is available.

        Args:
            device_port: it can be string or the value of the `function(localport)`,
                         e.g. `"tcp:5001"` or `"localabstract:{}".format`

        Returns:
            local port and device port

        """
        localport = self.get_available_forward_local()
        if callable(device_port):
            device_port = device_port(localport)
        self.forward("tcp:%s" % localport, device_port)
        return localport, device_port

    def remove_forward(self, local=None):
        """
        Perform `adb forward --remove` command

        Args:
            local: local tcp port

        Returns:
            None

        """
        if local:
            cmds = ["forward", "--remove", local]
        else:
            cmds = ["forward", "--remove-all"]
        self.cmd(cmds)
        # unregister for cleanup
        if local in self._forward_local_using:
            self._forward_local_using.remove(local)

    def install_app(self, filepath, replace=False):
        """
        Perform `adb install` command

        Args:
            filepath: full path to file to be installed on the device
            replace: force to replace existing application, default is False

        Returns:
            command output

        """
        if isinstance(filepath, str):
            filepath = decode_path(filepath)

        if not replace:
            cmds = ["install", filepath]
        else:
            cmds = ["install", "-r", filepath]
        out = self.cmd(cmds)
        return out

    def pm_install(self, filepath, replace=False):
        """
        Perform `adb push` and `adb install` commands

        Note:
            This is more reliable and recommended way of installing `.apk` files

        Args:
            filepath: full path to file to be installed on the device
            replace: force to replace existing application, default is False

        Returns:
            None

        """
        filename = os.path.basename(filepath)
        device_dir = "/data/local/tmp"
        # if the apk file path contains spaces, the path must be escaped
        device_path = '\"%s/%s\"' % (device_dir, filename)

        out = self.cmd(["push", filepath, device_dir])
        print(out)

        if not replace:
            self.shell(['pm', 'install', device_path])
        else:
            self.shell(['pm', 'install', '-r', device_path])

    def uninstall_app(self, package):
        """
        Perform `adb uninstall` command
        Args:
            package: package name to be uninstalled from the device

        Returns:
            command output

        """
        return self.cmd(['uninstall', package])

    def pm_uninstall(self, package, keepdata=False):
        """
        Perform `adb uninstall` command and delete all related application data

        Args:
            package: package name to be uninstalled from the device
            keepdata: True or False, keep application data after removing the app from the device

        Returns:
            command output

        """
        cmd = ['pm', 'uninstall', package]
        if keepdata:
            cmd.append('-k')
        self.shell(cmd)

    def snapshot(self):
        """
        Take the screenshot of the device display

        Returns:
            command output (stdout)

        """
        raw = self.cmd('shell screencap -p', ensure_unicode=False)
        return raw.replace(self.line_breaker, b"\n")

    # PEP 3113 -- Removal of Tuple Parameter Unpacking
    # https://www.python.org/dev/peps/pep-3113/
    def touch(self, tuple_xy):
        """
        Perform user input (touchscreen) on given coordinates

        Args:
            tuple_xy: coordinates (x, y)

        Returns:
            None

        """
        x, y = tuple_xy
        self.shell('input tap %d %d' % (x, y))
        time.sleep(0.1)

    def swipe(self, tuple_x0y0, tuple_x1y1, duration=500):
        """
        Perform user input (swipe screen) from start point (x,y) to end point (x,y)

        Args:
            tuple_x0y0: start point coordinates (x, y)
            tuple_x1y1: end point coordinates (x, y)
            duration: time interval for action, default 500

        Raises:
            AirtestError: if SDK version is not supported

        Returns:
            None

        """
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
        """
        Perform `adb shell logcat` command and search for given patterns

        Args:
            grep_str: pattern to filter from the logcat output
            extra_args: additional logcat arguments
            read_timeout: time interval to read the logcat, default is 10

        Yields:
            logcat lines containing filtered patterns

        Returns:
            None

        """
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
        """
        Check if the file exits on the device

        Args:
            filepath: path to the file

        Returns:
            True or False if file found or not

        """
        try:
            out = self.shell(["ls", filepath])
        except AdbShellError:
            return False
        else:
            return not("No such file or directory" in out)

    def _cleanup_forwards(self):
        """
        Remove the local forward ports

        Returns:
            None
        """
        for local in self._forward_local_using:
            self.start_cmd(["forward", "--remove", local])

        self._forward_local_using = []

    @property
    def line_breaker(self):
        """
        Set carriage return and line break property for various platforms and SDK versions

        Returns:
            carriage return and line break string

        """
        if not self._line_breaker:
            if self.sdk_version >= SDK_VERISON_NEW:
                line_breaker = os.linesep
            else:
                line_breaker = b'\r' + os.linesep
            self._line_breaker = line_breaker
        return self._line_breaker

    @property
    def display_info(self):
        """
        Set device display properties (orientation, rotation and max values for x and y coordinates)

        Notes:
        if there is a lock screen detected, the function tries to unlock the device first

        Returns:
            device screen properties

        """
        self._display_info_lock.acquire()
        if not self._display_info:
            self._display_info = self.get_display_info()
        self._display_info_lock.release()
        return self._display_info

    def get_display_info(self):
        """
        Get information about device physical display (orientation, rotation and max values for x and y coordinates)

        Returns:
            device screen properties

        """
        display_info = self.getPhysicalDisplayInfo()
        display_info["orientation"] = self.getDisplayOrientation()
        display_info["rotation"] = display_info["orientation"] * 90
        display_info["max_x"], display_info["max_y"] = self._getMaxXY()
        return display_info

    def _getMaxXY(self):
        """
        Get device display maximum values for x and y coordinates

        Returns:
            max x and max y coordinates

        """
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
        """
        Display size and resolution to be obtained:
            1. physical display size (physical_width, physical_height) of the device - this is used by `minitouch` as a
               coordinates system
            1. screen effective resolution (width, height) - this is used by game image adaptation as a coordinates
               system
            1. click range resolution (max_x, max_y)

        Returns:
            display size and resolution information

        """

        info = self._getPhysicalDisplayInfo()
        # record the width of physical display (used for screen mapping)
        if info["width"] > info["height"]:
            info["physical_height"], info["physical_width"] = info["width"], info["height"]
        else:
            info["physical_width"], info["physical_height"] = info["width"], info["height"]
        # get the screen effective resolution (e.g., the device with soft keys requires resolution removal)
        mRestrictedScreen = self._getRestrictedScreen()
        if mRestrictedScreen:
            info["width"], info["height"] = mRestrictedScreen
        # as the mRestrictedScreen is related to the horizontal and vertical state of the device, the custom settings
        # for height and width are set here
        if info["width"] > info["height"]:
            info["height"], info["width"] = info["width"], info["height"]
        # for a special device, do the special treatment
        special_device_list = ["5fde825d043782fc", "320496728874b1a5"]
        if self.serialno in special_device_list:
            # for these devices: width > hight, swap the width and the height
            info["height"], info["width"] = info["width"], info["height"]
            info["physical_width"], info["physical_height"] = info["physical_height"], info["physical_width"]
        return info

    def _getRestrictedScreen(self):
        """
        Get value for mRestrictedScreen from `adb -s sno shell dumpsys window`

        Returns:
            screen resolution mRestrictedScreen value as tuple (x, y)

        """
        # get the effective screen resolution of the device
        result = None
        # get the corresponding mRestrictedScreen parameters according to the device serial number
        dumpsys_info = self.shell("dumpsys window")
        match = re.search(r'mRestrictedScreen=.+', dumpsys_info)
        if match:
            infoline = match.group(0).strip()  # like 'mRestrictedScreen=(0,0) 720x1184'
            resolution = infoline.split(" ")[1].split("x")
            if isinstance(resolution, list) and len(resolution) == 2:
                result = int(str(resolution[0])), int(str(resolution[1]))

        return result

    def _getPhysicalDisplayInfo(self):
        """
        Get value for display dimension and density from `mPhysicalDisplayInfo` value obtained from `dumpsys` command.

        Returns:
            physical display info for dimension and density

        """
        phyDispRE = re.compile('.*PhysicalDisplayInfo{(?P<width>\d+) x (?P<height>\d+), .*, density (?P<density>[\d.]+).*')
        out = self.raw_shell('dumpsys display')
        m = phyDispRE.search(out)
        if m:
            displayInfo = {}
            for prop in ['width', 'height']:
                displayInfo[prop] = int(m.group(prop))
            for prop in ['density']:
                # In mPhysicalDisplayInfo density is already a factor, no need to calculate
                displayInfo[prop] = float(m.group(prop))
            return displayInfo

        # gets C{mPhysicalDisplayInfo} values from dumpsys. This is a method to obtain display dimensions and density
        phyDispRE = re.compile('Physical size: (?P<width>\d+)x(?P<height>\d+).*Physical density: (?P<density>\d+)', re.S)
        m = phyDispRE.search(self.raw_shell('wm size; wm density'))
        if m:
            displayInfo = {}
            for prop in ['width', 'height']:
                displayInfo[prop] = int(m.group(prop))
            for prop in ['density']:
                displayInfo[prop] = float(m.group(prop))
            return displayInfo

        # This could also be mSystem or mOverscanScreen
        phyDispRE = re.compile('\s*mUnrestrictedScreen=\((?P<x>\d+),(?P<y>\d+)\) (?P<width>\d+)x(?P<height>\d+)')
        # This is known to work on older versions (i.e. API 10) where mrestrictedScreen is not available
        dispWHRE = re.compile('\s*DisplayWidth=(?P<width>\d+) *DisplayHeight=(?P<height>\d+)')
        out = self.raw_shell('dumpsys window')
        m = phyDispRE.search(out, 0)
        if not m:
            m = dispWHRE.search(out, 0)
        if m:
            displayInfo = {}
            for prop in ['width', 'height']:
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
        """
        Get display density

        Args:
            key:
            strip: strip the output

        Returns:
            display density

        """
        BASE_DPI = 160.0
        d = self.getprop('ro.sf.lcd_density', strip)
        if d:
            return float(d) / BASE_DPI
        d = self.getprop('qemu.sf.lcd_density', strip)
        if d:
            return float(d) / BASE_DPI
        return -1.0

    def getDisplayOrientation(self):
        """
        Another way to get the display orientation, this works well for older devices (SDK version 15)

        Returns:
            display orientation information

        """
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
        """
        Perform `adb shell dumpsys activity top` command search for the top activity

        Raises:
            AirtestError: if top activity cannot be obtained

        Returns:
            top activity as a tuple

        """
        dat = self.shell('dumpsys activity top')
        activityRE = re.compile('\s*ACTIVITY ([A-Za-z0-9_.]+)/([A-Za-z0-9_.]+) \w+ pid=(\d+)')
        m = activityRE.search(dat)
        if m:
            return (m.group(1), m.group(2), m.group(3))
        else:
            raise AirtestError("Can not get top activity, output:%s" % dat)

    def is_keyboard_shown(self):
        """
        Perform `adb shell dumpsys input_method` command and search for information if keyboard is shown

        Returns:
            True or False whether the keyboard is shown or not

        """
        dim = self.shell('dumpsys input_method')
        if dim:
            return "mInputShown=true" in dim
        return False

    def is_screenon(self):
        """
        Perform `adb shell dumpsys window policy` command and search for information if screen is turned on or off

        Raises:
            AirtestError: if screen state can't be detected

        Returns:
            True or False whether the screen is turned on or off

        """
        screenOnRE = re.compile('mScreenOnFully=(true|false)')
        m = screenOnRE.search(self.shell('dumpsys window policy'))
        if m:
            return (m.group(1) == 'true')
        raise AirtestError("Couldn't determine screen ON state")

    def is_locked(self):
        """
        Perform `adb shell dumpsys window policy` command and search for information if screen is locked or not

        Raises:
            AirtestError: if lock screen can't be detected

        Returns:
            True or False whether the screen is locked or not

        Notes:
            Does not work on Xiaomi 2S

        """
        lockScreenRE = re.compile('mShowingLockscreen=(true|false)')
        m = lockScreenRE.search(self.shell('dumpsys window policy'))
        if not m:
            raise AirtestError("Couldn't determine screen lock state")
        return (m.group(1) == 'true')

    def unlock(self):
        """
        Perform `adb shell input keyevent MENU` and `adb shell input keyevent BACK` commands to attempt
        to unlock the screen

        Returns:
            None

        Warnings:
            Might not work on all devices

        """
        self.shell('input keyevent MENU')
        self.shell('input keyevent BACK')

    def get_package_version(self, package):
        """
        Perform `adb shell dumpsys package` and search for information about given package version

        Args:
            package: package name

        Returns:
            None if no info has been found, otherwise package version

        """
        package_info = self.shell(['dumpsys', 'package', package])
        matcher = re.search(r'versionCode=(\d+)', package_info)
        if matcher:
            return int(matcher.group(1))
        return None

    def list_app(self, third_only=False):
        """
        Perform `adb shell pm list packages` to print all packages, optionally only
          those whose package name contains the text in FILTER.

        Options
            -f: see their associated file
            -d: filter to only show disabled packages
            -e: filter to only show enabled packages
            -s: filter to only show system packages
            -3: filter to only show third party packages
            -i: see the installer for the packages
            -u: also include uninstalled packages


        Args:
            third_only: print only third party packages

        Returns:
            list of packages

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
        """
        Perform `adb shell pm path` command to print the path to the package

        Args:
            package: package name

        Raises:
            AdbShellError: if any adb error occurs
            AirtestError: if package is not found on the device

        Returns:
            path to the package

        """
        try:
            output = self.shell(['pm', 'path', package])
        except AdbShellError:
            output = ""
        if 'package:' not in output:
            raise AirtestError('package not found, output:[%s]' % output)
        return output.split(":")[1].strip()

    def check_app(self, package):
        """
        Perform `adb shell dumpsys package` command and check if package exists on the device

        Args:
            package: package name

        Raises:
            AirtestError: if package is not found

        Returns:
            True if package has been found

        """
        output = self.shell(['dumpsys', 'package', package]).strip()
        if package not in output:
            raise AirtestError('package "{}" not found'.format(package))
        return True

    def start_app(self, package, activity=None):
        """
        Perform `adb shell monkey` commands to start the application, if `activity` argument is `None`, then
        `adb shell am start` command is used.

        Args:
            package: package name
            activity: activity name

        Returns:
            None

        """
        if not activity:
            self.shell(['monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1'])
        else:
            self.shell(['am', 'start', '-n', '%s/%s.%s' % (package, package, activity)])

    def stop_app(self, package):
        """
        Perform `adb shell am force-stop` command to force stop the application

        Args:
            package: package name

        Returns:
            None

        """
        self.shell(['am', 'force-stop', package])

    def clear_app(self, package):
        """
        Perform `adb shell pm clear` command to clear all application data

        Args:
            package: package name

        Returns:
            None

        """
        self.shell(['pm', 'clear', package])

    def get_ip_address(self):
        """
        Perform several set of commands to obtain the IP address
            * `adb shell netcfg | grep wlan0`
            * `adb shell ifconfig`
            * `adb getprop dhcp.wlan0.ipaddress`

        Returns:
            None if no IP address has been found, otherwise return the IP address

        """
        try:
            res = self.shell('netcfg')
        except AdbShellError:
            res = ''
        matcher = re.search(r'wlan0.* ((\d+\.){3}\d+)/\d+', res)
        if matcher:
            return matcher.group(1)
        else:
            try:
                res = self.shell('ifconfig')
            except AdbShellError:
                res = ''
            matcher = re.search(r'wlan0.*?inet addr:((\d+\.){3}\d+)', res, re.DOTALL)
            if matcher:
                return matcher.group(1)
            else:
                try:
                    res = self.shell('getprop dhcp.wlan0.ipaddress')
                except AdbShellError:
                    res = ''
                matcher = IP_PATTERN.search(res)
                if matcher:
                    return matcher.group(0)
        return None

    def get_gateway_address(self):
        """
        Perform several set of commands to obtain the gateway address
            * `adb getprop dhcp.wlan0.gateway`
            * `adb shell netcfg | grep wlan0`

        Returns:
            None if no gateway address has been found, otherwise return the gateway address

        """
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
        """
        Perform `adb shell netcfg | grep wlan0` command to obtain mask length

        Returns:
            17 if mask length could not be detected, otherwise the mask length

        """
        try:
            res = self.shell('netcfg')
        except AdbShellError:
            pass
        else:
            matcher = re.search(r'wlan0.* (\d+\.){3}\d+/(\d+) ', res)
            if matcher:
                return int(matcher.group(2))
        # 获取不到网段长度就默认取17
        print('[iputils WARNING] fail to get subnet mask len. use 17 as default.')
        return 17


def cleanup_adb_forward():
    for adb in ADB._instances:
        adb._cleanup_forwards()


reg_cleanup(cleanup_adb_forward)
