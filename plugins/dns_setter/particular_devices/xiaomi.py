# coding=utf-8
__author__ = 'lxn3032'


import time
from . import particular_case


MI_2 = ('c0e82f5f', )
MI_SERIALS = MI_2


class MIx(object):
    @particular_case.specified(MI_SERIALS)
    def enter_wlan_advanced_settings(self):
        pass

    @particular_case.specified(MI_SERIALS)
    def use_static_ip(self):
        pass


class MI2(MIx):
    @particular_case.specified(MI_2)
    def enter_wlan_settings(self):
        self.d(text='netease_game').right(clickable=True, className='android.widget.ImageView').click()
        time.sleep(0.5)

    @particular_case.specified(MI_2)
    def modify_wlan_settings_fields(self, dns1, back_after_texting=False):
        for _ in range(5):
            self.uiutil.get_scrollable().scroll.vert.forward(steps=50)
        uiobj = self.d(text=u'域名 1').right(className='android.widget.EditText')
        self.uiutil.replace_text(uiobj, dns1, back_after_texting)
        self.uiutil.click_any({'text': u'确定'})
