from airtest.core.api import *
from airtest.core.android.minitouch import *


connect_device("Android:///")


multitouch_event = [
	DownEvent((100, 100), 0),
	DownEvent((200, 200), 1),
	SleepEvent(1),
	UpEvent(0), UpEvent(1)]

device().minitouch.perform(multitouch_event)
sleep(1)


swipe_event = [DownEvent((500, 500)), SleepEvent(0.1)]

for i in range(5):
	swipe_event.append(MoveEvent((500 + 100*i, 500 + 100*i)))
	swipe_event.append(SleepEvent(0.2))

swipe_event.append(UpEvent())

device().minitouch.perform(swipe_event)
sleep(1)
