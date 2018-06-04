from airtest.core.api import *
from poco.drivers.qt import QtPoco

connect_device("linux:///")
# touch((300, 300))

p = QtPoco()
# d = (p.agent.hierarchy.dump())
# import json
# s = json.dumps(d, indent=4)
# print(s)
# for i in p():
#     print(i)
# print(p.agent.hierarchy.selector.getRoot())
p(name="Open", type="QToolButton").click()
# print(p.agent.hierarchy.select(('attr=', ('name', 'NodePad'))))
# p(type="QTextEdit").click()