# coding=utf-8
__author__ = 'lxn3032'


import random
from pprint import pprint

import airtest.core.main
from airtest.core.main import set_serialno, snapshot, logwrap, _log_in_func
from airtest.core.android.uiautomator import AutomatorDevice


PRIMARY_ACTION = ['click', 'long_click', 'swipe', 'drag', 'fling', 'scroll', 'press', 'clear_text', 'set_text']

SECONDARY_ACTIONS = {
    'press': ['home', 'back', 'left', 'right', 'up', 'down', 'center', 'menu', 'search', 'enter', 'delete', 'del',
              'volumn_up', 'volumn_down', 'volumn_mute', 'camera', 'power'],
    'swipe': ['left', 'right', 'top', 'bottom'],
    'drag': ['to'],
    'open': ['notification', 'quick_settings'],
    'click': ['bottomright', 'topleft', 'wait'],
    'long_click': ['bottomright', 'topleft'],
    'pinch': ['In', 'Out'],
    'wait': ['exists', 'gone'],
    'fling': ['forward', 'backward', 'toBeginning', 'toEnd'],
    'scroll': ['forward', 'backward', 'toBeginning', 'toEnd', 'to'],
    'gesture': ['to'],
}

TERTIARY_ACTION = {
    'fling': {
        'horiz': ['forward', 'backward', 'toBeginning', 'toEnd'],
        'vert': ['forward', 'backward', 'toBeginning', 'toEnd'],
    },
    'scroll': {
        'horiz': ['forward', 'backward', 'toBeginning', 'toEnd', 'to'],
        'vert': ['forward', 'backward', 'toBeginning', 'toEnd', 'to'],
    }
}


SELECTOR_ARGS = ['text', 'textContains', 'textMatches', 'textStartsWith',
                 'className', 'classNameMatches',
                 'description', 'descriptionContains', 'descriptionMatches', 'descriptionStartsWith',
                 'checkable', 'checked', 'clickable', 'longClickable',
                 'scrollable', 'enabled', 'focusable', 'focused', 'selected',
                 'packageName', 'packageNameMatches',
                 'resourceId', 'resourceIdMatches',
                 'index', 'instance']
QUERY_ACTION = ['info', 'exists', 'count', 'dump', 'screenshot', 'freeze_rotation'] + SELECTOR_ARGS


log = []
action_stack = []


def genlog(action, params, uiobj):
    global log, action_stack
    pprint(log)
    @logwrap
    def command_layer(action, params):
        traverse_layer(action, params)
        _log_in_func({"name": action, 'ret': None})

    @logwrap
    def traverse_layer(action, params):
        snapshot()
        if uiobj and 'visibleBounds' in uiobj:
            b = uiobj['visibleBounds']['bottom']
            l = uiobj['visibleBounds']['left']
            r = uiobj['visibleBounds']['right']
            t = uiobj['visibleBounds']['top']
            x = (l + r) / 2
            y = (b + t) / 2
            _log_in_func({
                "cv": {"confidence": 1, "result": [x, y], "rectangle": [[l, t], [l, b], [r, b], [r, t]]},
                'ret': [x, y],
            })
    command_layer(action, params)
    log = []
    action_stack = []


class AutomatorWrapper(object):
    def __init__(self, obj):
        super(AutomatorWrapper, self).__init__()
        self.obj = obj

    def __getattr__(self, action):
        global log, action_stack
        important = True
        is_key_action = False
        if action in PRIMARY_ACTION:
            is_key_action = True
        if action in QUERY_ACTION:
            important = False
        if important:
            action_stack.append(action)
            if is_key_action:
                try:
                    uiobj = self.obj.info
                except:
                    uiobj = None
                log.append({'primary-action': action, 'uiobj': uiobj})
            else:
                log.append({'action': action})

        attr = getattr(self.obj, action)
        if callable(attr):
            return AutomatorWrapper(attr)
        else:
            return attr

    def __call__(self, *args, **kwargs):
        global log, action_stack
        calling = self.obj(*args, **kwargs)

        try:
            uiobj = calling.info
        except:
            uiobj = None
        if args or kwargs:
            if all([k in SELECTOR_ARGS for k in kwargs]):
                log.append({'select': kwargs, 'uiobj': uiobj})
            else:
                log.append({'args': (args, kwargs)})

        if len(log) >= 1 and 'select' in log[-1]:
            if len(log) >= 2 and 'action' in log[-2]:
                action = log[-2]['action']
            else:
                action = 'global'
            genlog('select', [action, log[-1]['select']], uiobj)

        if len(action_stack) >= 3 and action_stack[-3] in TERTIARY_ACTION:
            taction = TERTIARY_ACTION[action_stack[-3]]
            if action_stack[-2] in taction:
                saction = taction[action_stack[-2]]
                if action_stack[-1] in saction:
                    genlog(action_stack[-3], action_stack[-2:] + log[-1].values(), uiobj)
        if len(action_stack) >= 2 and action_stack[-2] in SECONDARY_ACTIONS:
            secondary_action = SECONDARY_ACTIONS[action_stack[-2]]
            if action_stack[-1] in secondary_action:
                genlog(action_stack[-2], action_stack[-1:] + log[-1].values(), uiobj)
        if len(action_stack) >= 1 and action_stack[-1] in PRIMARY_ACTION:
            genlog(action_stack[-1], log[-1].values(), uiobj)

        return self.__class__(calling)


if not airtest.core.main.DEVICE:
    set_serialno()
dev = AutomatorDevice(airtest.core.main.DEVICE.serialno)
d = AutomatorWrapper(dev)


if __name__ == '__main__':
    uiobj = d(text='WLAN').right(className='android.widget.TextView')
    if uiobj and uiobj.text == 'netease_game':
        print uiobj.info
        uiobj.click.topleft()
        d.wait.idle()
        d.press.back()
