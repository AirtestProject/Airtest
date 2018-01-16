# coding=utf-8

from airtest.core.android.rotation import RotationWatcher, XYTransformer 
from airtest.core.device import Device
from airtest.core.kivy.controler import Controler

from jnius import autoclass
from airtest import aircv

class Kivy(Device):
    def __init__(self, serialno=None, mActivity=None, _agent=None):
        super(Kivy, self).__init__()
        if not _agent:
            _Controler = autoclass('org.kivy.android.Controler')
            _agent=_Controler()

        if not mActivity:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            mActivity = PythonActivity.mActivity

        self.controler = Controler(_agent)
        self.mActivity = mActivity

    def stop_app(self):
        pass

    def list_app(self):
        return self.controler.list_app()

    def snapshot(self, filename=None, ensure_orientation=True):
        """default not write into file"""
        file_name = self.controler.snapshot()
        screen = aircv.imread(file_name)

        if filename:
            aircv.imwrite(filename, screen)
        return screen

    def keyevent(self, keyname):
        self.controler.keyevent(keyname)

    def wake(self):
        self.controler.wake()

    def home(self):
        self.keyevent("HOME")

    def touch(self, pos, times=1, duration=0.01):
        for _ in range(times):
            self.controler.touch(pos)

    def swipe(self, p1, p2, duration=5, steps=5):
       # p1 = self._transformPointByOrientation(p1)
       # p2 = self._transformPointByOrientation(p2)
        self.controler.swipe(p1, p2, duration)

    def text(self, text):
        self.controler.text(text)

    def start_app(self, package, activity=None):
        self.controler.start_app(package)
    
    def stop_app(self, package):
        self.controler.stop_app()

    def _transformPointByOrientation(self, tuple_xy):
        x, y = tuple_xy
        x, y = XYTransformer.up_2_ori(
            (x, y),
            (self.display_info["width"], self.display_info["height"]), 
            self.display_info["orientation"]
        )
        return x, y

    def get_now_package(self):
        manager = self.mActivity.getSystemService(Context.ACTIVITY_SERVICE)
        pis = manager.getRunningAppProcesses()
        topAppProcess = pis.get(0)
        if topAppProcess :
            print topAppProcess.processName

    def getDisplayOrientation(self):
        return self.mActivity.getResources().getConfiguration().orientation

    @property
    def display_info(self):
        return self.get_display_info()

    def get_display_info(self):
        display_info = self.controler.get_display_info()
        display_info["rotation"] = display_info["orientation"] * 90
        return display_info


