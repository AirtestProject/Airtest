__version__ = "1.3.5"

import os
import sys


def get_airtest_version():
    pip_pkg_dir = os.path.join(os.path.dirname(__file__), "..", "..")
    pip_pkg_dir = os.path.abspath(pip_pkg_dir)

    return (
        'airtest {} from {} (python {})'.format(
            __version__, pip_pkg_dir, sys.version[:3],
        )
    )


def show_version():
    sys.stdout.write(get_airtest_version())
    sys.stdout.write(os.linesep)
    sys.exit()
