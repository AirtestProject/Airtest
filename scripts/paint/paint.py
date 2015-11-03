#!/usr/bin/env python -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2015-10-29 16:11:28
# @Last Modified by:   anchen
# @Last Modified time: 2015-11-03 21:25:03
import sys
sys.path.insert(0, "..")
from g1utils import *
sys.path.insert(0, "../..")
from moa.moa import *
from moa import * 
import time 

set_serialno()
moa.OP_DELAY = 0.5

def init():
    server_call("$mb paint set_god $id@89")
    server_call("$at g1/sday0 $id")
    server_call("$at bian 2")
    set_var("energy", 1000)
    set_var("exp", 0)
    set_var("cash", 0)
    touch("main.png")

def paint_test():
    init()
    touch("tufa.png",delay=0.5)
    touch("mbdq_btn.png",delay=1.0)
    #test 游历
    touch("youli_btn.png",delay=1.0)
    touch("xydt_btn.png",delay=1.0)
    touch("go_btn.png",delay=1.0)

    assert_equal(get_var("energy"), 1000 - 450, u"游历仙缘洞天消耗450精力")
    lg_dict = lpc_mixed_2_py(get_var("im_linggan"))
    assert_equal(lg_dict[2]["num"] > 10000, True, u"游历仙缘洞天后山水灵感增加")

    touch("back.png")


    #test 委托
    ret = server_call("at/G1/mb/test->set_test_task($id)")
    if ret:
        set_var("exp", 0)
        server_call("$at g1/clearbag $id")
        server_call("$mb paint set_god $id@89")

        # 公共委托
        touch("chakanweituo_btn.png",delay=3.0)
        touch("paint_longwang.png",delay=2.0)
        assert_exists("paint_publictask.png",u"打开公共委托界面")
        touch("paint_start.png")
        assert_exists("painting.png",u"播放拍卖动画")
        time.sleep(5.0)
        touch("paint_sure.png", delay=1.0)

        assert_equal(get_var("exp") > 0 , True, u"完成公共委托获得经验")
        assert_equal(get_daycnt("im_achieve_task_times"), 1, u"完成公共委托次数增加")
        g1_bag = get_var("g1_bag")
        assert_equal(g1_bag.find("18126") != -1, True, u"完成公共委托获得灵饰书")
        assert_equal(g1_bag.find("4243") != -1, True, u"完成公共委托获得元灵晶石")
        lg_dict = lpc_mixed_2_py(get_var("im_linggan"))
        assert_equal(lg_dict[1]["num"] < 10000 or lg_dict[2]["num"] < 10000 or lg_dict[3]["num"] < 10000 , True, u"完成公共委托消耗灵感")


        set_var("exp", 0)
        server_call("$mb paint set_god $id@89")
        # 私人委托
        touch("chakanweituo_btn.png",delay=3.0)
        assert_exists("paint_finished.png", u"完成公共委托增加已完成标志")
        touch("paint_guanjia.png",delay=2.0)
        assert_exists("paint_publictask.png",u"打开私有委托界面")
        touch("paint_start.png")
        assert_exists("painting.png",u"播放拍卖动画")
        time.sleep(5.0)
        touch("paint_sure.png")

        assert_equal(get_var("exp") > 0 , True, u"完成私人委托获得经验")
        assert_equal(get_daycnt("im_achieve_task_times"), 2, u"完成公共委托次数增加")
        g1_bag = get_var("g1_bag")
        assert_equal(g1_bag.find("646") != -1, True, u"完成私人委托获得彩果")
        lg_dict = lpc_mixed_2_py(get_var("im_linggan"))
        assert_equal(lg_dict[1]["num"] < 10000 or lg_dict[2]["num"] < 10000 or lg_dict[3]["num"] < 10000 , True, u"完成私人委托消耗灵感")



    else:
        assert_equal(True, False, u'没有生成指定的委托任务')

    server_call("$mb paint set_god $id@89")
    #test 拍卖
    touch("paimai_btn.png",delay=3.0)
    touch("xieyi.png")
    touch("huaniao.png")
    touch("kaishizuohua.png",delay=1.0)
    assert_exists("painting.png",u"播放拍卖动画")
    time.sleep(5.0)
    touch("paimai.png",delay=1.0)
    touch((0,0),offset={"x":50,"y":50,"percent":True},delay=20)
    touch((0,0),offset={"x":50,"y":50,"percent":True})

    lg_dict = lpc_mixed_2_py(get_var("im_linggan"))
    assert_equal(get_var("exp") > 0 , True, u"拍卖完成获得经验")
    assert_equal(get_var("cash") > 0 , True, u"拍卖完成获得金钱")
    assert_equal(lg_dict[3]["num"] < 10000 , True, u"拍卖完成消耗灵感")

    touch("main.png")


if __name__ == '__main__':
    paint_test()