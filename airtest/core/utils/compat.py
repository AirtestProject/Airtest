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
