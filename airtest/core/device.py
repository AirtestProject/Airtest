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

    def shell(self):
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

    def snapshot(self):
        raise NotImplementedError

    def touch(self):
        raise NotImplementedError
        
    def swipe(self):
        raise NotImplementedError
        
    def keyevent(self):
        raise NotImplementedError
        
    def text(self):
        raise NotImplementedError


class iOS(Device):

    def __init__(self):
        pass


class android(Device):

    def __init__(self):
        pass

print DEV_TYPE_DICT
