#encoding=utf8
__author__ = 'Someone'

set_serialno()
# start your script here
touch(r"tpl1450684831555.png", record_pos=(-0.466, -0.176), resolution=(1280, 720))

touch(r"tpl1450665551469.png", record_pos=(-0.277, -0.108), resolution=(1280, 720))
swipe(r"tpl1450665558323.png", vector=[-0.014, 0.3783], record_pos=(-0.28, -0.109), resolution=(1280, 720))
wait(r"tpl1450665589451.png", record_pos=(-0.28, -0.108), resolution=(1280, 720))
exists(r"tpl1450665609094.png", record_pos=(0.196, -0.141), resolution=(1280, 720))
text("你好")
server_call("hello")
sleep(1.0)
assert_exists(r"tpl1450665645211.png", "福利界面可见", record_pos=(0.008, -0.222), resolution=(1280, 720))
assert_not_exists(r"tpl1450665672526.png", "看不到人物", record_pos=(0.137, -0.051), resolution=(1280, 720))

assert_equal("111", "111", "服务端数值符合预期")
keyevent("BACK")