# -*- coding: utf-8 -*-
import subprocess
import threading
import platform
import random
import time
import sys
import os
import re
from airtest.core.error import MoaError, AdbError, AdbShellError
from airtest.core.utils import NonBlockingStreamReader, reg_cleanup, get_adb_path, retries, split_cmd, get_logger, get_std_encoding
from airtest.core.android.constant import DEFAULT_ADB_SERVER, ADB_SHELL_ENCODING, SDK_VERISON_NEW
LOGGING = get_logger('android')


class ADB(object):
    """adb client for one serialno"""

    _forward_local = 11111

    status_device = "device"
    status_offline = "offline"

    def __init__(self, serialno=None, adb_path=None, server_addr=None):
        self.adb_path = adb_path or get_adb_path()
        self.adb_server_addr = server_addr or self.default_server()
        self.set_serialno(serialno)
        self._sdk_version = None
        self._line_breaker = None
        self._forward_local_using = []
        reg_cleanup(self._cleanup_forwards)

    @staticmethod
    def default_server():
        """get default adb server"""
        host = DEFAULT_ADB_SERVER[0]
        port = os.environ.get("ANDROID_ADB_SERVER_PORT", DEFAULT_ADB_SERVER[1])
        return (host, port)

    def set_serialno(self, serialno):
        """set serialno after init"""
        self.serialno = serialno
        self.connect()

    def start_server(self):
        """adb start-server, cannot assign any -H -P -s"""
        if self.adb_server_addr[0] not in ("localhost", "127.0.0.1"):
            raise RuntimeError("cannot start-server on other host")
        return subprocess.check_call([self.adb_path, "start-server"])

    def start_cmd(self, cmds, device=True):
        """
        start a subprocess to run adb cmd
        device: specify -s serialno if True
        """
        cmds = split_cmd(cmds)
        if cmds[0] == "start-server":
            raise RuntimeError("please use self.start_server instead")

        host, port = self.adb_server_addr
        prefix = [self.adb_path, '-H', host, '-P', str(port)]
        if device:
            if not self.serialno:
                raise RuntimeError("please set_serialno first")
            prefix += ['-s', self.serialno]
        cmds = prefix + cmds
        cmds = [c.encode(get_std_encoding(sys.stdin)) for c in cmds]

        LOGGING.debug(" ".join(cmds))

        proc = subprocess.Popen(
            cmds,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return proc

    def cmd(self, cmds, device=True, not_decode=False):
        """
        get adb cmd output
        device: specify -s serialno if True
        """
        proc = self.start_cmd(cmds, device)
        stdout, stderr = proc.communicate()

        if not_decode is False:
            stdout = stdout.decode(get_std_encoding(sys.stdout))
            stderr = stderr.decode(get_std_encoding(sys.stderr))

        if proc.returncode > 0:
            raise AdbError(stdout, stderr)
        return stdout

    def version(self):
        """adb version, 1.0.36 for windows, 1.0.32 for linux/mac"""
        return self.cmd("version", device=False).strip()

    def devices(self, state=None):
        """adb devices"""
        patten = re.compile(r'^[\w\d.:-]+\t[\w]+$')
        device_list = []
        self.start_server()
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
        if timeout, raise MoaError
        """
        proc = self.start_cmd("wait-for-device")
        timer = threading.Timer(timeout, proc.kill)
        timer.start()
        ret = proc.wait()
        if ret == 0:
            timer.cancel()
        else:
            raise MoaError("device not ready")

    def raw_shell(self, cmds, not_wait=False):
        cmds = ['shell'] + split_cmd(cmds)
        if not_wait:
            return self.start_cmd(cmds)
        out = self.cmd(cmds, not_decode=True)
        return out.decode(ADB_SHELL_ENCODING)

    def shell(self, cmd, not_wait=False):
        """
        adb shell
        not_wait:
            return subprocess if True
            return output if False
        """
        if not_wait is True:
            return self.raw_shell(cmd, not_wait)
        if self.sdk_version < SDK_VERISON_NEW:
            # for sdk_version < 25, adb shell do not raise error
            # https://stackoverflow.com/questions/9379400/adb-error-codes
            cmd = split_cmd(cmd) + [";", "echo", "$?"]
            out = self.raw_shell(cmd).rstrip()
            try:
                # 返回值解析错误
                returncode = int(out[-1])
            except ValueError:
                returncode = 0
                stdout = out
            else:
                stdout = out[:-1]
            if returncode > 0:
                raise AdbShellError("", stdout)
            return stdout
        else:
            try:
                out = self.raw_shell(cmd)
            except AdbError as err:
                # adb connection error
                if re.match('error: device \'\w+\' not found', err.stdout.rstrip()):
                    raise
                else:
                    raise AdbShellError(err.stdout, err.stderr)
            else:
                return out

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
    def _get_forward_local(cls):
        port = cls._forward_local
        cls._forward_local += random.randint(1, 100)
        return port

    def get_available_forward_local(self):
        """
        1. do not repeat in different process, by check forward list(latency exists when setting up)
        2. do not repeat in one process, by cls._forward_local
        """
        forwards = self.get_forwards()
        localports = [i[1] for i in forwards]
        times = 100
        for i in range(times):
            port = self._get_forward_local()
            if "tcp:%s" % port not in localports:
                return port
        raise RuntimeError("No available adb forward local port for %s times" % (times))

    @retries(3)
    def setup_forward(self, device_port):
        localport = self.get_available_forward_local()
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

    def install(self, filepath, overinstall=False):
        """adb install, if overinstall then adb install -r xxx"""
        if not os.path.isfile(filepath):
            raise RuntimeError("%s is not valid file" % filepath)

        filename = os.path.basename(filepath)
        device_dir = "/data/local/tmp"
        # 如果apk名称包含空格，需要用引号括起来
        device_path = '\"%s/%s\"' % (device_dir, filename)

        out = self.cmd(["push", filepath, device_dir])
        print(out)

        if not overinstall:
            self.shell(['pm', 'install', device_path])
        else:
            self.shell(['pm', 'install', '-r', device_path])

    def uninstall(self, package):
        """adb uninstall"""
        return self.cmd(['uninstall', package])

    def snapshot(self):
        """take a screenshot"""
        raw = self.cmd('shell screencap -p', not_decode=True)
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
            raise MoaError('swipe: API <= 15 not supported (version=%d)' % version)
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
