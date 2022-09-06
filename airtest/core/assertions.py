"""
Assertions for Airtest
"""

from airtest.core.helper import logwrap
from airtest.core.cv import loop_find
from airtest.core.error import TargetNotFoundError
from airtest.core.settings import Settings as ST


@logwrap
def assert_exists(v, msg=""):
    """
    Assert target exists on device screen

    :param v: target to be checked
    :param msg: short description of assertion, it will be recorded in the report
    :raise AssertionError: if assertion fails
    :return: coordinates of the target
    :platforms: Android, Windows, iOS
    :Example:

        >>> assert_exists(Template(r"tpl1607324047907.png"), "assert exists")

    """
    try:
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT, threshold=ST.THRESHOLD_STRICT or v.threshold)
        return pos
    except TargetNotFoundError:
        raise AssertionError("%s does not exist in screen, message: %s" % (v, msg))


@logwrap
def assert_not_exists(v, msg=""):
    """
    Assert target does not exist on device screen

    :param v: target to be checked
    :param msg: short description of assertion, it will be recorded in the report
    :raise AssertionError: if assertion fails
    :return: None.
    :platforms: Android, Windows, iOS
    :Example:

        >>> assert_not_exists(Template(r"tpl1607324047907.png"), "assert not exists")
    """
    try:
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT_TMP)
        raise AssertionError("%s exists unexpectedly at pos: %s, message: %s" % (v, pos, msg))
    except TargetNotFoundError:
        pass


@logwrap
def assert_equal(first, second, msg="", snapshot=True):
    """
    Assert two values are equal

    :param first: first value
    :param second: second value
    :param msg: short description of assertion, it will be recorded in the report
    :raise AssertionError: if assertion fails
    :return: None
    :platforms: Android, Windows, iOS
    :Example:

        >>> assert_equal(1, 1, msg="assert 1==1")
    """
    # print(3444444444, snapshot)
    if first != second:
        raise AssertionError("%s and %s are not equal, message: %s" % (first, second, msg))


@logwrap
def assert_not_equal(first, second, msg="", snapshot=True):
    """
    Assert two values are not equal

    :param first: first value
    :param second: second value
    :param msg: short description of assertion, it will be recorded in the report
    :raise AssertionError: if assertion
    :return: None
    :platforms: Android, Windows, iOS
    :Example:

        >>> assert_not_equal(1, 2, msg="assert 1!=2")
    """
    if first == second:
        raise AssertionError("%s and %s are equal, message: %s" % (first, second, msg))


@logwrap
def assert_true(expr, msg="", snapshot=True):
    """
    Assert expression is True ( bool(expr) is True )
    Note that this is equivalent to bool(expr) is True and not to expr is True (use assertIs(expr, True) for the latter).

    :Example:

        >>> assert_true(1==1, msg="assert 1==1")
    """
    if bool(expr) is not True:
        raise AssertionError("expression is not True, message: %s" % msg)


@logwrap
def assert_false(expr, msg="", snapshot=True):
    """
    Assert expression is False ( bool(expr) is False )

    :Example:

        >>> assert_false(1==2, msg="assert 1!=2")
    """
    if bool(expr) is True:
        raise AssertionError("expression is not False, message: %s" % msg)


@logwrap
def assert_is(first, second, msg="", snapshot=True):
    """
    Test that first and second are the same object.

    :Example:

        >>> assert_is(1, 1, msg="assert 1 is 1")
    """
    if first is not second:
        raise AssertionError("%s is not %s, message: %s" % (first, second, msg))


@logwrap
def assert_is_not(first, second, msg="", snapshot=True):
    """
    Test that first and second are not the same object.

    :Example:

        >>> assert_is_not(1, 2, msg="assert 1 is not 2")
    """
    if first is second:
        raise AssertionError("%s is %s, message: %s" % (first, second, msg))


@logwrap
def assert_is_none(expr, msg="", snapshot=True):
    """
    Test that expr is None.

    :Example:

        >>> assert_is_none(None, msg="assert None is None")
    """
    if expr is not None:
        raise AssertionError("%s is not None, message: %s" % (expr, msg))


@logwrap
def assert_is_not_none(expr, msg="", snapshot=True):
    """
    Test that expr is not None.

    :Example:

        >>> assert_is_not_none(1, msg="assert 1 is not None")
    """
    if expr is None:
        raise AssertionError("%s is None, message: %s" % (expr, msg))


@logwrap
def assert_in(first, second, msg="", snapshot=True):
    """
    Test that first is in second.

    :Example:

        >>> assert_in(1, [1, 2], msg="assert 1 in [1, 2]")
    """
    if first not in second:
        raise AssertionError("%s is not in %s, message: %s" % (first, second, msg))


@logwrap
def assert_not_in(first, second, msg="", snapshot=True):
    """
    Test that first is not in second.

    :Example:

        >>> assert_not_in(3, [1, 2], msg="assert 3 not in [1, 2]")
    """
    if first in second:
        raise AssertionError("%s is in %s, message: %s" % (first, second, msg))


@logwrap
def assert_is_instance(obj, cls, msg="", snapshot=True):
    """
    Test that obj is an instance of cls (which can be a class or a tuple of classes, as supported by isinstance()).

    :Example:

        >>> assert_is_instance(1, int, msg="assert 1 is int")
    """
    if not isinstance(obj, cls):
        raise AssertionError("%s is not instance of %s, message: %s" % (obj, cls, msg))


@logwrap
def assert_not_is_instance(obj, cls, msg="", snapshot=True):
    """
    Test that obj is not an instance of cls.

    :Example:

        >>> assert_not_is_instance(1, str, msg="assert 1 is not str")
    """
    if isinstance(obj, cls):
        raise AssertionError("%s is instance of %s, message: %s" % (obj, cls, msg))


@logwrap
def assert_greater(first, second, msg="", snapshot=True):
    """
    Test that first is greater than second. (first > second)

    :Example:

        >>> assert_greater(2, 1, msg="assert 2 > 1")
    """
    if not first > second:
        raise AssertionError("%s is not greater than %s, message: %s" % (first, second, msg))


@logwrap
def assert_greater_equal(first, second, msg="", snapshot=True):
    """
    Test that first is greater than or equal to second. (first >= second)

    :Example:

        >>> assert_greater_equal(1, 1, msg="assert 1 >= 1")
    """
    if not first >= second:
        raise AssertionError("%s is not greater than or equal to %s, message: %s" % (first, second, msg))


@logwrap
def assert_less(first, second, msg="", snapshot=True):
    """
    Test that first is less than second. (first < second)

    :Example:

        >>> assert_less(1, 2, msg="assert 1 < 2")
    """
    if not first < second:
        raise AssertionError("%s is not less than %s, message: %s" % (first, second, msg))


@logwrap
def assert_less_equal(first, second, msg="", snapshot=True):
    """
    Test that first is less than or equal to second. (first <= second)

    :Example:

        >>> assert_less_equal(1, 1, msg="assert 1 <= 1")
    """
    if not first <= second:
        raise AssertionError("%s is not less than or equal to %s, message: %s" % (first, second, msg))