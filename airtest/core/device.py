#encoding=utf-8


DEV_TYPE_DICT = {}


def register_class(name, cls):
    DEV_TYPE_DICT[name] = cls


class Meta(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        register_class(name, cls)
        return cls


class Device(object):
    """base class for test device"""
    __metaclass__ = Meta

    def __init__(self):
        super(Device, self).__init__()
        self._custom_snapshot_method = None

    def shell(self):
        raise NotImplementedError

    def snapshot(self, *args, **kwargs):
        raise NotImplementedError

    def touch(self):
        raise NotImplementedError
        
    def swipe(self):
        raise NotImplementedError
        
    def keyevent(self):
        raise NotImplementedError
        
    def text(self):
        raise NotImplementedError

    def start_app(self):
        raise NotImplementedError

    def stop_app(self):
        raise NotImplementedError

    def clear_app(self):
        raise NotImplementedError

    def install_app(self):
        raise NotImplementedError

    def uninstall_app(self):
        raise NotImplementedError

    def register_custom_snapshot_method(self, func):
        """
        注册自定义截图方法

        Args:
            func: 接受0个或1个参数的函数，
                    @args filename=None, 截图临时存盘文件名
                  返回aircv.screen对象，参考`aircv.string_2_img`
        """
        self._custom_snapshot_method = func

    def _snapshot_impl(self, *args, **kwargs):
        if callable(self._custom_snapshot_method):
            self._custom_snapshot_method(*args, **kwargs)
        else:
            self.snapshot(*args, **kwargs)
