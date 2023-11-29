# -*- coding: utf-8 -*-
import os
import re
import traceback
import struct
import threading
import six
import socket
from functools import wraps, partial
from airtest.core.android.constant import STFLIB
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.safesocket import SafeSocket
from airtest.utils.snippet import reg_cleanup, on_method_ready, ready_method, kill_proc
from airtest.utils.threadsafe import threadsafe_generator
from airtest.core.android.cap_methods.base_cap import BaseCap
from airtest import aircv
from airtest.core.error import ScreenError

LOGGING = get_logger(__name__)


def retry_when_socket_error(func):
    @wraps(func)
    def wrapper(inst, *args, **kwargs):
        try:
            return func(inst, *args, **kwargs)
        except socket.error:
            inst.frame_gen = None
            return func(inst, *args, **kwargs)
    return wrapper


class Minicap(BaseCap):
    """super fast android screenshot method from stf minicap.

    reference https://github.com/openstf/minicap
    """

    VERSION = 5
    RECVTIMEOUT = 3  # default value is None, but the version above 1.2.7 is changed to 3s
    CMD = "LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap"

    def __init__(self, adb, projection=None, rotation_watcher=None, display_id=None, ori_function=None):
        """
        :param adb: adb instance of android device
        :param projection: projection, default is None. If `None`, physical display size is used
        """
        super(Minicap, self).__init__(adb=adb)
        self.projection = projection
        self.display_id = display_id
        self.ori_function = ori_function or self.adb.get_display_info
        self.frame_gen = None
        self.stream_lock = threading.Lock()
        self.quirk_flag = 0
        self._stream_rotation = None
        self._update_rotation_event = threading.Event()
        if rotation_watcher:
            # Minicap needs to be reconnected when switching between landscape and portrait
            # minicap需要在横竖屏转换时，重新连接
            rotation_watcher.reg_callback(lambda x: self.update_rotation(x * 90))
        self.cleanup_func = []
        # Force cleanup on exit
        reg_cleanup(self.teardown_stream)

    @ready_method
    def install_or_upgrade(self):
        """
        Install or upgrade minicap

        Returns:
            None

        """
        if self.adb.exists_file("/data/local/tmp/minicap") \
                and self.adb.exists_file("/data/local/tmp/minicap.so"):
            try:
                output = self.adb.raw_shell("%s -v 2>&1" % self.CMD)
            except Exception as err:
                LOGGING.error(str(err))
                version = -1
            else:
                LOGGING.debug(output.strip())
                m = re.match("version:(\d)", output)
                if m:
                    version = int(m.group(1))
                else:
                    version = -1
            if version >= self.VERSION:
                LOGGING.debug('skip install minicap')
                return
            else:
                LOGGING.debug('upgrade minicap to lastest version: %s->%s' % (version, self.VERSION))
                self.uninstall()
        else:
            LOGGING.debug('install minicap')
        self.install()

    def uninstall(self):
        """
        Uninstall minicap

        Returns:
            None

        """
        try:
            self.adb.raw_shell("rm -r /data/local/tmp/minicap*")
        except Exception as e:
            # AdbError: No such file or directory
            LOGGING.warning(e)

    def install(self):
        """
        Install minicap

        Reference: https://github.com/openstf/minicap/blob/master/run.sh

        Returns:
            None

        """
        abi = self.adb.getprop("ro.product.cpu.abi")
        pre = self.adb.getprop("ro.build.version.preview_sdk")
        rel = self.adb.getprop("ro.build.version.release")
        sdk = self.adb.sdk_version

        if pre.isdigit() and int(pre) > 0:
            sdk += 1

        if sdk >= 16:
            binfile = "minicap"
        else:
            binfile = "minicap-nopie"

        device_dir = "/data/local/tmp"

        path = os.path.join(STFLIB, abi, binfile)
        self.adb.push(path, "%s/minicap" % device_dir)
        self.adb.shell("chmod 755 %s/minicap" % device_dir)

        pattern = os.path.join(STFLIB, 'minicap-shared/aosp/libs/android-%s/%s/minicap.so')
        path = pattern % (sdk, abi)
        if not os.path.isfile(path):
            path = pattern % (rel, abi)

        self.adb.push(path, "%s/minicap.so" % device_dir)
        self.adb.shell("chmod 755 %s/minicap.so" % device_dir)
        LOGGING.info("minicap installation finished")

    @on_method_ready('install_or_upgrade')
    def get_frame(self, projection=None):
        """
        Get the single frame from minicap -s, this method slower than `get_frames`
            1. shell cmd
            1. remove log info
            1. \r\r\n -> \n ...

        Args:
            projection: screenshot projection, default is None which means using self.projection

        Returns:
            jpg data

        """
        params, display_info = self._get_params(projection)
        if self.display_id:
            raw_data = self.adb.raw_shell(
                self.CMD + " -d " + str(self.display_id) + " -n 'airtest_minicap' -P %dx%d@%dx%d/%d -s" % params,
                ensure_unicode=False,
            )
        else:
            raw_data = self.adb.raw_shell(
                self.CMD + " -n 'airtest_minicap' -P %dx%d@%dx%d/%d -s" % params,
                ensure_unicode=False,
            )
        jpg_data = raw_data.split(b"for JPG encoder" + self.adb.line_breaker)[-1]
        jpg_data = jpg_data.replace(self.adb.line_breaker, b"\n")
        if jpg_data.startswith(b"\xff\xd8") and jpg_data.endswith(b"\xff\xd9"):
            return jpg_data
        else:
            raise ScreenError("invalid jpg format")

    def _get_params(self, projection=None):
        """
        Get the minicap origin parameters and count the projection

        Returns:
            physical display size (width, height), counted projection (width, height) and real display orientation

        """
        display_info = self.ori_function()
        real_width = display_info["width"]
        real_height = display_info["height"]
        real_rotation = display_info["rotation"]
        # 优先去传入的projection
        projection = projection or self.projection
        if projection:
            proj_width, proj_height = projection
        else:
            proj_width, proj_height = real_width, real_height

        if self.quirk_flag & 2 and real_rotation in (90, 270):
            params = real_height, real_width, proj_height, proj_width, 0
        else:
            params = real_width, real_height, proj_width, proj_height, real_rotation

        return (params, display_info)

    @on_method_ready('install_or_upgrade')
    def get_stream(self, lazy=True):
        """
        Get stream, it uses `adb forward`and socket communication. Use minicap ``lazy``mode (provided by gzmaruijie)
        for long connections - returns one latest frame from the server


        Args:
            lazy: True or False

        Returns:

        """
        gen = self._get_stream(lazy)

        # if quirk error, restart server and client once
        stopped = next(gen)

        if stopped:
            try:
                next(gen)
            except StopIteration:
                pass
            gen = self._get_stream(lazy)
            next(gen)

        return gen

    @threadsafe_generator
    @on_method_ready('install_or_upgrade')
    def _get_stream(self, lazy=True):
        self._cleanup_minicap()
        proc, nbsp, localport = self._setup_stream_server(lazy=lazy)
        s = SafeSocket()
        s.connect((self.adb.host, localport))
        t = s.recv(24)
        # minicap header
        global_headers = struct.unpack("<2B5I2B", t)
        LOGGING.debug(global_headers)
        # check quirk-bitflags, reference: https://github.com/openstf/minicap#quirk-bitflags
        ori, self.quirk_flag = global_headers[-2:]

        if self.quirk_flag & 2 and ori in (1, 3):
            # resetup
            LOGGING.debug("quirk_flag found, going to resetup")
            stopping = True
        else:
            stopping = False
        self.cleanup_func.append(s.close)
        self.cleanup_func.append(nbsp.kill)
        self.cleanup_func.append(partial(kill_proc, proc))
        self.cleanup_func.append(partial(self.adb.remove_forward, "tcp:%s" % localport))
        yield stopping

        while not stopping:
            if lazy:
                s.send(b"1")
            # recv frame header, count frame_size
            if self.RECVTIMEOUT is not None:
                # Some mobile phones may keep waiting for data when switching between horizontal and vertical screens,
                # and the connection is not closed, resulting in a black screen
                # Set the timeout to 3s(airtest>=1.2.7)
                header = s.recv_with_timeout(4, self.RECVTIMEOUT)
            else:
                header = s.recv(4)
            if header is None:
                LOGGING.error("minicap header is None")
                # recv timeout, if not frame updated, maybe screen locked
                stopping = yield None
            else:
                frame_size = struct.unpack("<I", header)[0]
                if self.RECVTIMEOUT is not None:
                    frame_data = s.recv_with_timeout(frame_size, self.RECVTIMEOUT)
                else:
                    frame_data = s.recv(frame_size)
                stopping = yield frame_data

        LOGGING.debug("minicap stream ends")
        # teardown stream() cannot be called directly because the connection may be rebuilt multiple times
        # while the screen is rotated, and self.frame_gen gets stuck
        self._cleanup()

    def _setup_stream_server(self, lazy=False):
        """
        Setup minicap process on device

        Args:
            lazy: parameter `-l` is used when True

        Returns:
            adb shell process, non-blocking stream reader and local port

        """
        localport, deviceport = self.adb.setup_forward("localabstract:minicap_{}".format)
        deviceport = deviceport[len("localabstract:"):]
        other_opt = "-l" if lazy else ""
        params, display_info = self._get_params()
        if self.display_id:
            proc = self.adb.start_shell(
                "%s -d %s -n '%s' -P %dx%d@%dx%d/%d %s 2>&1" %
                tuple([self.CMD, self.display_id, deviceport] + list(params) + [other_opt]),
            )
        else:
            proc = self.adb.start_shell(
                "%s -n '%s' -P %dx%d@%dx%d/%d %s 2>&1" %
                tuple([self.CMD, deviceport] + list(params) + [other_opt]),
            )
        nbsp = NonBlockingStreamReader(proc.stdout, print_output=True, name="minicap_server", auto_kill=True)
        while True:
            line = nbsp.readline(timeout=5.0)
            if line is None:
                kill_proc(proc)
                raise RuntimeError("minicap server setup timeout")
            if b"Server start" in line:
                break

        if proc.poll() is not None:
            # minicap server setup error, may be already setup by others
            # subprocess exit immediately
            kill_proc(proc)
            raise RuntimeError("minicap server quit immediately")

        self._stream_rotation = int(display_info["rotation"])
        return proc, nbsp, localport

    @retry_when_socket_error
    def get_frame_from_stream(self):
        """
        Get one frame from minicap stream

        Returns:
            frame

        """
        if self._update_rotation_event.is_set():
            LOGGING.debug("do update rotation")
            self.teardown_stream()
            self._update_rotation_event.clear()
        if self.frame_gen is None:
            self.frame_gen = self.get_stream()
        return six.next(self.frame_gen)

    def snapshot(self, ensure_orientation=True, projection=None):
        """

        Args:
            ensure_orientation: True or False whether to keep the orientation same as display
            projection: the size of the desired projection, (width, height)

        Returns:

        """
        if projection:
            # minicap模式在单张截图时，可以传入projection参数来强制指定图片大小，如手机分辨率(width, height)
            screen = self.get_frame(projection=projection)
            try:
                screen = aircv.utils.string_2_img(screen)
            except Exception:
                # may be black/locked screen or other reason, print exc for debugging
                traceback.print_exc()
                return None
            return screen
        else:
            return super(Minicap, self).snapshot()

    def update_rotation(self, rotation):
        """
        Update rotation and reset the backend stream generator

        Args:
            rotation: rotation input

        Returns:
            None

        """
        LOGGING.debug("update_rotation: %s" % rotation)
        self._update_rotation_event.set()

    def _cleanup_minicap(self):
        """
        Clean up the minicap process whose status is __skb_wait_for_more_packets or futex_wait_queue_me
        清理状态为__skb_wait_for_more_packets, futex_wait_queue_me的minicap进程

        Returns:

        """
        # 卡住的进程状态
        TASK_INTERRUPTIBLE1 = "__skb_wait_for_more_packets"
        TASK_INTERRUPTIBLE2 = "futex_wait_queue_me"

        shell_output = ""
        try:
            shell_output = self.adb.shell("ps -A| grep minicap")
        except:
            try:
                shell_output = self.adb.shell("ps| grep minicap")
            except:
                pass

        if len(shell_output) == 0:
            return
        for line in shell_output.split("\r\n"):
            if TASK_INTERRUPTIBLE1 in line or TASK_INTERRUPTIBLE2 in line:
                pid = line.split()[1]
                try:
                    self.adb.shell("kill %s" % pid)
                except:
                    pass

    def _cleanup(self):
        """
        Cleanup minicap process and stream reader

        主动将minicap建立的各个连接关闭
        与snippet.py中的CLEANUP_CALLS功能相同，但是允许主动调用，避免异常退出时有遗漏进程没清理干净

        Returns:

        """
        for func in self.cleanup_func:
            func()
        self.cleanup_func = []

    def teardown_stream(self):
        """
        End the stream

        Returns:
            None

        """
        # clean up established connections
        self._cleanup()
        if not self.frame_gen:
            return
        try:
            self.frame_gen.send(1)
        except (TypeError, StopIteration):
            # TypeError: can't send non-None value to a just-started generator
            pass
        else:
            LOGGING.warn("%s tear down failed" % self.frame_gen)
        self.frame_gen = None
