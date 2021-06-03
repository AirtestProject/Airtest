# -*- coding: utf-8 -*-
import warnings
from airtest.core.android.cap_methods.base_cap import BaseCap
from airtest.core.android.constant import SDK_VERISON_ANDROID7
from airtest import aircv


class AdbCap(BaseCap):
    def get_frame_from_stream(self):
        warnings.warn("Currently using ADB screenshots, the efficiency may be very low.")
        return self.adb.snapshot()

    def snapshot(self, ensure_orientation=True):
        screen = super(AdbCap, self).snapshot()
        if ensure_orientation and self.adb.sdk_version <= SDK_VERISON_ANDROID7:
            screen = aircv.rotate(screen, self.adb.display_info["orientation"] * 90, clockwise=False)
        return screen
