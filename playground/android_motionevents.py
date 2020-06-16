from airtest.core.api import *
from airtest.core.android.touch_methods.base_touch import *
from airtest.core.android.rotation import XYTransformer


connect_device("Android:///")
# get current device
dev = device()


multitouch_event = [
    DownEvent((100, 100), 0),
    DownEvent((200, 200), 1),
    SleepEvent(1),
    UpEvent(0), UpEvent(1)]

dev.minitouch.perform(multitouch_event)
sleep(1)


swipe_event = [DownEvent((500, 500)), SleepEvent(0.1)]

for i in range(5):
    swipe_event.append(MoveEvent((500 + 100*i, 500 + 100*i)))
    swipe_event.append(SleepEvent(0.2))

swipe_event.append(UpEvent())

dev.minitouch.perform(swipe_event)
sleep(1)


# in landscape mode
def transform_xy(tuple_xy, display_info):
    x, y = tuple_xy
    x, y = XYTransformer.up_2_ori(
            (x, y),
            (display_info["width"], display_info["height"]),
            display_info["orientation"]
        )
    return x, y


touch_landscape_point = [DownEvent(transform_xy((100, 100), dev.display_info)), SleepEvent(1), UpEvent()]
dev.minitouch.perform(touch_landscape_point)
