# coding=utf-8
__author__ = 'lxn3032'


from functools import wraps


class FnSlots(object):
    def __init__(self):
        super(FnSlots, self).__init__()
        self._fn_slots = {}  # (sn, fnname) -> fn

    def specified(self, snlist):
        def wrapper(func):
            for sn in snlist:
                self._fn_slots[(sn, func.__name__)] = func
            return func
        return wrapper

    def default_call(self, func):
        @wraps(func)
        def decorated(this, *args, **kwargs):
            specified_fn = self._fn_slots.get((this.sn, func.__name__), None)
            if specified_fn:
                return specified_fn(this, *args, **kwargs)
            else:
                return func(this, *args, **kwargs)
        return decorated
