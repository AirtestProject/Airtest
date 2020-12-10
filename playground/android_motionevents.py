"""
Android custom motions sample, only support minitouch and maxtouch
Android自定义手势示例代码，仅支持minitouch和maxtouch两种模式
"""

from airtest.core.api import *
from airtest.core.android.touch_methods.base_touch import *


connect_device("Android:///")
# get current device
dev = device()


# 1. tap with two fingers
multitouch_event = [
    DownEvent((100, 100), 0),
    DownEvent((200, 200), 1),  # second finger
    SleepEvent(1),
    UpEvent(0), UpEvent(1)]

dev.touch_proxy.perform(multitouch_event)
sleep(1)


# 2. swipe
swipe_event = [DownEvent((500, 500)), SleepEvent(0.1)]

for i in range(5):
    swipe_event.append(MoveEvent((500 + 100*i, 500 + 100*i)))
    swipe_event.append(SleepEvent(0.2))

swipe_event.append(UpEvent())

dev.touch_proxy.perform(swipe_event)
sleep(1)


# 3. When the screen is horizontal, the coordinates need to be converted
# 注意：如果设备是横屏，必须要加上坐标转换（竖屏也可以加）
ori_transformer = dev.touch_proxy.ori_transformer
touch_landscape_point = [DownEvent(ori_transformer((100, 100))), SleepEvent(1), UpEvent()]
dev.touch_proxy.perform(touch_landscape_point)


# 4. swipe with two fingers
swipe_event2 = [DownEvent((100, 300), 0), DownEvent((100, 500), 1), SleepEvent(0.1)]

for i in range(5):
    swipe_event2.append(MoveEvent((100 + 100*i, 300), 0))
    swipe_event2.append(MoveEvent((100 + 100*i, 500), 1))
    swipe_event2.append(SleepEvent(0.2))

swipe_event2.append(UpEvent(0))
swipe_event2.append(UpEvent(1))

dev.touch_proxy.perform(swipe_event2)

# 5. Long press the app and drag it to the trash can to delete
# 长按然后拖动删除app
longpress_delete_event = [
    DownEvent([908, 892]),
    SleepEvent(2),
    MoveEvent([165, 285]),  # target coordinates
    UpEvent(0)]

dev.touch_proxy.perform(longpress_delete_event)
