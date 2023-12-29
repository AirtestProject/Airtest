# -*- coding: utf-8 -*-
import os
import re
import sys
import time
import random
import platform
import psutil
import warnings
import subprocess
import threading
from copy import copy
from six import PY3, text_type, binary_type
from six.moves import reduce

from airtest.core.android.constant import (DEFAULT_ADB_PATH, IP_PATTERN,
                                           SDK_VERISON_ANDROID7)
from airtest.core.error import (AdbError, AdbShellError, AirtestError,
                                DeviceConnectionError)
from airtest.utils.compat import decode_path, raisefrom, proc_communicate_timeout, SUBPROCESS_FLAG
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.retry import retries
from airtest.utils.apkparser import APK
from airtest.utils.snippet import get_std_encoding, reg_cleanup, split_cmd, make_file_executable

LOGGING = get_logger(__name__)


class ADB(object):
    """adb client object class"""

    _instances = []
    status_device = "device"
    status_offline = "offline"
    SHELL_ENCODING = "utf-8"

    def __init__(self, serialno=None, adb_path=None, server_addr=None, display_id=None, input_event=None):
        self.serialno = serialno
        self.adb_path = adb_path or self.get_adb_path()
        self.display_id = display_id
        self.input_event = input_event
        self._set_cmd_options(server_addr)
        self.connect()
        self._sdk_version = None
        self._line_breaker = None
        self._display_info = {}
        self._display_info_lock = threading.Lock()
        self._forward_local_using = []
        self.__class__._instances.append(self)

    @staticmethod
    def get_adb_path():
        """
        Returns the path to the adb executable.

        Checks if adb process is running, returns the running process path.

        If adb process is not running, checks if ANDROID_HOME environment variable is set.
        Constructs the adb path using ANDROID_HOME and returns it if set.

        If adb process is not running and ANDROID_HOME is not set, uses built-in adb path.

        Returns:
            str: The path to the adb executable.
        """
        if platform.system() == "Windows":
            ADB_NAME = "adb.exe"
        else:
            ADB_NAME = "adb"

        # Check if adb process is already running
        try:
            for process in psutil.process_iter(['name', 'exe']):
                if process.info['name'] == ADB_NAME and process.info['exe'] and os.path.exists(process.info['exe']):
                    return process.info['exe']
        except:
            # maybe OSError
            pass

        # Check if ANDROID_HOME environment variable exists
        android_home = os.environ.get('ANDROID_HOME')
        if android_home:
            adb_path = os.path.join(android_home, 'platform-tools', ADB_NAME)
            if os.path.exists(adb_path):
                return adb_path

        # Use airtest builtin adb path
        builtin_adb_path = ADB.builtin_adb_path()
        return builtin_adb_path

    @staticmethod
    def builtin_adb_path():
        """
        Return built-in adb executable path

        Returns:
            adb executable path

        """
        system = platform.system()
        machine = platform.machine()
        adb_path = DEFAULT_ADB_PATH.get('{}-{}'.format(system, machine))
        if not adb_path:
            adb_path = DEFAULT_ADB_PATH.get(system)
        if not adb_path:
            raise RuntimeError("No adb executable supports this platform({}-{}).".format(system, machine))

        if system != "Windows":
            # chmod +x adb
            make_file_executable(adb_path)
        return adb_path

    def _set_cmd_options(self, server_addr=None):
        """
        Set communication parameters (host and port) between adb server and adb client

        Args:
            server_addr: adb server address, default is ["127.0.0.1", 5037]

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
            stderr=subprocess.PIPE,
            creationflags=SUBPROCESS_FLAG
        )
        return proc

    def cmd(self, cmds, device=True, ensure_unicode=True, timeout=None):
        """
        Run the adb command(s) in subprocess and return the standard output

        Args:
            cmds: command(s) to be run
            device: if True, the device serial number must be specified by -s serialno argument
            ensure_unicode: encode/decode unicode of standard outputs (stdout, stderr)
            timeout: timeout in seconds

        Raises:
            DeviceConnectionError: if any error occurs when connecting the device
            AdbError: if any other adb error occurs

        Returns:
            command(s) standard output (stdout)

        """
        proc = self.start_cmd(cmds, device)
        if timeout:
            stdout, stderr = proc_communicate_timeout(proc, timeout)
        else:
            stdout, stderr = proc.communicate()

        if ensure_unicode:
            stdout = stdout.decode(get_std_encoding(sys.stdout))
            stderr = stderr.decode(get_std_encoding(sys.stderr))

        if proc.returncode > 0:
            # adb connection error
            pattern = DeviceConnectionError.DEVICE_CONNECTION_ERROR
            if isinstance(stderr, binary_type):
                pattern = pattern.encode("utf-8")
            if re.search(pattern, stderr):
                raise DeviceConnectionError(stderr)
            else:
                raise AdbError(stdout, stderr)
        return stdout

    def close_proc_pipe(self, proc):
        """close stdin/stdout/stderr of subprocess.Popen."""

        def close_pipe(pipe):
            if pipe:
                pipe.close()

        close_pipe(proc.stdin)
        close_pipe(proc.stdout)
        close_pipe(proc.stderr)

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
        try:
            self.cmd("wait-for-device", timeout=timeout)
        except RuntimeError as e:
            raisefrom(DeviceConnectionError, "device not ready", e)

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
            return text_type(repr(out))

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
        if self.sdk_version < SDK_VERISON_ANDROID7:
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
            if "\r\r\n" in prop:
                # Some mobile phones will output multiple lines of extra log
                prop = prop.split("\r\r\n")
                if len(prop) > 1:
                    prop = prop[-2]
                else:
                    prop = prop[-1]
            else:
                prop = prop.strip("\r\n")
        return prop

    @property
    @retries(max_tries=3)
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

        Note:
            If there is a space (or special symbol) in the file name, it will be forced to add escape characters,
            and the new file name will be added with quotation marks and returned as the return value

            注意：文件名中如果带有空格（或特殊符号），将会被强制增加转义符，并将新的文件名添加引号，作为返回值返回

        Args:
            local: local file to be copied to the device
            remote: destination on the device where the file will be copied

        Returns:
            The file path saved in the phone may be enclosed in quotation marks, eg. '"test\ file.txt"'

        Examples:

            >>> adb = device().adb
            >>> adb.push("test.txt", "/data/local/tmp")

            >>> new_name = adb.push("test space.txt", "/data/local/tmp")  # test the space in file name
            >>> print(new_name)
            "/data/local/tmp/test\ space.txt"
            >>> adb.shell("rm " + new_name)

        """
        local = decode_path(local)  # py2
        if os.path.isfile(local) and os.path.splitext(local)[-1] != os.path.splitext(remote)[-1]:
            # If remote is a folder, add the filename and escape
            filename = os.path.basename(local)
            # Add escape characters for spaces, parentheses, etc. in filenames
            filename = re.sub(r"[ \(\)\&]", lambda m: "\\" + m.group(0), filename)
            remote = '%s/%s' % (remote, filename)
        self.cmd(["push", local, remote], ensure_unicode=False)
        return '\"%s\"' % remote

    def pull(self, remote, local):
        """
        Perform `adb pull` command

        Args:
            remote: remote file to be downloaded from the device
            local: local destination where the file will be downloaded from the device

        Note:
            If <=PY3, the path in Windows cannot be the root directory, and cannot contain symbols such as /g in the path
            注意：如果低于PY3,windows中路径不能为根目录，并且不能包含/g等符号在路径里

        Returns:
            None
        """
        local = decode_path(local)  # py2
        if PY3:
            # If python3, use Path to force / convert to \
            from pathlib import Path
            local = Path(local).as_posix()
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
    def setup_forward(self, device_port, no_rebind=True):
        """
        Generate pseudo random local port and check if the port is available.

        Args:
            device_port: it can be string or the value of the `function(localport)`,
                         e.g. `"tcp:5001"` or `"localabstract:{}".format`
            no_rebind: adb forward --no-rebind option

        Returns:
            local port and device port

        """
        localport = self.get_available_forward_local()
        if callable(device_port):
            device_port = device_port(localport)
        self.forward("tcp:%s" % localport, device_port, no_rebind=no_rebind)
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
        try:
            self.cmd(cmds)
        except AdbError as e:
            # ignore if already removed or disconnected
            if "not found" in (repr(e.stdout) + repr(e.stderr)):
                pass
        except DeviceConnectionError:
            pass
        # unregister for cleanup
        if local in self._forward_local_using:
            self._forward_local_using.remove(local)

    def install_app(self, filepath, replace=False, install_options=None):
        """
        Perform `adb install` command

        Args:
            filepath: full path to file to be installed on the device
            replace: force to replace existing application, default is False

                e.g.["-t",  # allow test packages
                    "-l",  # forward lock application,
                    "-s",  # install application on sdcard,
                    "-d",  # allow version code downgrade (debuggable packages only)
                    "-g",  # grant all runtime permissions
                ]

        Returns:
            command output

        """
        if isinstance(filepath, str):
            filepath = decode_path(filepath)

        if not os.path.isfile(filepath):
            raise RuntimeError("file: %s does not exists" % (repr(filepath)))

        if not install_options or type(install_options) != list:
            install_options = []
        if replace:
            install_options.append("-r")
        cmds = ["install", ] + install_options + [filepath, ]
        try:
            out = self.cmd(cmds)
        except AdbError as e:
            out = repr(e.stderr) + repr(e.stdout)
            # If the signatures are inconsistent, uninstall the old version first
            if "INSTALL_FAILED_UPDATE_INCOMPATIBLE" in out and replace:
                try:
                    package_name = re.search(r"package (.*?) .*", out).group(1)
                except:
                    # get package name
                    package_name = APK(filepath).get_package()
                self.uninstall_app(package_name)
                out = self.cmd(cmds)
            else:
                raise

        if re.search(r"Failure \[.*?\]", out):
            raise AdbShellError("Installation Failure", repr(out))

        return out

    def install_multiple_app(self, filepath, replace=False, install_options=None):
        """
            Perform `adb install-multiple` command

            Args:
                filepath: full path to file to be installed on the device
                replace: force to replace existing application, default is False
                install_options:  list of options
                    e.g.["-t",  # allow test packages
                        "-l",  # forward lock application,
                        "-s",  # install application on sdcard,
                        "-d",  # allow version code downgrade (debuggable packages only)
                        "-g",  # grant all runtime permissions
                        "-p",  # partial application install (install-multiple only)
                    ]

            Returns:
                command output
        """
        if isinstance(filepath, str):
            filepath = decode_path(filepath)

        if not os.path.isfile(filepath):
            raise RuntimeError("file: %s does not exists" % (repr(filepath)))

        if not install_options or type(install_options) != list:
            install_options = []
        if replace:
            install_options.append("-r")
        cmds = ["install-multiple", ] + install_options + [filepath, ]

        try:
            out = self.cmd(cmds)
        except AdbError as err:
            if "Failed to finalize session".lower() in err.stderr.lower():
                return "Success"
            else:
                return self.install_app(filepath, replace)

        if re.search(r"Failure \[.*?\]", out):
            raise AdbShellError("Installation Failure", repr(out))

        return out

    def pm_install(self, filepath, replace=False, install_options=None):
        """
        Perform `adb push` and `adb install` commands

        Note:
            This is more reliable and recommended way of installing `.apk` files

        Args:
            filepath: full path to file to be installed on the device
            replace: force to replace existing application, default is False
            install_options:  list of options
                e.g.["-t",  # allow test packages
                    "-l",  # forward lock application,
                    "-s",  # install application on sdcard,
                    "-d",  # allow version code downgrade (debuggable packages only)
                    "-g",  # grant all runtime permissions
                ]

        Returns:
            None

        """
        if isinstance(filepath, str):
            filepath = decode_path(filepath)
        if not os.path.isfile(filepath):
            raise RuntimeError("file: %s does not exists" % (repr(filepath)))

        if not install_options or type(install_options) != list:
            install_options = []
        if replace:
            install_options.append("-r")

        filename = os.path.basename(filepath)
        device_dir = "/data/local/tmp"

        try:
            # if the apk file path contains spaces, the path must be escaped
            device_path = self.push(filepath, device_dir)
        except AdbError as err:
            # Error: no space left on device
            raise err

        try:
            cmds = ["pm", "install", ] + install_options + [device_path]
            self.shell(cmds)
        except AdbError as e:
            out = repr(e.stderr) + repr(e.stdout)
            # If the signatures are inconsistent, uninstall the old version first
            if re.search(r"INSTALL_FAILED_UPDATE_INCOMPATIBLE", out):
                try:
                    package_name = re.search(r"package (.*?) .*", out).group(1)
                except:
                    # get package name
                    package_name = APK(filepath).get_package()
                self.uninstall_app(package_name)
                out = self.shell(cmds)
            else:
                raise
        finally:
            # delete apk file
            self.cmd(["shell", "rm", device_path], timeout=30)

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
        if self.display_id:
            raw = self.cmd('shell screencap -d {0} -p'.format(self.display_id), ensure_unicode=False)
        else:
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
            return not ("No such file or directory" in out)

    def file_size(self, filepath):
        """
        Get the file size

        Args:
            filepath: path to the file

        Returns:
            The file size

        Raises:
            AdbShellError if no such file
        """
        out = self.shell(["ls", "-l", filepath])
        try:
            file_size = int(out.split()[4])
        except ValueError:
            # 安卓6.0.1系统得到的结果是[3]为文件大小
            file_size = int(out.split()[3])
        return file_size

    def _cleanup_forwards(self):
        """
        Remove the local forward ports

        Returns:
            None
        """
        # remove forward成功后，会改变self._forward_local_using的内容，因此需要copy一遍
        # After remove_forward() is successful, self._forward_local_using will be changed, so it needs to be copied
        forward_local_list = copy(self._forward_local_using)
        for local in forward_local_list:
            try:
                self.remove_forward(local)
            except DeviceConnectionError:
                # if device is offline, ignore
                pass

    @property
    def line_breaker(self):
        """
        Set carriage return and line break property for various platforms and SDK versions

        Returns:
            carriage return and line break string

        """
        if not self._line_breaker:
            if self.sdk_version >= SDK_VERISON_ANDROID7:
                line_breaker = os.linesep
            else:
                line_breaker = '\r' + os.linesep
            self._line_breaker = line_breaker.encode("ascii")
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
            e.g {
                'width': 1440,
                'height': 2960,
                'density': 4.0,
                'orientation': 3,
                'rotation': 270,
                'max_x': 4095,
                'max_y': 4095
            }

        """
        display_info = self.getPhysicalDisplayInfo()
        orientation = self.getDisplayOrientation()
        max_x, max_y = self.getMaxXY()
        display_info.update({
            "orientation": orientation,
            "rotation": orientation * 90,
            "max_x": max_x,
            "max_y": max_y,
        })
        return display_info

    def getMaxXY(self):
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

    def getRestrictedScreen(self):
        """
        Get value for mRestrictedScreen (without black border / virtual keyboard)`

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

    def getPhysicalDisplayInfo(self):
        """
        Get value for display dimension and density from `mPhysicalDisplayInfo` value obtained from `dumpsys` command.

        Returns:
            physical display info for dimension and density

        """
        # use adb shell wm size
        displayInfo = {}
        try:
            wm_size = re.search(r'(?P<width>\d+)x(?P<height>\d+)\s*$', self.cmd('shell wm size', timeout=5))
        except (AdbError, RuntimeError) as e:
            LOGGING.error(e)
        else:
            if wm_size:
                displayInfo = dict((k, int(v)) for k, v in wm_size.groupdict().items())
                displayInfo['density'] = self._getDisplayDensity(strip=True)
                return displayInfo

        phyDispRE = re.compile('.*PhysicalDisplayInfo{(?P<width>\d+) x (?P<height>\d+), .*, density (?P<density>[\d.]+).*')
        out = self.raw_shell('dumpsys display')
        m = phyDispRE.search(out)
        if m:
            for prop in ['width', 'height']:
                displayInfo[prop] = int(m.group(prop))
            for prop in ['density']:
                # In mPhysicalDisplayInfo density is already a factor, no need to calculate
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
            for prop in ['width', 'height']:
                displayInfo[prop] = int(m.group(prop))
            for prop in ['density']:
                d = self._getDisplayDensity(strip=True)
                if d:
                    displayInfo[prop] = d
                else:
                    # No available density information
                    displayInfo[prop] = -1.0
            return displayInfo

        # gets C{mPhysicalDisplayInfo} values from dumpsys. This is a method to obtain display dimensions and density
        phyDispRE = re.compile('Physical size: (?P<width>\d+)x(?P<height>\d+).*Physical density: (?P<density>\d+)', re.S)
        m = phyDispRE.search(self.cmd('shell wm size; wm density', timeout=3))
        if m:
            for prop in ['width', 'height']:
                displayInfo[prop] = int(m.group(prop))
            for prop in ['density']:
                displayInfo[prop] = float(m.group(prop))
            return displayInfo

        if not displayInfo:
            raise DeviceConnectionError("Getting device screen information timed out")

    def _getDisplayDensity(self, strip=True):
        """
        Get display density

        Args:
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

        displayFramesRE = re.compile(r"DisplayFrames.*r=(\d+)")
        output = self.shell('dumpsys window displays')
        m = displayFramesRE.search(output)
        if m:
            return int(m.group(1))

        # We couldn't obtain the orientation
        warnings.warn("Could not obtain the orientation, return 0")
        return 0

    def update_cur_display(self, display_info):
        """
        Some phones support resolution modification, try to get the modified resolution from dumpsys
        adb shell dumpsys window displays | find "cur="

        本方法虽然可以更好地获取到部分修改过分辨率的手机信息
        但是会因为cur=(\d+)x(\d+)的数值在不同设备上width和height的顺序可能不同，导致横竖屏识别出现问题
        airtest不再使用本方法作为通用的屏幕尺寸获取方法，但依然可用于部分设备获取当前被修改过的分辨率

        Examples:

            >>> # 部分三星和华为设备，若分辨率没有指定为最高，可能会导致点击偏移，可以用这个方式强制修改：
            >>> # For some Samsung and Huawei devices, if the resolution is not specified as the highest,
            >>> # it may cause click offset, which can be modified in this way:
            >>> dev = device()
            >>> info = dev.display_info
            >>> info2 = dev.adb.update_cur_display(info)
            >>> dev.display_info.update(info2)

        Args:
            display_info: the return of self.getPhysicalDisplayInfo()

        Returns:
            display_info

        """
        # adb shell dumpsys window displays | find "init="
        # 上面的命令行在dumpsys window里查找init=widthxheight，得到的结果是物理分辨率，且部分型号手机不止一个结果
        # 如果改为读取 cur=widthxheight 的数据，得到的是修改过分辨率手机的结果（例如三星S8）
        actual = self.shell("dumpsys window displays")
        arr = re.findall(r'cur=(\d+)x(\d+)', actual)
        if len(arr) > 0:
            # 强制设定宽度width为更小的数字、height为更大的数字，避免因为各手机厂商返回结果的顺序不同导致问题
            # Set the width to a smaller number and the height to a larger number
            width, height = min(list(map(int, arr[0]))), max(list(map(int, arr[0])))
            display_info['physical_width'] = display_info['width']
            display_info['physical_height'] = display_info['height']
            display_info['width'], display_info['height'] = width, height
        return display_info

    def get_top_activity(self):
        """
        Perform `adb shell dumpsys activity top` command search for the top activity

        Raises:
            AirtestError: if top activity cannot be obtained

        Returns:
            top activity as a tuple: (package_name, activity_name, pid)

        """
        dat = self.shell('dumpsys activity top')
        activityRE = re.compile(r'\s*ACTIVITY ([A-Za-z0-9_.$]+)/([A-Za-z0-9_.$]+) \w+ pid=(\d+)')
        # in Android8.0 or higher, the result may be more than one
        m = activityRE.findall(dat)
        if m:
            return m[-1]
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
            return m.group(1) == 'true'
        else:
            # MIUI11
            screenOnRE = re.compile('screenState=(SCREEN_STATE_ON|SCREEN_STATE_OFF)')
            m = screenOnRE.search(self.shell('dumpsys window policy'))
            if m:
                return m.group(1) == 'SCREEN_STATE_ON'
        raise AirtestError("Couldn't determine screen ON state")

    @retries(max_tries=3)
    def is_locked(self):
        """
        Perform `adb shell dumpsys window policy` command and search for information if screen is locked or not

        Raises:
            AirtestError: if lock screen can't be detected

        Returns:
            True or False whether the screen is locked or not

        """
        lockScreenRE = re.compile('(?:mShowingLockscreen|isStatusBarKeyguard|showing)=(true|false)')
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
        return output.split("package:")[1].strip()

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
        output = self.shell(['dumpsys', 'package', package])
        pattern = r'Package\s+\[' + str(package) + '\]'
        match = re.search(pattern, output)
        if match is None:
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
            try:
                ret = self.shell(['monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1'])
            except AdbShellError as e:
                raise AirtestError("Starting App: %s Failed! No activities found to run." % package)
            if "No activities found to run" in ret:
                raise AirtestError("Starting App: %s Failed! No activities found to run." % package)
        else:
            self.shell(['am', 'start', '-n', '%s/%s.%s' % (package, package, activity)])

    def start_app_timing(self, package, activity):
        """
        Start the application and activity, and measure time

        Args:
            package: package name
            activity: activity name

        Returns:
            app launch time

        """
        out = self.shell(['am', 'start', '-S', '-W', '%s/%s' % (package, activity),
                          '-c', 'android.intent.category.LAUNCHER', '-a', 'android.intent.action.MAIN'])
        if not re.search(r"Status:\s*ok", out):
            raise AirtestError("Starting App: %s/%s Failed!" % (package, activity))

        # matcher = re.search(r"TotalTime:\s*(\d+)", out)
        matcher = re.search(r"TotalTime:\s*(\d+)", out)
        if matcher:
            return int(matcher.group(1))
        else:
            return 0

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

    def text(self, content):
        """
        Use adb shell input for text input

        Args:
            content: text to input

        Returns:
            None

        Examples:
            >>> dev = connect_device("Android:///")
            >>> dev.text("Hello World")
            >>> dev.text("test123")
        """
        if content.isalpha():
            self.shell(["input", "text", content])
        else:
            # If it contains letters and numbers, input with `adb shell input text` may result in the wrong order
            for i in content:
                if i == " ":
                    self.keyevent("KEYCODE_SPACE")
                else:
                    self.shell(["input", "text", i])

    def get_ip_address(self):
        """
        Perform several set of commands to obtain the IP address.

            * `adb shell netcfg | grep wlan0`
            * `adb shell ifconfig`
            * `adb getprop dhcp.wlan0.ipaddress`

        Returns:
            None if no IP address has been found, otherwise return the IP address

        """

        def get_ip_address_from_interface(interface):
            """Get device ip from target network interface."""
            # android >= 6.0: ip -f inet addr show {interface}
            try:
                res = self.shell('ip -f inet addr show {}'.format(interface))
            except AdbShellError:
                res = ''
            matcher = re.search(r"inet (\d+\.){3}\d+", res)
            if matcher:
                return matcher.group().split(" ")[-1]

            # android >= 6.0 backup method: ifconfig
            try:
                res = self.shell('ifconfig')
            except AdbShellError:
                res = ''
            matcher = re.search(interface + r'.*?inet addr:((\d+\.){3}\d+)', res, re.DOTALL)
            if matcher:
                return matcher.group(1)

            # android <= 6.0: netcfg
            try:
                res = self.shell('netcfg')
            except AdbShellError:
                res = ''
            matcher = re.search(interface + r'.* ((\d+\.){3}\d+)/\d+', res)
            if matcher:
                return matcher.group(1)

            # android <= 6.0 backup method: getprop dhcp.{}.ipaddress
            try:
                res = self.shell('getprop dhcp.{}.ipaddress'.format(interface))
            except AdbShellError:
                res = ''
            matcher = IP_PATTERN.search(res)
            if matcher:
                return matcher.group(0)

            # sorry, no more methods...
            return None

        interfaces = ('eth0', 'eth1', 'wlan0')
        for i in interfaces:
            ip = get_ip_address_from_interface(i)
            if ip and not ip.startswith('127.') and not ip.startswith('169.'):
                return ip

        return None

    def get_gateway_address(self):
        """
        Perform several set of commands to obtain the gateway address.
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

    def get_memory(self):
        res = self.shell("dumpsys meminfo")
        pat = re.compile(r".*Total RAM:\s+(\S+)\s+", re.DOTALL)
        _str = pat.match(res).group(1)
        if ',' in _str:
            _list = _str.split(',')
            _num = int(_list[0])
            _num = round(_num + (float(_list[1]) / 1000.0))
        else:
            _num = round(float(_str) / 1000.0 / 1000.0)
        res = str(_num) + 'G'
        return res

    def get_storage(self):
        res = self.shell("df /data")
        pat = re.compile(r".*\/data\s+(\S+)", re.DOTALL)
        if pat.match(res):
            _str = pat.match(res).group(1)
        else:
            pat = re.compile(r".*\s+(\S+)\s+\S+\s+\S+\s+\S+\s+\/data", re.DOTALL)
            _str = pat.match(res).group(1)
        if 'G' in _str:
            _num = round(float(_str[:-1]))
        elif 'M' in _str:
            _num = round(float(_str[:-1]) / 1000.0)
        else:
            _num = round(float(_str) / 1000.0 / 1000.0)
        if _num > 64:
            res = '128G'
        elif _num > 32:
            res = '64G'
        elif _num > 16:
            res = '32G'
        elif _num > 8:
            res = '16G'
        else:
            res = '8G'
        return res

    def get_cpuinfo(self):
        res = self.shell("cat /proc/cpuinfo").strip()
        cpuNum = res.count("processor")
        pat = re.compile(r'Hardware\s+:\s+(\w+.*)')
        m = pat.search(res)
        if not m:
            pat = re.compile(r'Processor\s+:\s+(\w+.*)')
            m = pat.match(res)
        cpuName = m.group(1).replace('\r', '')
        return dict(cpuNum=cpuNum, cpuName=cpuName)

    def get_cpufreq(self):
        res = self.shell("cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
        num = round(float(res) / 1000 / 1000, 1)
        res = str(num) + 'GHz'
        return res.strip()

    def get_cpuabi(self):
        res = self.shell("getprop ro.product.cpu.abi")
        return res.strip()

    def get_gpu(self):
        res = self.shell("dumpsys SurfaceFlinger")
        pat = re.compile(r'GLES:\s+(.*)')
        m = pat.search(res)
        if not m:
            return None
        _list = m.group(1).split(',')
        gpuModel = ""
        opengl = ""
        if len(_list) > 0:
            gpuModel = _list[1].strip()
        if len(_list) > 1:
            m2 = re.search(r'(\S+\s+\S+\s+\S+).*', _list[2])
            if m2:
                opengl = m2.group(1)
        return dict(gpuModel=gpuModel, opengl=opengl)

    def get_model(self):
        return self.getprop("ro.product.model")

    def get_manufacturer(self):
        return self.getprop("ro.product.manufacturer")

    def get_device_info(self):
        """
        Get android device information, including: memory/storage/display/cpu/gpu/model/manufacturer...

        Returns:
            Dict of info

        """
        handlers = {
            "platform": "Android",
            "serialno": self.serialno,
            "memory": self.get_memory,
            "storage": self.get_storage,
            "display": self.getPhysicalDisplayInfo,
            "cpuinfo": self.get_cpuinfo,
            "cpufreq": self.get_cpufreq,
            "cpuabi": self.get_cpuabi,
            "sdkversion": self.sdk_version,
            "gpu": self.get_gpu,
            "model": self.get_model,
            "manufacturer": self.get_manufacturer,
            # "battery": getBatteryCapacity
        }
        ret = {}
        for k, v in handlers.items():
            if callable(v):
                try:
                    value = v()
                except Exception:
                    value = None
                ret[k] = value
            else:
                ret[k] = v
        return ret

    def get_display_of_all_screen(self, info, package=None):
        """
        Perform `adb shell dumpsys window windows` commands to get window display of application.

        Args:
            info: device screen properties
            package: package name, default to the package of top activity

        Returns:
            None if adb command failed to run, otherwise return device screen properties(portrait mode)
            eg. (offset_x, offset_y, screen_width, screen_height)

        """
        output = self.shell("dumpsys window windows")
        windows = output.split("Window #")
        offsetx, offsety, width, height = 0, 0, info['width'], info['height']
        package = self._search_for_current_package(output) if package is None else package
        if package:
            for w in windows:
                if "package=%s" % package in w:
                    arr = re.findall(r'Frames: containing=\[(\d+\.?\d*),(\d+\.?\d*)]\[(\d+\.?\d*),(\d+\.?\d*)]', w)
                    if len(arr) >= 1 and len(arr[0]) == 4:
                        offsetx, offsety, width, height = float(arr[0][0]), float(arr[0][1]), float(arr[0][2]), float(arr[0][3])
                        if info["orientation"] in [1, 3]:
                            offsetx, offsety, width, height = offsety, offsetx, height, width
                        width, height = width - offsetx, height - offsety
        return {
            "offset_x": offsetx,
            "offset_y": offsety,
            "offset_width": width,
            "offset_height": height,
        }

    def _search_for_current_package(self, ret):
        """
        Search for current app package name from the output of command "adb shell dumpsys window windows"

        Returns:
            package name if exists else ""
        """
        try:
            packageRE = re.compile('\s*mCurrentFocus=Window{.* ([A-Za-z0-9_.]+)/[A-Za-z0-9_.]+}')
            m = packageRE.findall(ret)
            if m:
                return m[-1]
            else:
                return self.get_top_activity()[0]
        except Exception as e:
            print("[Error] Cannot get current top activity")
        return ""


def cleanup_adb_forward():
    for adb in ADB._instances:
        adb._cleanup_forwards()


reg_cleanup(cleanup_adb_forward)
