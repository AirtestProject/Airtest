import sys
from setuptools import setup, find_packages
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]
if sys.platform != "win32":
    reqs.remove('pywinauto')


setup(
    name='airtest',
    version='1.0.2',
    author='Netease Games',
    author_email='gzliuxin@corp.netease.com',
    description='UI Test Automation Framework for Games and Apps',
    long_description='UI Test Automation Framework for Games and Apps, present by NetEase Games',
    url='https://github.com/AirtestProject/Airtest',
    license='Apache License 2.0',
    keywords=['game', 'automation', 'test', 'android', 'windows', 'opencv'],
    packages=find_packages(exclude=['cover', 'examples', 'tests', 'dist']),
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
    classifiers=[
        'Programming Language :: Python :: 2.7',
    ],
)
