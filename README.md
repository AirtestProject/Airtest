Skip to content

Pull requestsIssues
Marketplace
Explore

 
 
Learn Git and GitHub without any code!
Using the Hello World guide, you’ll start a branch, write comments, and open a pull request.
Read the guide

 Used by 
33
 Watch 
185
 Star3.1k
 Fork
474
AirtestProject/Airtest
 Code Issues 131 Pull requests 0 Projects 0 Wiki Security Insights
You’re editing a file in a project you don’t have write access to. We’ve created a fork of this project for you to commit your proposed changes to. Submitting a change to this file will write it to a new branch in your fork, so you can send a pull request.
Airtest/Cancel
 Edit file  Preview changes
           
             
Spaces
 
Tabs
           
                    
             
2
 
4
 
8
           
                    
             
No wrap
 
Soft wrap
           
         



1
# Airtest &middot; [![Build status](https://travis-ci.org/AirtestProject/Airtest.svg?branch=master)](https://travis-ci.org/AirtestProject/Airtest)
2
​
3
**Cross-Platform UI Automation Framework for Games and Apps**
4
​
5
**跨平台的UI自动化框架，适用于游戏和App** （[中文版点这里](./README_zh.md)）
6
​
7
​
8
![image](./demo.gif)
9
​
10
​
11
## Features
12
​
13
*   **Write Once, Run Anywhere:** Airtest provides cross-platform APIs, including app installation, simulated input, assertion and so forth. Airtest uses image recognition technology to locate UI elements so that you can automate games and apps without injecting any code. 
14
​
15
*   **Fully Scalable:** Airtest cases can be easily run on large device farms, using command-line or python API. HTML reports with detailed info and screen recording allow you to quickly locate failure points. NetEase builds [Airlab](https://airlab.163.com/) on top of Airtest Project.
16
​
17
*   **AirtestIDE:** AirtestIDE is an out of the box GUI tool that helps to create and run cases in a user-friendly way. AirtestIDE supports a complete automation workflow: ``create -> run -> report``.
18
​
19
*   **Poco:** [Poco](https://github.com/AirtestProject/Poco) adds the ability to directly access object(UI widget) hierarchy across the major platforms and game engines. it allows writing instructions in Python, to achieve more advanced automation.
20
​
21
Get started from [airtest homepage](http://airtest.netease.com/)
22
​
23
#### [Supported Platforms](./docs/wiki/platforms.md)
24
​
25
| | | | | | | | |
26
|-|-|-|-|-|-|-|-|
27
[Android](http://airtest.netease.com/docs/en/1_quick_start/2_test_with_Android_device.html) |[Emulator](./docs/wiki/platforms.md#android-emulator) |[iOS](https://github.com/AirtestProject/iOS-Tagent)|[Windows](http://airtest.netease.com/docs/en/1_quick_start/4_get_started_with_Windows_test.html)|[Unity](http://airtest.netease.com/docs/en/1_quick_start/1_how_to_write_the_first_script_for_your_game.html)|Cocos2dx|Egret|[WeChat](http://airtest.netease.com/blog/tutorial/WechatSmallProgram/)| [web](http://airtest.netease.com/docs/en/1_quick_start/5_get_started_with_web_test.html)
28
​
29
## Installation
30
​
31
Use `pip` to install Airtest python library. 
32
​
33
```Shell
34
pip install -U airtest
35
```
36
​
37
On MacOS/Linux platform, you need to grant adb execute permission.
38
​
39
```Shell
40
# for mac
41
cd {your_python_path}/site-packages/airtest/core/android/static/adb/mac
42
# for Linux
43
# cd {your_python_path}/site-packages/airtest/core/android/static/adb/linux
44
chmod +x adb
45
```
46
​
47
Download AirtestIDE from our [homepage](http://airtest.netease.com/) if you need to use the GUI tool.
48
​
49
​
50
## Documentation
51
​
52
You can find the complete Airtest documentation on [readthedocs](http://airtest.readthedocs.io/).
53
​
54
​
55
## Examples
56
​
57
Airtest aims at providing platform-independent API so that you can write automated cases once and run it on multiple devices and platforms.
58
​
59
1. Using [connect_device](http://airtest.readthedocs.io/en/latest/README_MORE.html#connect-device) API you can connect to any android/iOS device or windows application.
60
1. Then perform [simulated input](http://airtest.readthedocs.io/en/latest/README_MORE.html#simulate-input) to automate your game or app.
61
1. **DO NOT** forget to [make assertions](http://airtest.readthedocs.io/en/latest/README_MORE.html#make-assertion) of the expected result. 
62
​
63
```Python
64
from airtest.core.api import *
65
​
66
# connect an android phone with adb
67
init_device("Android")
68
# or use connect_device api

Propose file change
Commit summaryOptional extended description

Propose file change Cancel
© 2019 GitHub, Inc.
Terms
Privacy
Security
Status
Help
Contact GitHub
Pricing
API
Training
Blog
About

