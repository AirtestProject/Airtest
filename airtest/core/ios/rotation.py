# -*- coding: utf-8 -*-
import threading
import traceback
import time
from airtest.core.error import AirtestError
from airtest.utils.snippet import reg_cleanup, on_method_ready
from airtest.utils.logger import get_logger

from wda import LANDSCAPE, PORTRAIT, LANDSCAPE_RIGHT, PORTRAIT_UPSIDEDOWN
from wda import WDAError

LOGGING = get_logger(__name__)


class RotationWatcher(object):
    """
    RotationWatcher class
    """

    def __init__(self, iosHandle):
        self.iosHandle = iosHandle
        self.session = iosHandle.session
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

    def start(self):
        """
        Start the RotationWatcher daemon thread

        Returns:
            None

        """
        self._install_and_setup()

        def _refresh_by_ow():
            try:
                return self.session.orientation
            except WDAError as err:
                if err.status == 6:
                    self.iosHandle._fetchNewSession()
                    self.session = self.iosHandle.session
                    return self.session.orientation
                else:
                    return self.last_result
            except ValueError as err:
                import traceback
                print(traceback.format_exc())
                return self.last_result

        def _run():
            while not self._stopEvent.isSet():
                time.sleep(1)
                ori = _refresh_by_ow()
                if ori is None:
                    break
                elif self.last_result == ori:
                    continue
                LOGGING.info('update orientation %s->%s' % (self.last_result, ori))
                self.last_result = ori

                # exec cb functions
                for cb in self.ow_callback:
                    try:
                        cb(ori)
                    except:
                        LOGGING.error("cb: %s error" % cb)
                        traceback.print_exc()

        self.roundProcess = threading.Thread(target=_run, name="rotationwatcher")
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

        # no need to do changing
        # ios touch point same way of image

        return x, y

        if orientation == LANDSCAPE:
            x, y = x, y
        elif orientation == LANDSCAPE_RIGHT:
            x, y = x, y
        elif orientation == PORTRAIT_UPSIDEDOWN:
            x, y = x, y
        elif orientation == PORTRAIT:
            x, y = x, y
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

        # no need to do changing
        # ios touch point same way of image

        return x, y