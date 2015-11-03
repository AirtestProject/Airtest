#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2015-10-23 15:57:27
# @Last Modified by:   anchen
# @Last Modified time: 2015-11-03 22:03:46

import sys
sys.path.insert(0, "..")
from g1utils import *
sys.path.insert(0, "../..")
from moa.moa import *
from moa import * 


set_serialno()
moa.OP_DELAY = 0.5

def init():
    server_call("$at g1/sday0 $id")
    server_call('mobile_app/task/gzj_task/main->clear_gzj("$id@89")')#清任务
    set_var("energy", 1000)
    set_var("exp", 0)

def check_rew():
    energy = get_var("energy")
    active = get_daycnt("active")
    exp = get_var("exp")
    gzj_times =  get_daycnt("d_gzj_leftTime")

    assert_equal(energy, 995, u"答题成功消耗5精力")
    assert_equal(exp > 0 , True, u"答题成功后获得经验")
    assert_equal(active >= 5, True, u"答题成功获得活跃度")
    assert_equal(gzj_times, 1, u"答题成功答题次数加1")

def gzj_test():
    init()
    touch("renwu_btn.png", delay=3.0)#第一次打开界面要加载很久..
    touch("gzj_btn.png",delay=2.0)
    assert_exists("gzj_start.png",u"弹出答题界面")
    touch("start_qs_btn.png",delay=2.0)

    score_goal = get_var('gzj_pass_score')
    times = score_goal / 2 + 1;

    pos_dict = {1:[-1,-1], 2:[1,-1], 3:[-1,1], 4:[1,1],}

    sc = get_var("gzj_score")
    touch("gzj_tian_btn.png",delay=1.0)
    assert_equal(get_var("gzj_score"),sc + 2,u"使用天王令直接答对")

    sc = get_var("gzj_score")
    true_pos = get_var("_gzj_true_pos")
    touch("gzj_ren_btn.png")
    touch("answer_area.png", delay=1.0,offset={'x':18 * pos_dict[true_pos][0], 'y': 3 * pos_dict[true_pos][1], 'percent':True})
    assert_equal(get_var("gzj_score"), sc + 4, u"使用仁王令答对积分翻倍")

    sc = get_var("gzj_score")
    true_pos = (get_var("_gzj_true_pos") + 1) % 4
    touch("gzj_ren_btn.png")
    touch("answer_area.png", delay=1.0,offset={'x':18 * pos_dict[true_pos][0], 'y': 3 * pos_dict[true_pos][1], 'percent':True})
    assert_equal(get_var("gzj_score"), sc - 2, u"使用仁王令答错积分翻倍")


    for i in range(times):
        true_pos = get_var("_gzj_true_pos")
        if not true_pos:
            break
        
        tmp = pos_dict[true_pos]

        touch("answer_area.png", delay=1.0,offset={'x':18 * tmp[0], 'y': 3 * tmp[1], 'percent':True})

    check_rew()
    assert_exists("gzj_finish.png",u"答题成功弹出结束界面")
    touch("main.png")


if __name__ == '__main__':
    gzj_test()




