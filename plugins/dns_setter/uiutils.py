# coding=utf-8
__author__ = 'lxn3032'


import time
import traceback


class UIUtil(object):
    def __init__(self, d):
        super(UIUtil, self).__init__()
        self.d = d

    def get_scrollable(self):
        if self.d(className='android.widget.ScrollView').exists:
            return self.d(className='android.widget.ScrollView')
        else:
            return self.d(className='android.widget.ListView')

    def click_any(self, *pattern):
        for p in pattern:
            uiobj = self.d(**p)
            if uiobj.exists:
                uiobj.click()
                time.sleep(0.6)
                return uiobj
        return None

    def scroll_find(self, *pattern):
        for p in pattern:
            try:
                self.get_scrollable().scroll.to(**p)
            except:
                # in some cases ListView is not scrollable, just skip that
                pass
            uiobj = self.d(**p)
            if uiobj.exists:
                return uiobj
        return None

    def scroll_to_click_any(self, *pattern):
        for p in pattern:
            self.get_scrollable().scroll.to(**p)
            uiobj = self.click_any(p)
            if uiobj:
                return uiobj
        return None

    def wait_any(self, *pattern, **kwargs):
        if 'timeout' in kwargs:
            timeout = kwargs['timeout']
        else:
            timeout = 3000
        for p in pattern:
            self.d(**p).wait.exists(timeout=timeout)
            if self.d(**p).exists:
                return True
        return False

    def replace_text(self, uiobj, text, back_after_texting=False):
        uiobj.click.bottomright()
        time.sleep(1)
        uiobj.clear_text()
        uiobj.set_text(text)
        time.sleep(0.5)
        result = uiobj.text
        try:
            idx1 = result.index(text)
        except ValueError:
            raise Exception('{} \n\ninput dns field failed.'.format(traceback.format_exc()))
        idx2 = idx1 + len(text)
        if idx1 > 0:
            # 光标移到最左边，往右移动idx1，删掉前面那部分
            for _ in range(len(result)):
                self.d.press('left')
            for _ in range(idx1):
                self.d.press('right')
                self.d.press('del')
        current_len = len(uiobj.text)
        if idx2 < len(result):
            # 一定要先归位到最左，不然往右移光标时会移出到控件外面的
            uiobj.click.bottomright()
            for _ in range(current_len):
                self.d.press('left')
            for _ in range(current_len):
                self.d.press('right')
            for _ in range(current_len - idx2):
                self.d.press('del')
        if back_after_texting:
            self.d.press.back()
