# -*- coding: utf-8 -*-
import subprocess
import time
import sys
import random
import shutil
import platform
import warnings
import threading
import wda
from copy import copy
from functools import partial
from airtest.core.error import AirtestError, LocalDeviceError
from airtest.utils.snippet import reg_cleanup, make_file_executable, get_std_encoding, kill_proc
from airtest.utils.logger import get_logger
from airtest.utils.retry import retries
from airtest.utils.compat import SUBPROCESS_FLAG
from airtest.core.ios.constant import DEFAULT_IPROXY_PATH
from airtest.core.ios.relay import ThreadedTCPServer, TCPRelay

LOGGING = get_logger(__name__)


class InstructHelper(object):
    """
    ForwardHelper class
    or help run other Instruction
    """

    def __init__(self, uuid=None):
        self.subprocessHandle = []
        # uuid不是ios手机序列号，而是wda.info['uuid']字段
        self.uuid = uuid
        # 下面_udid这个是真正的手机序列号，检测到是USB设备，才会记录这个字段
        self._udid = None
        self._device = None
        # 记录曾经使用过的端口号和关闭端口用的方法，方便后续释放端口, _port_using_func[port] = kill_func
        self._port_using_func = {}
        reg_cleanup(self.tear_down)

    @staticmethod
    def builtin_iproxy_path():
        # Port forwarding for iOS:
        # 1. Windows/Mac: iproxy.exe/iproxy -u uid port1 port2
        # 2. Ubuntu linux: apt-get install libusbmuxd-tools; iproxy port1 port2
        # 3. Use python (low efficiency): python relay.py -t 5100:5100
        if shutil.which("iproxy"):
            return shutil.which("iproxy")
        system = platform.system()
        iproxy_path = DEFAULT_IPROXY_PATH.get(system)
        if iproxy_path:
            if system == "Darwin":
                make_file_executable(iproxy_path)
            return iproxy_path
        warnings.warn("Please install iproxy for a better experience(Ubuntu Linux): apt-get install libusbmuxd-tools")
        return None

    @property
    def usb_device(self):
        """
        Whether the current iOS uses the local USB interface, if so, return the wda.usbmux.Device object
        当前iOS是否使用了本地USB接口，如果是，返回wda.usbmux.Device对象
        Returns: wda.usbmux.Device or None

        """
        if not self._device:
            # wda无法直接获取iOS的udid，因此先检查usb连接的手机udid列表
            try:
                device_list = wda.usbmux.Usbmux().device_list()
            except ConnectionRefusedError:
                # windows上必须要先启动iTunes才能获取到iOS设备列表
                LOGGING.warning("If you are using iOS device in windows, please check if iTunes is launched")
                return None
            except Exception as e:
                # 其他异常，例如 socket unix:/var/run/usbmuxd unable to connect
                print(e)
                return None
            for dev in device_list:
                udid = dev.get('SerialNumber')
                usb_dev = wda.Client(url=wda.requests_usbmux.DEFAULT_SCHEME + udid)
                # 对比wda.info获取到的uuid是否一致
                try:
                    if usb_dev.info['uuid'] == self.uuid:
                        self._device = wda.usbmux.Device(udid)
                        self._udid = udid
                except:
                    return None
        return self._device

    def tear_down(self):
        # 退出时的清理操作，目前暂时只有清理端口
        using_ports = copy(list(self._port_using_func.keys()))
        for port in using_ports:
            try:
                kill_func = self._port_using_func.pop(port)
                kill_func()
            except:
                continue

    # this function auto gen local port
    @retries(3)
    def setup_proxy(self, device_port):
        """
        Map a port number on an iOS device to a random port number on the machine
        映射iOS设备上某个端口号到本机的随机端口号

        Args:
            device_port: The port number to be mapped on the ios device

        Returns:

        """
        if not self.usb_device:
            raise LocalDeviceError("Currently only supports port forwarding for locally connected iOS devices")
        local_port = random.randint(11111, 20000)
        self.do_proxy(local_port, device_port)
        return local_port, device_port

    def remove_proxy(self, local_port):
        if local_port in self._port_using_func:
            kill_func = self._port_using_func.pop(local_port)
            kill_func()

    def do_proxy(self, port, device_port):
        """
        Start do proxy of ios device and self device
        目前只支持本地USB连接的手机进行端口转发，远程手机暂时不支持
        Returns:
            None

        """
        if not self.usb_device:
            raise LocalDeviceError("Currently only supports port forwarding for locally connected iOS devices")
        proxy_process = self.builtin_iproxy_path() or shutil.which("tidevice")
        if proxy_process:
            cmds = [proxy_process, "-u", self._udid, str(port), str(device_port)]
        else:
            # Port forwarding using python
            self.do_proxy_usbmux(port, device_port)
            return

        # Port forwarding using iproxy
        # e.g. cmds=['/usr/local/bin/iproxy', '-u', '00008020-001270842E88002E', '11565', '5001']
        proc = subprocess.Popen(
            cmds,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=SUBPROCESS_FLAG
        )
        # something like port binding fail
        time.sleep(0.5)

        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            stdout = stdout.decode(get_std_encoding(sys.stdout))
            stderr = stderr.decode(get_std_encoding(sys.stderr))
            raise AirtestError((stdout, stderr))

        self._port_using_func[port] = partial(kill_proc, proc)

    def do_proxy_usbmux(self, lport, rport):
        """
        Mapping ports of local USB devices using python multithreading
        使用python多线程对本地USB设备的端口进行映射（当前仅使用USB连接一台iOS时才可用）

        Args:
            lport: local port
            rport: remote port

        Returns:

        """
        server = ThreadedTCPServer(("localhost", lport), TCPRelay)
        server.rport = rport
        server.device = self.usb_device
        server.bufsize = 128
        self.server = server
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self._port_using_func[lport] = self.server.shutdown


if __name__ == '__main__':
    ins = InstructHelper()
    ins.do_proxy_usbmux(5001, 5001)
