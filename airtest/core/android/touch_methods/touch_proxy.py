
class TouchProxy(object):
    """
    Perform touch operation according to the specified method
    """
    TOUCH_METHODS = []

    def __init__(self, touch_method):
        self.touch_method = touch_method

    def __getattr__(self, name):
        method = getattr(self.touch_method, name, None)
        if method:
            return method
        else:
            raise NotImplementedError("%s does not support %s method" %
                                      (getattr(self.touch_method, "METHOD_NAME", ""), name))


def register_touch(cls):
    TouchProxy.TOUCH_METHODS.append(cls.METHOD_NAME)
    return cls


@register_touch
class AdbTouchImplementation(object):
    METHOD_NAME = "ADBTOUCH"

    def __init__(self, base_touch):
        self.base_touch = base_touch

    def touch(self, pos, duration=0.01):
        if duration <= 0.01:
            self.base_touch.touch(pos)
        else:
            self.swipe(pos, pos, duration=duration)

    def swipe(self, p1, p2, duration=0.5, *args, **kwargs):
        duration *= 1000
        self.base_touch.swipe(p1, p2, duration=duration)


@register_touch
class MinitouchImplementation(AdbTouchImplementation):
    METHOD_NAME = "MINITOUCH"

    def __init__(self, minitouch, ori_transformer):
        super(MinitouchImplementation, self).__init__(minitouch)
        self.ori_transformer = ori_transformer

    def touch(self, pos, duration=0.01):
        pos = self.ori_transformer(pos)
        self.base_touch.touch(pos, duration=duration)

    def swipe(self, p1, p2, duration=0.5, steps=5, fingers=1):
        p1 = self.ori_transformer(p1)
        p2 = self.ori_transformer(p2)
        if fingers == 1:
            self.base_touch.swipe(p1, p2, duration=duration, steps=steps)
        elif fingers == 2:
            self.base_touch.two_finger_swipe(p1, p2, duration=duration, steps=steps)
        else:
            raise Exception("param fingers should be 1 or 2")

    def pinch(self, center=None, percent=0.5, duration=0.5, steps=5, in_or_out='in'):
        if center:
            center = self.ori_transformer(center)
        self.base_touch.pinch(center=center, percent=percent, duration=duration, steps=steps, in_or_out=in_or_out)

    def swipe_along(self, coordinates_list, duration=0.8, steps=5):
        pos_list = [self.ori_transformer(xy) for xy in coordinates_list]
        self.base_touch.swipe_along(pos_list, duration=duration, steps=steps)

    def two_finger_swipe(self, tuple_from_xy, tuple_to_xy, duration=0.8, steps=5, offset=(0, 50)):
        tuple_from_xy = self.ori_transformer(tuple_from_xy)
        tuple_to_xy = self.ori_transformer(tuple_to_xy)
        self.base_touch.two_finger_swipe(tuple_from_xy, tuple_to_xy, duration=duration, steps=steps, offset=offset)


@register_touch
class MaxtouchImplementation(MinitouchImplementation):
    METHOD_NAME = "MAXTOUCH"

    def __init__(self, maxtouch, ori_transformer):
        super(MaxtouchImplementation, self).__init__(maxtouch, ori_transformer)
