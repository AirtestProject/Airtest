#encoding=utf8
__author__ = "刘欣"

# start your script here
install(APK)
amstop(PKG)
amstart(PKG)
sleep(1)
touch(r"tpl1473667153329.png", record_pos=(-0.001, -0.002), resolution=(1536, 2048))
assert_exists(r"tpl1473667188174.png", "小兔子出现", record_pos=(-0.019, 0.12), resolution=(1536, 2048))
p = wait(r"tpl1473667207419.png", record_pos=(0.365, -0.602), resolution=(1536, 2048), timeout=3)
touch(p)
sleep(1)
exec_script(r"14-untitled.owl")
