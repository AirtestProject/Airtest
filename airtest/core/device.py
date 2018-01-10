# encoding=utf-8
from six import with_metaclass


class MetaDevice(type):

    REGISTRY = {}

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        meta.REGISTRY[name] = cls
        return cls


class Device(with_metaclass(MetaDevice, object)):
    """base class for test device"""

    def __init__(self):
        super(Device, self).__init__()

    def shell(self, *args, **kwargs):
        raise NotImplementedError

    def snapshot(self, *args, **kwargs):
        raise NotImplementedError

    def touch(self, target, **kwargs):
        raise NotImplementedError

    def swipe(self, t1, t2, **kwargs):
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

    def list_app(self, **kwargs):
        raise NotImplementedError

    def install_app(self, uri, **kwargs):
        raise NotImplementedError

    def uninstall_app(self, package):
        raise NotImplementedError

    def get_current_resolution(self):
        raise NotImplementedError
