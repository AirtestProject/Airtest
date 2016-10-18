# coding=utf-8
__author__ = 'lxn3032'


import time
import traceback
from pprint import pprint

import airtest.core.main
from airtest.core.main import set_serialno, snapshot, logwrap, _log_in_func
from airtest.core.android.uiautomator import AutomatorDevice


__all__ = ['UiAutomator']

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


def genlog(action, params, uiobj=None):
    global log, action_stack

    # transform action names
    # avoid conflicting with airtest actions
    if action == 'swipe':
        action = 'ui.swipe'

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
            
            if params and params[-1] == "topleft":  # 点击识别区域的左上角
                x, y = l, t
            elif params and params[-1] == "bottomright":  # 点击识别区域的右下角
                x, y = r, b
            else:  # 点击中间位置
                x, y = (l + r) / 2, (b + t) / 2

            _log_in_func({
                "cv": {"confidence": 1, "result": [x, y], "rectangle": [[l, t], [l, b], [r, b], [r, t]]},
                'ret': [x, y],
            })
    command_layer(action, params)
    log = []
    action_stack = []


def try_call(f, action, *args, **kwargs):
    logger = airtest.core.main.LOGGER
    start = time.time()
    fndata = {'name': action, 'args': args, 'kwargs': kwargs}
    logger.running_stack.append(fndata)
    try:
        ret = f(*args, **kwargs)
    except Exception:
        data = {"traceback": traceback.format_exc(), "time_used": time.time() - start}
        fndata.update(data)
        fndata.update(logger.extra_log)
        logger.log("error", fndata)
        raise
    finally:
        logger.running_stack.pop()
    return ret


def try_getattr(obj, attr, action, *args, **kwargs):
    logger = airtest.core.main.LOGGER
    start = time.time()
    fndata = {'name': action, 'args': args, 'kwargs': kwargs}
    logger.running_stack.append(fndata)
    try:
        ret = getattr(obj, attr)
    except Exception:
        data = {"traceback": traceback.format_exc(), "time_used": time.time() - start}
        fndata.update(data)
        fndata.update(logger.extra_log)
        logger.log("error", fndata)
        raise
    finally:
        logger.running_stack.pop()
    return ret


class AutomatorWrapper(object):
    def __init__(self, obj, last_obj=None):
        super(AutomatorWrapper, self).__init__()
        self.obj = obj
        self.last_obj = last_obj  # prev layer obj
        self.selectors = None
        self.select_action = None

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
                log.append({'primary-action': action})
            else:
                log.append({'action': action})

        attr = getattr(self.obj, action)
        if callable(attr):
            return self.__class__(attr, self)
        else:
            return attr

    def __call__(self, *args, **kwargs):
        global log, action_stack
        calling = None

        if args or kwargs:
            if all([k in SELECTOR_ARGS for k in kwargs]):
                # get this select action name
                if len(action_stack) >= 1:
                    action = action_stack[-1]
                else:
                    action = 'global'

                # relative selector
                prev_selector_obj = self._get_selector_obj()
                if prev_selector_obj:
                    uiobj = try_getattr(prev_selector_obj.obj, 'info', prev_selector_obj.select_action, prev_selector_obj.selectors)
                    genlog('select', [prev_selector_obj.select_action, prev_selector_obj.selectors], uiobj)

                calling = try_call(self.obj, action, *args, **kwargs)
                ret = self.__class__(calling, self)
                ret.selectors = args, kwargs if args else kwargs
                ret.select_action = action
                return ret

        # 其他操作的log记录
        action, params = None, None
        if args or kwargs:
            last_log = list(args) or kwargs.values()
        else:
            last_log = []
        if len(action_stack) >= 3 and action_stack[-3] in TERTIARY_ACTION:
            taction = TERTIARY_ACTION[action_stack[-3]]
            if action_stack[-2] in taction:
                saction = taction[action_stack[-2]]
                if action_stack[-1] in saction:
                    action = action_stack[-3]
                    params = action_stack[-2:] + last_log
        if len(action_stack) >= 2 and action_stack[-2] in SECONDARY_ACTIONS:
            secondary_action = SECONDARY_ACTIONS[action_stack[-2]]
            if action_stack[-1] in secondary_action:
                action = action_stack[-2]
                params = action_stack[-1:] + last_log
        if len(action_stack) >= 1 and action_stack[-1] in PRIMARY_ACTION:
            action = action_stack[-1]
            params = last_log

        if action:
            # select操作log记录
            selector_obj = self._get_selector_obj()
            uiobj = None
            if selector_obj:
                uiobj = try_getattr(selector_obj.obj, 'info', selector_obj.select_action, selector_obj.selectors)
                genlog('select', [selector_obj.select_action, selector_obj.selectors], uiobj)
            genlog(action, params, uiobj)

        if not calling:
            calling = try_call(self.obj, 'action', *args, **kwargs)
        return self.__class__(calling, self)

    def __len__(self):
        return len(self.obj)

    def __nonzero__(self):
        """ python 2 only, for python 3, please overide __bool__
        """
        return bool(self.obj)

    def __getitem__(self, item):
        return self.__class__(self.obj[item], self)

    def __iter__(self):
        objs, length = self, len(self)

        class Iter(object):
            def __init__(self):
                self.index = -1

            def next(self):
                self.index += 1
                if self.index < length:
                    return objs[self.index]
                else:
                    raise StopIteration()
            __next__ = next

        return Iter()

    def _get_selector_obj(self):
        ret = None
        if self.selectors:
            ret = self
        elif self.last_obj and self.last_obj.selectors:
            ret = self.last_obj
        elif self.last_obj and self.last_obj.last_obj and self.last_obj.last_obj.selectors:
            ret = self.last_obj.last_obj
        elif self.last_obj and self.last_obj.last_obj and self.last_obj.last_obj.last_obj and self.last_obj.last_obj.last_obj.selectors:
            ret = self.last_obj.last_obj.last_obj
        return ret

    def end(self):
        time.sleep(1)
        genlog('end', [], None)


def UiAutomator():
    if not airtest.core.main.DEVICE:
        set_serialno()
    dev = AutomatorDevice(airtest.core.main.DEVICE.serialno)
    return AutomatorWrapper(dev)
