# encoding=utf8
import sys
sys.path.insert(0, "..")
from g1utils import server_call
from moa.moa import *
from moa import moa


set_serialno()
moa.OP_DELAY = 0.5
server_call("$at g1/sday0 $id")
server_call("$at g1/set1 $id mfb 0")
touch(MoaText(u"副 本", font=u"华康唐风隶"), delay=0.5)
touch(MoaText(u"开 启"))
touch(MoaText(u"挑 战"))
assert_exists("fbfighting.png", msg=u"副本战斗中", timeout=5)
assert_exists("fbfinish.png", msg=u"副本完成", timeout=40, threshold=0.8)

