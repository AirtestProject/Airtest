from airtest.core.ios.ios import IOS
import time

addr="http://10.251.100.86:20003"

device = IOS(addr=addr)
# print(device.uuid)
# print(device.session)
print(device.window_size())
# print(device.device_status())
# print(device.get_ip_address())
print(device.orientation)
# print(device.new_orientation)
# print(device.display_info)
# print(device.get_render_resolution())
# device.home()
# start_time_to = time.time()
# device.touch((100, 100)) # 可
# print("cost time: {}".format(time.time() - start_time_to))
# start_time_sw = time.time()
# device.swipe((0.1, 0.3), (0.3, 0.3)) # 可
# print("cost time: {}".format(time.time() - start_time_sw))
device.snapshot(filename="test.jpg")
# device.keyevent('home')
# device.text("Hello", enter=False)
# print(device.app_state("com.apple.Preferences"))
# device.start_app("com.apple.Preferences")
# print(device.app_state("com.apple.Preferences"))
# device.stop_app("com.apple.Preferences")
# print(device.app_state("com.apple.Preferences"))
# device.press('home')
# device.press('volumeUp')
# device.press('volumeDown'
# down = {'type': 'down', 'x': 471.5681063122923, 'y': 2043.4617940199332}
# move = {'type': 'move', 'x': 30.671096345514947, 'y': 1506.7176079734218}
# up = {'type': 'up', 'x': 30.671096345514947, 'y': 1506.7176079734218}
# device.minitouch.operate(down)
# device.minitouch.operate(move)
# device.minitouch.operate(up)

# 新接口调试
# print(device.is_locked())
# device.unlock()
# device.lock()
# print(device.is_locked())
# print(device.alert_exists())
# print(device.alert_buttons())
# device.alert_accept()
# device.alert_dismiss()
# device.alert_click(['不允许'])
# print(device.app_current())
print(device.device_info())
print(device.uuid)