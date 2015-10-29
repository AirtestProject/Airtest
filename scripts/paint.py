#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2015-10-29 16:11:28
# @Last Modified by:   anchen
# @Last Modified time: 2015-10-29 18:01:07
import sys
sys.path.insert(0, "..")
from g1utils import *
from moa.moa import *
from moa import * 
import time 

set_serialno()
moa.OP_DELAY = 0.5

def init():
    server_call("$mb paint set_god $id@89")
    server_call("$at g1/sday0 $id")
    set_var("energy", 1000)
    set_var("exp", 0)
    set_var("cash", 0)
    touch("main.png")

def paint_test():
    init()
    touch("tufa.png",delay=0.5)
    touch("mbdq_btn.png",delay=1.0)
    # touch("chakanweituo_btn.png",delay=1.0)
    
    '''
    #test 游历
    touch("youli_btn.png",delay=1.0)
    touch("xydt_btn.png",delay=1.0)
    touch("go_btn.png",delay=1.0)

    assert_equal(get_var("energy"), 1000 - 450, u"游历仙缘洞天消耗450精力")
    lg_dict = lpc_mixed_2_py(get_var("im_linggan"))
    assert_equal(lg_dict[2]["num"] > 10000, True, u"游历仙缘洞天后山水灵感增加")

    touch("back.png")
    '''
    #test 委托
    


    #test 拍卖
    touch("paimai_btn.png",delay=2.0)
    touch("xieyi.png")
    touch("huaniao.png")
    touch("kaishizuohua.png",delay=1.0)
    assert_exists("painting.png",u"播放拍卖动画")
    time.sleep(5.0)
    touch("paimai.png",delay=1.0)
    touch((0,0),offset={"x":50,"y":50,"percent":True},delay=15)
    # touch("paimai_touxiang.png",delay=20)
    touch((0,0),offset={"x":50,"y":50,"percent":True})

    lg_dict = lpc_mixed_2_py(get_var("im_linggan"))
    assert_equal(get_var("exp") > 0 , True, u"拍卖完成获得经验")
    assert_equal(get_var("cash") > 0 , True, u"拍卖完成获得金钱")
    assert_equal(lg_dict[3]["num"] < 10000 , True, u"拍卖完成消耗灵感")

if __name__ == '__main__':
    paint_test()