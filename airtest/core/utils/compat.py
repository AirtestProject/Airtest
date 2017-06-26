# coding: utf-8
import six
import sys

# Useful for very coarse version differentiation.
PY3 = sys.version_info[0] == 3

if PY3:
    from configparser import ConfigParser
    from urllib.parse import unquote
    import queue

    text_type = str
    str_class = str

    def enforce_unicode(text):
        return text
else:
    from ConfigParser import SafeConfigParser as ConfigParser
    import Queue as queue
    from urllib import unquote

    text_type = unicode
    str_class = basestring

    def enforce_unicode(text):
        return unicode(text)

# get apk information by this class
class apkparser(object):

    @staticmethod
    def apk(apk_path):
        if PY3:
            from pyaxmlparser import APK
        else:
            from axmlparserpy.apk import APK
        return APK(apk_path)

    @classmethod
    def version(cls, apk_path):
        if PY3:
            v = cls.apk(apk_path).version_code
        else:
            v = cls.apk(apk_path).androidversion_code
        return int(v)

    @classmethod
    def packagename(cls, apk_path):
        if PY3:
            return cls.apk(apk_path).package
        else:
            return cls.apk(apk_path).get_package()
