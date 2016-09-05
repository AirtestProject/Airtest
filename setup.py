from setuptools import setup, find_packages


setup(
    name='airtest',
    version='0.0.4',
    author='Netease Game',
    author_email='gzliuxin@corp.netease.com',
    description='automated test package',
    long_description='automated test package from Netease Game',
    url='http://git-qa.gz.netease.com/gzliuxin/airtest',
    license='MIT',
    keywords=['automation', 'test', 'android', 'opencv'],
    packages=find_packages(exclude=['cover', 'examples', 'tests', 'dist']),
    package_data={
        'android_deps': ["*.apk", "airtest/core/libs", "airtest/core/adb"],
        'html_statics': ["moa/report"]
    },
    install_requires=[
        'requests',
        'Jinja2',
        'Pillow',
        'AxmlParserPY',
    ],
    classifiers=[
        'Programming Language :: Python :: 2.7',
    ],
)
