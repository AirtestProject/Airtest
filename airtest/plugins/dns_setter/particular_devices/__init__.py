# coding=utf-8
__author__ = 'lxn3032'


from airtest.plugins.dns_setter.fnslots import FnSlots


try:
    _ = particular_case
except NameError:
    particular_case = FnSlots()
