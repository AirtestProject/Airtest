# -*- coding: utf-8 -*-
import traceback
from airtest import aircv


class BaseCap(object):
    """
    Base class for all screenshot methods
    所有屏幕截图方法的基类
    """

    def __init__(self, adb, *args, **kwargs):
        self.adb = adb

    def get_frame_from_stream(self):
        """
        Get a frame of the current screen from the mobile screen stream

        从手机画面流中，获取一张当前屏幕截图

        Returns: frame_data

        """
        raise NotImplementedError

    def get_frame(self):
        # 获得单张屏幕截图
        return self.get_frame_from_stream()

    def teardown_stream(self):
        pass

    def snapshot(self, ensure_orientation=True, *args, **kwargs):
        """
        Take a screenshot and convert it into a cv2 image object

        获取一张屏幕截图，并转化成cv2的图像对象

        Returns: numpy.ndarray

        """
        screen = self.get_frame_from_stream()
        try:
            screen = aircv.utils.string_2_img(screen)
        except Exception:
            # may be black/locked screen or other reason, print exc for debugging
            traceback.print_exc()
            return None
        return screen
