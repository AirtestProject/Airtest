from setuptools import setup, find_packages
#import moa
#from moa import __version__

VERSION = '0.0.1' #__version__

setup(
    name='air-moa',
    version=VERSION,
    author='codeskyblue@gmail.com(hzsunshx)',
    # author_email='',
    description='Android auto test package',
    # long_description=long_description,
    url='https://git-qa.gz.netease.com/airtest-projects/moa.git',
    # download_url='https://github.com/Cal-CS-61A-Staff/ok/releases/download/v{}/ok'.format(VERSION),

    license='MIT',
    keywords=['mobile', 'android', 'opencv'],
    packages=find_packages(),##include=[
        #'client',
        #'client.*',
    #]),
    #package_data={
    #    'client': ['config.ok'],
    #},
    # install_requires=[],
    entry_points={
        'console_scripts': [
            'moatool=moa.moatool:main',
        ],
    },
    install_requires=[
        'requests',
    ],
    classifiers=[
        'Programming Language :: Python :: 2.7',
    ],
)
