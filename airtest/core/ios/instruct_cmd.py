# -*- coding: utf-8 -*-
import os
import subprocess
import time
import sys
import random
import shutil
import platform
import warnings
import threading
import wda
from airtest.core.error import AirtestError
from airtest.utils.snippet import reg_cleanup, on_method_ready, get_std_encoding
from airtest.utils.logger import get_logger
from airtest.utils.retry import retries
from airtest.utils.compat import SUBPROCESS_FLAG
from airtest.core.ios.constant import IPROXY_PATH
from airtest.core.ios.relay import ThreadedTCPServer, TCPRelay, select, TCPServer

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
        self.cleanup_handler = []
        reg_cleanup(self.tear_down)

    @staticmethod
    def builtin_iproxy_path():
        # iOS的端口转发主要分为以下几种情况：
        # 1. windows上使用iproxy.exe port1 port2 uid
        # 2. mac上如果安装了iproxy，同理，如果没有安装则抛出warning
        # 并且使用relay.py中的逻辑用python转发（效率慢）
        if shutil.which("iproxy"):
            return shutil.which("iproxy")
        if platform.system() == "Windows":
            return IPROXY_PATH
        warnings.warn("Please install iproxy, run command: ")
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
            for dev in wda.usbmux.Usbmux().device_list():
                usb_dev = wda.Client(url=wda.requests_usbmux.DEFAULT_SCHEME + dev['UDID'])
                # 对比wda.info获取到的uuid是否一致
                try:
                    if usb_dev.info['uuid'] == self.uuid:
                        self._device = wda.usbmux.Device(dev['UDID'])
                        self._udid = dev['UDID']
                except:
                    return None
        return self._device

    def tear_down(self):
        for func in self.cleanup_handler:
            func()
        self.cleanup_handler = []

    # this function auto gen local port
    @retries(3)
    def setup_proxy(self, device_port):
        local_port = random.randint(11111, 20000)
        self.do_proxy(local_port, device_port)
        return local_port, device_port

    def do_proxy(self, local_port, device_port):
        """
        Start do proxy of ios device and self device
        目前只支持本地USB连接的手机进行端口转发，远程手机暂时不支持
        Returns:
            None

        """
        if not self.usb_device:
            raise AirtestError("Currently only supports port forwarding for locally connected iOS devices")
        proxy_process = self.builtin_iproxy_path() or shutil.which("tidevice")
        if proxy_process:
            cmds = [proxy_process, "-u", self._udid, str(local_port), str(device_port)]
        else:
            self.do_proxy_usbmux(local_port, device_port)

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

        self.cleanup_handler.append(proc.kill)

    def do_proxy_usbmux(self, lport, rport):
        server = ThreadedTCPServer(("localhost", lport), TCPRelay)
        server.rport = rport
        server.device = self.usb_device
        server.bufsize = 128
        alive = True
        self.server = server
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.cleanup_handler.append(self.server.shutdown)


if __name__ == '__main__':
    # ins = InstructHelper()
    # ins.do_proxy(8100, 8100)
    ins = InstructHelper()
    ins.do_proxy_usbmux(5001, 5001)
