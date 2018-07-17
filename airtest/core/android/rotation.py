# -*- coding: utf-8 -*-
import threading
import traceback
from airtest.core.error import AirtestError
from airtest.utils.snippet import reg_cleanup, is_exiting, on_method_ready
from airtest.utils.logger import get_logger
from airtest.core.android.constant import ROTATIONWATCHER_APK, ROTATIONWATCHER_PACKAGE
LOGGING = get_logger(__name__)


class RotationWatcher(object):
    """
    RotationWatcher class
    """

    def __init__(self, adb):
        self.adb = adb
        self.ow_proc = None
        self.ow_callback = []
        self._t = None
        self.current_orientation = None
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
        try:
            apk_path = self.adb.path_app(ROTATIONWATCHER_PACKAGE)
        except AirtestError:
            self.adb.install_app(ROTATIONWATCHER_APK, ROTATIONWATCHER_PACKAGE)
            apk_path = self.adb.path_app(ROTATIONWATCHER_PACKAGE)
        p = self.adb.start_shell('export CLASSPATH=%s;exec app_process /system/bin jp.co.cyberagent.stf.rotationwatcher.RotationWatcher' % apk_path)
        if p.poll() is not None:
            raise RuntimeError("orientationWatcher setup error")
        self.ow_proc = p

    def teardown(self):
        if self.ow_proc:
            self.ow_proc.kill()

    def start(self):
        """
        Start the RotationWatcher daemon thread

        Returns:
            initial orientation

        """
        self._install_and_setup()

        def _refresh_by_ow():
            line = self.ow_proc.stdout.readline()
            if line == b"":
                if LOGGING is not None:  # may be None atexit
                    LOGGING.debug("orientationWatcher has ended")
                else:
                    print("orientationWatcher has ended")
                return None

            ori = int(int(line) / 90)
            return ori

        def _run():
            while True:
                ori = _refresh_by_ow()
                if ori is None:
                    break
                LOGGING.info('update orientation %s->%s' % (self.current_orientation, ori))
                self.current_orientation = ori
                if is_exiting():
                    break
                for cb in self.ow_callback:
                    try:
                        cb(ori)
                    except:
                        LOGGING.error("cb: %s error" % cb)
                        traceback.print_exc()

        self.current_orientation = _refresh_by_ow()

        self._t = threading.Thread(target=_run, name="rotationwatcher")
        # self._t.daemon = True
        self._t.start()

        return self.current_orientation

    def reg_callback(self, ow_callback):
        """

        Args:
            ow_callback:

        Returns:

        """
        """方向变化的时候的回调函数，参数一定是ori，如果断掉了，ori传None"""
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
