#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2015-10-23 15:57:27
# @Last Modified by:   anchen
# @Last Modified time: 2015-10-26 20:11:12

import sys
sys.path.insert(0, "..")
from g1utils import *
from moa.moa import *
from moa import * 


set_serialno()
moa.OP_DELAY = 0.5

# touch("renwu_btn.png",delay=2.0)
# # # touch(MoaText(u"国子监", font=u"微软雅黑"), delay=0.5)
# touch("gzj_btn.png",delay=2.0)
# touch("start_qs_btn.png",delay=2.0)

# touch("answer_area.png", delay=2.0, offset={'x':-18,'y':-3,'percent':True})
#
def init():
    server_call("$at g1/sday0 $id")
    set_var("energy", 1000)
    set_var("exp", 0)

def check_rew():
    energy = get_var("energy")
    active = get_daycnt("active")
    exp = get_var("exp")

    assert_condition("%d == 995" % energy, u"答题成功消耗5精力")
    assert_condition("%d > 0" % exp, u"答题成功后获得经验")
    assert_condition("%d >= 5" % active, u"答题成功获得活跃度")

def gzj_test():
    init()
    touch('renwu_btn.png', delay=1.5)
    touch("gzj_btn.png",delay=2.0)
    touch("start_qs_btn.png",delay=2.0)

    score_goal = get_var('gzj_pass_score')
    times = score_goal / 2 + 1;

    pos_dict = {1:[-1,-1], 2:[1,-1], 3:[-1,1], 4:[1,1],}
    for i in range(times):
        true_pos = get_var("_gzj_true_pos")
        if not true_pos:
            break
        
        tmp = pos_dict[true_pos]

        touch("answer_area.png", delay=1.0,offset={'x':18 * tmp[0], 'y': 3 * tmp[1], 'percent':True})

    check_rew()


if __name__ == '__main__':
    gzj_test()




