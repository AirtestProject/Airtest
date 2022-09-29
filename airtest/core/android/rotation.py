# -*- coding: utf-8 -*-
import os
import time
import threading
import traceback
from airtest.utils.snippet import reg_cleanup, is_exiting, on_method_ready, kill_proc
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.logger import get_logger
from airtest.core.android.constant import ORI_METHOD, ROTATIONWATCHER_JAR
LOGGING = get_logger(__name__)


class RotationWatcher(object):
    """
    RotationWatcher class
    """

    def __init__(self, adb, ori_method=ORI_METHOD.MINICAP):
        self.adb = adb
        self.ow_proc = None
        self.nbsp = None
        self.ow_callback = []
        self.ori_method = ori_method
        self._t = None
        self._t_kill_event = threading.Event()
        self.current_orientation = None
        self.path_in_android = "/data/local/tmp/" + os.path.basename(ROTATIONWATCHER_JAR)
        reg_cleanup(self.teardown)

    @on_method_ready('start')
    def get_ready(self):
        pass

    def install(self):
        """
        Install the RotationWatcher package

        Returns:
            None

        """
        try:
            exists_file = self.adb.file_size(self.path_in_android)
        except:
            pass
        else:
            local_minitouch_size = int(os.path.getsize(ROTATIONWATCHER_JAR))
            if exists_file and exists_file == local_minitouch_size:
                LOGGING.debug("install_rotationwatcher skipped")
                return
            self.uninstall()

        self.adb.push(ROTATIONWATCHER_JAR, self.path_in_android)
        self.adb.shell("chmod 755 %s" % self.path_in_android)
        LOGGING.info("install rotationwacher finished")

    def uninstall(self):
        """
        Uninstall the RotationWatcher package

        Returns:
            None

        """
        self.adb.raw_shell("rm %s" % self.path_in_android)

    def setup_server(self):
        """
        Setup rotation wacher server

        Returns:
            server process

        """
        self.install()
        if self.ow_proc:
            self.ow_proc.kill()
            self.ow_proc = None

        p = self.adb.start_shell(
            "app_process -Djava.class.path={0} /data/local/tmp com.example.rotationwatcher.Main".format(
                self.path_in_android))
        self.nbsp = NonBlockingStreamReader(p.stdout, name="rotation_server", auto_kill=True)

        if p.poll() is not None:
            # server setup error, may be already setup by others
            # subprocess exit immediately
            raise RuntimeError("rotation watcher server quit immediately")
        self.ow_proc = p
        return p

    def teardown(self):
        self._t_kill_event.set()
        if self.ow_proc:
            kill_proc(self.ow_proc)
        if self.nbsp:
            self.nbsp.kill()
        self.ow_callback = []
        setattr(self, "_start_ready", None)

    def start(self):
        """
        Start the RotationWatcher daemon thread

        Returns:
            initial orientation

        """
        if self.ori_method == ORI_METHOD.MINICAP:
            try:
                self.setup_server()
            except:
                # install or setup failed
                LOGGING.error(traceback.format_exc())
                LOGGING.error("RotationWatcher setup failed, use ADBORI instead.")
                self.ori_method = ORI_METHOD.ADB

        def _refresh_by_ow():
            # 在产生旋转时，nbsp读取到的内容为b"90\r\n"，平时读到的是空数据None，进程结束时读到的是b""
            line = self.nbsp.readline()
            if line is not None:
                if line == b"":
                    self.teardown()
                    if LOGGING is not None:  # may be None atexit
                        LOGGING.debug("orientationWatcher has ended")
                    else:
                        print("orientationWatcher has ended")
                    return None

                ori = int(int(line) / 90)
                return ori
            # 每隔1秒读取一次
            time.sleep(1)

        def _refresh_by_adb():
            ori = self.adb.getDisplayOrientation()
            return ori

        def _run(kill_event):
            while not kill_event.is_set():
                if self.ori_method == ORI_METHOD.ADB:
                    ori = _refresh_by_adb()
                    if self.current_orientation == ori:
                        time.sleep(3)
                        continue
                else:
                    ori = _refresh_by_ow()
                if ori is None:
                    # 以前ori=None是进程结束，现在屏幕方向不变时会返回None
                    continue
                LOGGING.info('update orientation %s->%s' % (self.current_orientation, ori))
                self.current_orientation = ori
                if is_exiting():
                    self.teardown()
                for cb in self.ow_callback:
                    try:
                        cb(ori)
                    except:
                        LOGGING.error("cb: %s error" % cb)
                        traceback.print_exc()

        self.current_orientation = _refresh_by_ow() if self.ori_method != ORI_METHOD.ADB else _refresh_by_adb()

        self._t = threading.Thread(target=_run, args=(self._t_kill_event, ), name="rotationwatcher")
        self._t.daemon = True
        self._t.start()

        return self.current_orientation

    def reg_callback(self, ow_callback):
        """

        Args:
            ow_callback:

        Returns:

        """
        """方向变化的时候的回调函数，参数一定是ori，如果断掉了，ori传None"""
        if ow_callback not in self.ow_callback:
            self.ow_callback.append(ow_callback)


class XYTransformer(object):
    """
    transform the coordinates (x, y) by orientation (upright <--> original)
    """
    @staticmethod
    def up_2_ori(tuple_xy, tuple_wh, orientation):
        """
        Transform the coordinates upright --> original

        Args:
            tuple_xy: coordinates (x, y)
            tuple_wh: screen width and height
            orientation: orientation

        Returns:
            transformed coordinates (x, y)

        """
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
        """
        Transform the coordinates original --> upright

        Args:
            tuple_xy: coordinates (x, y)
            tuple_wh: screen width and height
            orientation: orientation

        Returns:
            transformed coordinates (x, y)

        """
        x, y = tuple_xy
        w, h = tuple_wh

        if orientation == 1:
            x, y = y, w - x
        elif orientation == 2:
            x, y = w - x, h - y
        elif orientation == 3:
            x, y = h - y, x
        return x, y
