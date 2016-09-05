#encoding=utf-8

class Device(object):
    """base class for test device"""
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
