# coding: utf-8
import os
import sys
import string
from shlex import shlex
from airtest.core.utils.compat import ConfigParser, text_type


class UndefinedValueError(Exception):
    pass


class Undefined(object):
    """
    Class to represent undefined type.
    """
    pass


# Reference instance to represent undefined values
undefined = Undefined()


class Config(object):
    """
    Handle .env file format used by Foreman.
    """
    _BOOLEANS = {'1': True, 'yes': True, 'true': True, 'on': True,
                 '0': False, 'no': False, 'false': False, 'off': False}

    def __init__(self, repository):
        self.repository = repository

    def _cast_boolean(self, value):
        """
        Helper to convert config values to boolean as ConfigParser do.
        """
        value = str(value)
        if value.lower() not in self._BOOLEANS:
            raise ValueError('Not a boolean: %s' % value)

        return self._BOOLEANS[value.lower()]

    def get(self, option, default=undefined, cast=undefined):
        """
        Return the value for option or default if defined.
        """
        if option in self.repository:
            value = self.repository.get(option)
        else:
            value = default

        if isinstance(value, Undefined):
            raise UndefinedValueError('%s option not found and default value was not defined.' % option)

        if isinstance(cast, Undefined):
            cast = lambda v: v  # nop
        elif cast is bool:
            cast = self._cast_boolean

        return cast(value)

    def __call__(self, *args, **kwargs):
        """
        Convenient shortcut to get.
        """
        return self.get(*args, **kwargs)


class RepositoryBase(object):
    def __init__(self, source):
        raise NotImplementedError

    def __contains__(self, key):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError


class RepositoryIni(RepositoryBase):
    """
    Retrieves option keys from .ini files.
    """
    SECTION = 'settings'

    def __init__(self, source):
        self.parser = ConfigParser()
        self.parser.readfp(open(source))

    def __contains__(self, key):
        return (key in os.environ or
                self.parser.has_option(self.SECTION, key))

    def get(self, key):
        return (os.environ.get(key) or
                self.parser.get(self.SECTION, key))


class RepositoryEnv(RepositoryBase):
    """
    Retrieves option keys from .env files with fall back to os.environ.
    """
    def __init__(self, source):
        self.data = {}

        for line in open(source):
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('\'"')
            self.data[k] = v

    def __contains__(self, key):
        return key in os.environ or key in self.data

    def get(self, key):
        return os.environ.get(key) or self.data[key]


class RepositoryShell(RepositoryBase):
    """
    Retrieves option keys from os.environ.
    """
    def __init__(self, source=None):
        pass

    def __contains__(self, key):
        return key in os.environ

    def get(self, key):
        return os.environ[key]


class AutoConfig(object):
    """
    Autodetects the config file and type.
    """
    SUPPORTED = {
        'settings.ini': RepositoryIni,
        '.env': RepositoryEnv,
    }

    def __init__(self, search_path=None):
        self.config = None
        self.search_path = search_path

    def _find_file(self, path):
        # look for all files in the current path
        for configfile in self.SUPPORTED:
            filename = os.path.join(path, configfile)
            if os.path.isfile(filename):
                return filename

        # search the parent
        parent = os.path.dirname(path)
        if parent and parent != os.path.sep:
            return self._find_file(parent)

        # reached root without finding any files.
        return ''

    def _load(self, path):
        # Avoid unintended permission errors
        try:
            filename = self._find_file(path)
        except Exception:
            filename = ''
        Repository = self.SUPPORTED.get(os.path.basename(filename))

        if not Repository:
            Repository = RepositoryShell

        self.config = Config(Repository(filename))

    def _caller_path(self):
        # MAGIC! Get the caller's module path.
        frame = sys._getframe()
        path = os.path.dirname(frame.f_back.f_back.f_code.co_filename)
        return path

    def __call__(self, *args, **kwargs):
        if not self.config:
            path = self.search_path or self._caller_path()
            self._load(path)

        return self.config(*args, **kwargs)


# A pré-instantiated AutoConfig to improve decouple's usability
# now just import config and start using with no configuration.
config = AutoConfig(os.environ.get("DECOUPLE_SEARCH_PATH"))


# Helpers

class Csv(object):
    """
    Produces a csv parser that return a list of transformed elements.
    """

    def __init__(self, cast=text_type, delimiter=',', strip=string.whitespace):
        """
        Parameters:
        cast -- callable that transforms the item just before it's added to the list.
        delimiter -- string of delimiters chars passed to shlex.
        strip -- string of non-relevant characters to be passed to str.strip after the split.
        """
        self.cast = cast
        self.delimiter = delimiter
        self.strip = strip

    def __call__(self, value):
        """The actual transformation"""
        transform = lambda s: self.cast(s.strip(self.strip))

        splitter = shlex(value, posix=True)
        splitter.whitespace = self.delimiter
        splitter.whitespace_split = True

        return [transform(s) for s in splitter]

