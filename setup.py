from setuptools import setup, find_packages


def parse_requirements(filename='requirements.txt'):
    """ load requirements from a pip requirements file. (replacing from pip.req import parse_requirements)"""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

install_reqs = parse_requirements()

setup(
    name='airtest',
    version='0.1.0',
    author='Netease Game',
    author_email='gzliuxin@corp.netease.com',
    description='Automated test framework for android/iOS/Windows',
    long_description='Automated test framework for android/iOS/Windows, present by NetEase Games',
    url='http://git-qa.gz.netease.com/gzliuxin/airtest',
    license='MIT',
    keywords=['automation', 'test', 'android', 'opencv'],
    packages=find_packages(exclude=['cover', 'examples', 'tests', 'dist', 'new_test']),
    package_data={
        'android_deps': ["*.apk", "airtest/core/android/stf_libs", "airtest/core/android/adb"],
        'html_statics': ["airtest/report"]
    },
    install_requires=install_reqs,
    classifiers=[
        'Programming Language :: Python :: 2.7',
    ],
)
