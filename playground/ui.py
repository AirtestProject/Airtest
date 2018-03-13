# coding=utf-8
__author__ = 'lxn3032'


import time
import traceback
from pprint import pprint

import airtest.cli.runner
import airtest.core.api
from airtest.core.api import set_serialno, snapshot, logwrap
from airtest.core.helper import log_in_func,G
from uiautomator import AutomatorDevice


__all__ = ['UiAutomator']

PRIMARY_ACTION = ['click', 'long_click', 'swipe', 'drag', 'fling', 'scroll', 'press', 'clear_text', 'set_text', 'assert']

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
        log_in_func({"name": action, 'ret': None})

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

            log_in_func({
                "cv": {"confidence": 1, "result": [x, y], "rectangle": [[l, t], [l, b], [r, b], [r, t]]},
                'ret': [x, y],
            })
    command_layer(action, params)
    log = []
    action_stack = []


def try_call(f, action, *args, **kwargs):
    try:
        return f(*args, **kwargs)
    except Exception:
        log_error(action, traceback.format_exc(), *args, **kwargs)
        raise


def try_getattr(obj, attr, action, *args, **kwargs):
    try:
        return getattr(obj, attr)
    except Exception:
        log_error(action, traceback.format_exc(), *args, **kwargs)
        raise


def log_error(action, tb, *args, **kwargs):
    logger = airtest.core.api.LOGGER
    start = time.time()
    fndata = {'name': action, 'args': args, 'kwargs': kwargs}
    logger.running_stack.append(fndata)
    fndata.update({"traceback": tb, "time_used": time.time() - start})
    logger.log("error", fndata)
    logger.running_stack.pop()


class AutomatorAssertionFail(Exception):
    pass


class AutomatorWrapper(object):
    def __init__(self, obj, parent=None, assertion=None):
        super(AutomatorWrapper, self).__init__()
        self.obj = obj
        self.parent = parent  # prev layer obj
        self.selectors = None
        self.select_action = None
        self.assertion = assertion

    def __getattr__(self, action):
        global log, action_stack

        assertion = None
        if action.startswith('assert_not_'):
            assertion = 'assert_not_'
            action = action[len(assertion):]
        elif action.startswith('assert_'):
            assertion = 'assert_'
            action = action[len(assertion):]

        important = True
        is_key_action = False
        if action in PRIMARY_ACTION:
            is_key_action = True
        if action in QUERY_ACTION and not assertion:
            important = False
        if important:
            action_stack.append(action)
            if is_key_action:
                log.append({'primary-action': action})
            else:
                log.append({'action': action})
        

        attr = getattr(self.obj, action)
        if callable(attr) or assertion:
            return self.__class__(attr, self, assertion=assertion)
        else:
            return attr

    def __call__(self, *args, **kwargs):
        global log, action_stack
        calling = None

        # handle assertion expr
        assert_value = False if self.assertion == 'assert_not_' else True
        if self.assertion:
            action = action_stack[-1]
            assert_result = self.obj == assert_value
            prev_selector_obj = self._get_selector_obj()

            # 必须预先判断所选对象是否存在，不存在的对象调用info属性时会抛出uiautomator.UiObjectNotFoundException
            # 因为即使是assert_not_checked时，也是可以获取对象info的
            if prev_selector_obj.obj.exists:
                uiobj = prev_selector_obj.obj.info
            else:
                uiobj = None
            assert_action = self.assertion + action
            genlog('assert', [assert_action, prev_selector_obj.selectors, assert_result] + list(args), uiobj)
            if not assert_result:
                try:
                    raise AutomatorAssertionFail('assert failed of {}, require {}, got {}'.format(assert_action, assert_value, self.obj))
                except AutomatorAssertionFail:
                    log_error('assert', traceback.format_exc(), assert_action, prev_selector_obj.selectors, assert_result, *args, **kwargs)
                    raise
            return None

        # handle selector expr
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
                ret.selectors = (args, kwargs) if args else kwargs
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
        """ python 2 only, for python 3, please override __bool__
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
        # 下面的is not None的判断方法有点特殊
        # 因为该类实现了bool隐式转换接口，如果不这样判断的话，在and表达式返回时，还会自动bool隐式转换一次
        # 导致条件判断非预期
        ret = None
        if self.selectors:
            ret = self
        elif (self.parent and self.parent.selectors) is not None:
            ret = self.parent
        elif (self.parent and self.parent.parent and self.parent.parent.selectors) is not None:
            ret = self.parent.parent
        elif (self.parent and self.parent.parent and self.parent.parent.parent and self.parent.parent.parent.selectors) is not None:
            ret = self.parent.parent.parent
        return ret

    def end(self):
        time.sleep(1)
        genlog('end', [], None)


def UiAutomator():
    current_device = airtest.cli.runner.device()
    if not current_device:
        set_serialno()
    current_device = airtest.cli.runner.device()
    dev = AutomatorDevice(current_device.serialno)
    return AutomatorWrapper(dev)
