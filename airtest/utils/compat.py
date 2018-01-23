# coding: utf-8
import six
import sys

# Useful for very coarse version differentiation.
PY3 = sys.version_info[0] == 3

if PY3:
    from configparser import ConfigParser
    from urllib.parse import unquote, urlparse, parse_qsl
    import queue

    text_type = str
    str_class = str

    def enforce_unicode(text):
        return text

    def decode_path(path):
        return path
else:
    from ConfigParser import SafeConfigParser as ConfigParser
    import Queue as queue
    from urllib import unquote
    from urlparse import urlparse, parse_qsl

    text_type = unicode
    str_class = basestring

    def enforce_unicode(text):
        return unicode(text)

    def decode_path(path):
        return path.decode(sys.getfilesystemencoding()) if path else path
