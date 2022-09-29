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

    @property
    def uuid(self):
        self._raise_not_implemented_error()

    def shell(self, *args, **kwargs):
        self._raise_not_implemented_error()

    def snapshot(self, *args, **kwargs):
        self._raise_not_implemented_error()

    def touch(self, target, **kwargs):
        self._raise_not_implemented_error()

    def double_click(self, target):
        raise NotImplementedError

    def swipe(self, t1, t2, **kwargs):
        self._raise_not_implemented_error()

    def keyevent(self, key, **kwargs):
        self._raise_not_implemented_error()

    def text(self, text, enter=True):
        self._raise_not_implemented_error()

    def start_app(self, package, **kwargs):
        self._raise_not_implemented_error()

    def stop_app(self, package):
        self._raise_not_implemented_error()

    def clear_app(self, package):
        self._raise_not_implemented_error()

    def list_app(self, **kwargs):
        self._raise_not_implemented_error()

    def install_app(self, uri, **kwargs):
        self._raise_not_implemented_error()

    def uninstall_app(self, package):
        self._raise_not_implemented_error()

    def get_current_resolution(self):
        self._raise_not_implemented_error()

    def get_render_resolution(self):
        self._raise_not_implemented_error()

    def get_ip_address(self):
        self._raise_not_implemented_error()

    def _raise_not_implemented_error(self):
        platform = self.__class__.__name__
        raise NotImplementedError("Method not implemented on %s" % platform)

    def disconnect(self):
        pass
