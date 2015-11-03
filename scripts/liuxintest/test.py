# encoding=utf8
import sys
sys.path.insert(0, "../..")
import os
print os.path.abspath(sys.path[0])
from scripts.g1utils import server_call
from moa.moa import *
from moa import moa


"""
TODO:
1. 开场准备&脚本间清场：关闭窗口、断线重连等（=sdk）
2. 图像识别准确度&可信度
"""


set_serialno()
moa.OP_DELAY = 0.5


server_call("$mb gen_fighter set g_qc_result 1")


def clear_task():
    server_call("$at g1/sday0 $id")
    server_call("$at g1/set1 $id mfb 0")
    server_call("at/G1/atdriver->clear_all_task(\"$id@89\")")
    server_call("$mb task_event set gEventProb 0")
    server_call("$mb task_event set gEventFriend 88")
    touch("main.png")


def fb():
    clear_task()
    touch("fb.png")
    touch("start_fb.png")
    touch("start_fight.png")
    # assert_exists("fbfighting.png", msg=u"副本战斗中", timeout=5)
    assert_exists("fbfinish.png", msg=u"副本完成", timeout=120, threshold=0.8)


def shimen1001():
    clear_task()
    leaf_before = server_call("at/G1/sm/main->get_sm_leaf(\"$id@89\")") 
    server_call("mobile_app/task/map_task/main->_X_Set_gQCTask(gUserRunner,\"1001\")")
    touch("renwu.png")
    touch("shimen.png")
    touch("start_sm.png")
    touch("qianwang.png")
    assert_exists("1001finish.png", msg=u"师门1001完成", timeout=10)
    leaf_check = server_call('at/G1/sm/main->check_sm($id, "$id@89", %s, 1, 0, 0)'%leaf_before)


def shimen1002():
    clear_task()
    server_call("mobile_app/task/map_task/main->_X_Set_gQCTask(gUserRunner,\"1002\")");
    # 固定找某种物品
    server_call("mobile_app/tinygame/find_things->set_g_qc_test_id(1026)")
    touch("renwu.png")
    touch("shimen.png")
    pos = wait("start_sm.png")
    touch(pos, delay=1)
    touch(pos)
    touch("wolaizhengli.png")
    touch("kaishi.png")
    for i in range(2):
        for i in range(10):
            pos = wait("yao1.png", timeout=1, safe=True)
            keep_capture()
            if pos:
                touch(pos)
                break
            pos = wait("yao2.png", timeout=1, safe=True)
            if pos:
                touch(pos)
                break
            touch("next.png")
            keep_capture(False)
    touch(100, 100)


def shimen1003():
    clear_task()
    server_call("mobile_app/task/map_task/main->_X_Set_gQCTask(gUserRunner,\"1003\")");
    touch("renwu.png")
    touch("shimen.png")
    touch("start_sm.png")
    touch("xunluo.png", rect=[0, 0.5, 1, 1])
    assert_exists("1003finish.png", msg=u"师门1003完成", timeout=10)


# 拼图逻辑太复杂。。先不写吧
def shimen1004():
    clear_task()
    server_call("mobile_app/task/map_task/main->_X_Set_gQCTask(gUserRunner,\"1004\")");
    pos = wait(MoaText(u"领取任务"))
    touch(pos)
    touch(pos, delay=4)
    touch(pos)
    touch((100, 100))


# 1003/1005/1006 都是一样的战斗，分别验证奖励就好了


def dazuo():
    touch("renwu.png")
    swipe((200, 600), (200, 200))
    touch("dazuo.png")
    touch("kaishidazuo.png")
    touch("queding.png")
    touch("queding2.png")
    sleep(5)
    touch("jieshudazuo.png")
    touch("main.png")


def xiuxing():
    touch("renwu.png")
    touch("xiuxing.png")
    pos = wait("xiuxingnpc.png")
    touch((pos[0], pos[1]+300))
    touch("queding.png")
    sleep(5)
    # 验证经验奖励
    touch("likai.png")
    touch("queding3.png")


if __name__ == '__main__':
    # clear_task()
    # fb()
    # shimen1001()
    # shimen1002()
    # shimen1003()
    # dazuo()
    xiuxing()
