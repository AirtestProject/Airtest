import sys
from setuptools import setup, find_packages


def parse_requirements(filename):
    """ load requirements from a pip requirements file. (replacing from pip.req import parse_requirements)"""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


reqs = parse_requirements('requirements.txt')
if sys.platform == "win32":
    reqs.append('pywin32')


setup(
    name='airtest',
    version='1.0.27',
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
    install_requires=reqs,
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
    ],
)
