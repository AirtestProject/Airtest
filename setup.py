from setuptools import setup, find_packages
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]


setup(
    name='airtest',
    version='0.1.5',
    author='Netease Game',
    author_email='gzliuxin@corp.netease.com',
    description='Automated test framework for android/iOS/Windows',
    long_description='Automated test framework for android/iOS/Windows, present by NetEase Games',
    url='http://git-qa.gz.netease.com/gzliuxin/airtest',
    license='Apache License 2.0',
    keywords=['automation', 'test', 'android', 'opencv'],
    packages=find_packages(exclude=['cover', 'examples', 'tests', 'dist', 'new_test']),
    package_data={
        'android_deps': ["*.apk", "airtest/core/android/stf_libs", "airtest/core/android/adb"],
        'html_statics': ["airtest/report"]
    },
    include_package_data=True,
    install_requires=reqs,
    classifiers=[
        'Programming Language :: Python :: 2.7',
    ],
)
