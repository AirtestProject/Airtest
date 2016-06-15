# coding=utf-8
__author__ = 'lxn3032'


from ..fnslots import FnSlots


try:
    _ = particular_case
except NameError:
    particular_case = FnSlots()
