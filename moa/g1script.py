# encoding=utf8

from g1utils import server_call
from moa import *

set_serialno()
server_call("$at g1/sday0 $id")
touch(MoaText(u"副 本", font=u"华康唐风隶"), delay=0.5)
touch(MoaText(u"开 启"))
# touch(MoaText(u"挑 战"))

