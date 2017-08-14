# -*- coding: utf-8 -*-
import threading
import traceback
from airtest.core.error import MoaError
from airtest.core.utils import reg_cleanup, get_logger
from airtest.core.android.constant import ROTATIONWATCHER_APK, ROTATIONWATCHER_PACKAGE
LOGGING = get_logger('rotation')


class RotationWatcher(object):

    def __init__(self, android):
        self.android = android
        self.ow_proc = None
        self.ow_callback = []
        self._t = None

    def _setup(self):
        try:
            apk_path = self.android.path_app(ROTATIONWATCHER_PACKAGE)
        except MoaError:
            self.android.install_app(ROTATIONWATCHER_APK, ROTATIONWATCHER_PACKAGE)
            apk_path = self.android.path_app(ROTATIONWATCHER_PACKAGE)
        p = self.android.adb.shell('export CLASSPATH=%s;exec app_process /system/bin jp.co.cyberagent.stf.rotationwatcher.RotationWatcher' % apk_path, not_wait=True)
        if p.poll() is not None:
            raise RuntimeError("orientationWatcher setup error")
        return p

    def get_ready(self):
        if not self._t:
            self.start()

    def start(self):
        self.ow_proc = self._setup()
        reg_cleanup(self.ow_proc.kill)

        def _refresh_by_ow():
            line = self.ow_proc.stdout.readline()
            if line == b"":
                if LOGGING is not None:  # may be None atexit
                    LOGGING.error("orientationWatcher has ended")
                return None

            ori = int(line) / 90
            return ori

        def _run():
            while True:
                ori = _refresh_by_ow()
                if ori is None:
                    break
                for cb in self.ow_callback:
                    try:
                        cb(ori)
                    except:
                        LOGGING.error("cb: %s error" % cb)
                        traceback.print_exc()

        self._t = threading.Thread(target=_run)
        self._t.daemon = True
        self._t.start()

    def reg_callback(self, ow_callback):
        """方向变化的时候的回调函数，参数一定是ori，如果断掉了，ori传None"""
        self.ow_callback.append(ow_callback)


class XYTransformer(object):
    """
    transform xy by orientation
    upright<-->original
    """
    @staticmethod
    def up_2_ori(tuple_xy, tuple_wh, orientation):
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
        x, y = tuple_xy
        w, h = tuple_wh

        if orientation == 1:
            x, y = y, w - x
        elif orientation == 2:
            x, y = w - x, h - y
        elif orientation == 3:
            x, y = h - y, x
        return x, y
