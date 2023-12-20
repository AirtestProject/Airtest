#! /usr/bin/env python
# -*- coding: utf-8 -*-
import numpy
import socket
import traceback
from airtest import aircv
from airtest.utils.snippet import reg_cleanup, on_method_ready, ready_method
from airtest.core.ios.constant import ROTATION_MODE, DEFAULT_MJPEG_PORT
from airtest.utils.logger import get_logger
from airtest.utils.safesocket import SafeSocket


LOGGING = get_logger(__name__)


class SocketBuffer(SafeSocket):
    def __init__(self, sock: socket.socket):
        super(SocketBuffer, self).__init__(sock)

    def _drain(self):
        _data = self.sock.recv(1024)
        if _data is None or _data == b"":
            raise IOError("socket closed")
        self.buf += _data
        return len(_data)

    def read_until(self, delimeter: bytes) -> bytes:
        """ return without delimeter """
        while True:
            index = self.buf.find(delimeter)
            if index != -1:
                _return = self.buf[:index]
                self.buf = self.buf[index + len(delimeter):]
                return _return
            self._drain()

    def read_bytes(self, length: int) -> bytes:
        while length > len(self.buf):
            self._drain()

        _return, self.buf = self.buf[:length], self.buf[length:]
        return _return

    def write(self, data: bytes):
        return self.sock.sendall(data)


class MJpegcap(object):

    def __init__(self, instruct_helper=None, ip='localhost', port=None, ori_function=None):
        self.instruct_helper = instruct_helper
        self.port = int(port or DEFAULT_MJPEG_PORT)
        self.ip = ip
        # 如果指定了port，说明已经将wda的9100端口映射到了新端口，无需本地重复映射
        self.port_forwarding = True if self.port == DEFAULT_MJPEG_PORT and ip in ('localhost', '127.0.0.1') else False
        self.ori_function = ori_function
        self.sock = None
        self.buf = None
        self._is_running = False

    @ready_method
    def setup_stream_server(self):
        if self.port_forwarding:
            self.port, _ = self.instruct_helper.setup_proxy(9100)
        self.init_sock()
        reg_cleanup(self.teardown_stream)

    def init_sock(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, self.port))
            self.buf = SocketBuffer(self.sock)
            self.buf.write(b"GET / HTTP/1.0\r\nHost: localhost\r\n\r\n")
            self.buf.read_until(b'\r\n\r\n')
            self._is_running = True
            LOGGING.info("mjpegsock is ready")
        except ConnectionResetError:
            # 断开tidevice或是拔线，会导致这个异常，直接退出即可
            LOGGING.error("mjpegsock connection error")
            raise

    @on_method_ready('setup_stream_server')
    def get_frame_from_stream(self):
        if self._is_running is False:
            self.init_sock()
        try:
            while True:
                line = self.buf.read_until(b'\r\n')
                if line.startswith(b"Content-Length"):
                    length = int(line.decode('utf-8').split(": ")[1])
                    break
            while True:
                if self.buf.read_until(b'\r\n') == b'':
                    break
            imdata = self.buf.read_bytes(length)
            return imdata
        except IOError:
            # 如果暂停获取mjpegsock的数据一段时间，可能会导致它断开，这里将self.buf关闭并临时返回黑屏图像
            # 等待下一次需要获取屏幕时，再进行重连
            LOGGING.debug("mjpegsock is closed")
            self._is_running = False
            self.buf.close()
            return self.get_blank_screen()

    def get_frame(self):
        # 获得单张屏幕截图
        return self.get_frame_from_stream()

    def snapshot(self, ensure_orientation=True, *args, **kwargs):
        """
        Take a screenshot and convert it into a cv2 image object

        获取一张屏幕截图，并转化成cv2的图像对象
        !!! 注意，该方法拿到的截图可能不是队列中最新的，除非一直在消费队列中的图像，否则可能会是过往图像内容，请谨慎使用

        Args:
            ensure_orientation: True or False whether to keep the orientation same as display

        Returns: numpy.ndarray

        """
        screen = self.get_frame_from_stream()
        try:
            screen = aircv.utils.string_2_img(screen)
        except Exception:
            # may be black/locked screen or other reason, print exc for debugging
            traceback.print_exc()
            return None

        if ensure_orientation:
            if self.ori_function:
                display_info = self.ori_function()
                orientation = next(key for key, value in ROTATION_MODE.items() if value == display_info["orientation"])
                screen = aircv.rotate(screen, -orientation, clockwise=False)

        return screen

    def get_blank_screen(self):
        """
        生成一个黑屏图像，在连接失效时代替屏幕画面返回
        Returns:

        """
        if self.ori_function:
            display_info = self.ori_function()
            width, height = display_info['width'], display_info['height']
            if display_info["orientation"] in [90, 270]:
                width, height = height, width
        else:
            width, height = 1080, 1920
        img = numpy.zeros((width, height, 3)).astype('uint8')
        img_string = aircv.utils.img_2_string(img)
        return img_string

    def teardown_stream(self):
        if self.buf:
            self.buf.close()
        if self.port_forwarding:
            self.instruct_helper.remove_proxy(self.port)
        self.port = None


if __name__ == "__main__":
    import wda
    from airtest.core.ios.instruct_cmd import InstructHelper
    addr = "http://localhost:8100"
    driver = wda.Client(addr)
    info = driver.info
    instruct_helper = InstructHelper(info['uuid'])
    mjpeg_server = MJpegcap(instruct_helper)
    print(len(mjpeg_server.get_frame()))