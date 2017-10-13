# encoding=utf-8
from six import with_metaclass


class MetaDevice(type):

    REPO = {}

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        meta.REPO[name] = cls
        return cls


class Device(with_metaclass(MetaDevice, object)):
    """base class for test device"""

    def __init__(self):
        super(Device, self).__init__()

    def shell(self):
        raise NotImplementedError

    def snapshot(self, *args, **kwargs):
        raise NotImplementedError

    def touch(self, pos, **kwargs):
        raise NotImplementedError

    def swipe(self, p1, p2, **kwargs):
        raise NotImplementedError

    def keyevent(self, key, **kwargs):
        raise NotImplementedError

    def text(self, text, enter=True):
        raise NotImplementedError

    def start_app(self, package):
        raise NotImplementedError

    def stop_app(self, package):
        raise NotImplementedError

    def clear_app(self, package):
        raise NotImplementedError

    def list_app(self, third_only=True):
        raise NotImplementedError

    def install_app(self, uri, **kwargs):
        raise NotImplementedError

    def uninstall_app(self, package):
        raise NotImplementedError
