# -*- coding: utf-8 -*-
import threading
import traceback
import time
import wda
from airtest.core.ios.constant import ROTATION_MODE
from airtest.utils.snippet import reg_cleanup, on_method_ready
from airtest.utils.logger import get_logger


LOGGING = get_logger(__name__)


class RotationWatcher(object):
    """
    RotationWatcher class
    """

    def __init__(self, iosHandle):
        self.iosHandle = iosHandle
        self.ow_callback = []
        self.roundProcess = None
        self._stopEvent = threading.Event()
        self.last_result = None
        reg_cleanup(self.teardown)

    @on_method_ready('start')
    def get_ready(self):
        pass

    def _install_and_setup(self):
        """
        Install and setup the RotationWatcher package

        Raises:
            RuntimeError: if any error occurs while installing the package

        Returns:
            None

        """
        # fetch orientation result
        self.last_result = None
        # reg_cleanup(self.ow_proc.kill)

    def teardown(self):
        # if has roataion watcher stop it
        if self.roundProcess:
            self._stopEvent.set()
        self.ow_callback = []

    def start(self):
        """
        Start the RotationWatcher daemon thread

        Returns:
            None

        """
        self._install_and_setup()

        def _refresh_by_ow():
            try:
                return self.get_rotation()
            except Exception:
                # 重试5次，如果还是失败就返回None，终止线程
                for i in range(5):
                    try:
                        self.iosHandle._fetch_new_session()
                        return self.get_rotation()
                    except:
                        time.sleep(2)
                        continue
                LOGGING.info("orientationWatcher has ended")
                return None

        def _run():
            while not self._stopEvent.isSet():
                time.sleep(1)
                ori = _refresh_by_ow()
                if ori is None:
                    break
                elif self.last_result == ori:
                    continue
                LOGGING.info('update orientation %s->%s' %
                             (self.last_result, ori))
                self.last_result = ori

                # exec cb functions
                for cb in self.ow_callback:
                    try:
                        cb(ori)
                    except:
                        LOGGING.error("cb: %s error" % cb)
                        traceback.print_exc()

        self.roundProcess = threading.Thread(
            target=_run, name="rotationwatcher")
        # self._t.daemon = True
        self.roundProcess.start()

    def reg_callback(self, ow_callback):
        """

        Args:
            ow_callback:

        Returns:

        """
        """方向变化的时候的回调函数，参数一定是ori，如果断掉了，ori传None"""
        self.ow_callback.append(ow_callback)

    def get_rotation(self):
        return self.iosHandle.get_orientation()


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
            tuple_wh: current screen width and height
            orientation: orientation

        Returns:
            transformed coordinates (x, y)

        """
        x, y = tuple_xy
        w, h = tuple_wh

        # no need to do changing
        # ios touch point same way of image

        if orientation == wda.LANDSCAPE:
            x, y = h-y, x
        elif orientation == wda.LANDSCAPE_RIGHT:
            x, y = y, w-x
        elif orientation == wda.PORTRAIT_UPSIDEDOWN:
            x, y = w-x, h-y
        elif orientation == wda.PORTRAIT:
            x, y = x, y
        return x, y

    @staticmethod
    def ori_2_up(tuple_xy, tuple_wh, orientation):
        """
        Transform the coordinates original --> upright

        Args:
            tuple_xy: coordinates (x, y)
            tuple_wh: current screen width and height
            orientation: orientation

        Returns:
            transformed coordinates (x, y)

        """
        x, y = tuple_xy
        w, h = tuple_wh

        # Only in the ipad+home interface,
        # the vertical screen coordinates need to be converted to display coordinates
        if orientation == wda.LANDSCAPE:
            x, y = y, h - x
        elif orientation == wda.LANDSCAPE_RIGHT:
            x, y = w - y, x
        elif orientation == wda.PORTRAIT_UPSIDEDOWN:
            x, y = w - x, h - y

        return x, y
