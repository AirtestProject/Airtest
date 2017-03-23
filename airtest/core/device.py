# encoding=utf-8


DEV_TYPE_DICT = {}


def register_class(name, cls):
    DEV_TYPE_DICT[name] = cls


class MetaDevice(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        register_class(name, cls)
        return cls


class Device(object):
    """base class for test device"""
    __metaclass__ = MetaDevice

    def __init__(self):
        super(Device, self).__init__()
        self._custom_snapshot_method = None

    def shell(self):
        raise NotImplementedError

    def snapshot(self, *args, **kwargs):
        raise NotImplementedError

    def touch(self, pos, **kwargs):
        raise NotImplementedError

    def swipe(self):
        raise NotImplementedError

    def keyevent(self, key):
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

    def install_app(self, uri, package, **kwargs):
        raise NotImplementedError

    def uninstall_app(self, package):
        raise NotImplementedError
