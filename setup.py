import os
import sys
import codecs
import pkg_resources
from setuptools import setup, find_packages


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            # __version__ = "1.x.x"
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


def parse_requirements(filename):
    """ load requirements from a pip requirements file. (replacing from pip.req import parse_requirements)"""
    lineiter = (line.strip() for line in open(filename))
    reqs = [line for line in lineiter if line and not line.startswith("#")]
    if sys.platform == "win32":
        reqs.append('pywin32')
    if sys.version_info[:2] <= (3, 6) and \
            "opencv-contrib-python" not in [d.project_name for d in pkg_resources.working_set]:
        # If py<=3.6 and opencv-contrib-python has not been installed, install version==3.2.0.7
        reqs.remove("opencv-contrib-python")
        reqs.append("opencv-contrib-python==3.2.0.7")
    return reqs


setup(
    name='airtest',
    version=get_version("airtest/utils/version.py"),
    author='Netease Games',
    author_email='gzliuxin@corp.netease.com',
    description='UI Test Automation Framework for Games and Apps on Android/iOS/Windows/Linux',
    long_description='UI Test Automation Framework for Games and Apps on Android/iOS/Windows, present by NetEase Games',
    url='https://github.com/AirtestProject/Airtest',
    license='Apache License 2.0',
    keywords=['automation', 'automated-test', 'game', 'android', 'ios', 'windows', 'linux'],
    packages=find_packages(exclude=['cover', 'playground', 'tests', 'dist']),
    package_data={
        'android_deps': ["*.apk", "airtest/core/android/static"],
        'html_statics': ["airtest/report"]
    },
    include_package_data=True,
    install_requires=parse_requirements('requirements.txt'),
    extras_require={
        'tests': [
            'nose',
        ],
        'docs': [
            'sphinx',
            'recommonmark',
            'sphinx_rtd_theme',
            'mock',
        ]},
    entry_points="""
    [console_scripts]
    airtest = airtest.cli.__main__:main
    """,
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
