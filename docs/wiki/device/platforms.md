

Supported Platforms 各平台支持情况
===================

## Overview



| Platforms                  | Airtest                                                      | Poco                                                         |
| -------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Android                    | √                                                            | √                                                            |
| Emulator                   | √ [model list](#android-emulator)                            | √                                                            |
| iOS                        | √ [ios-Tagent](https://github.com/AirtestProject/iOS-Tagent) | [ios-tagent](https://github.com/AirtestProject/iOS-Tagent)   |
| Windows                    | √                                                            | Not yet                                                      |
| Cocos2dx-js & Cocos2dx-lua | √                                                            | √ [integration doc](https://poco.readthedocs.io/en/latest/source/doc/integration.html#cocos2dx-lua) |
| Unity3D                    | √                                                            | √ [integration doc](https://poco-chinese.readthedocs.io/en/latest/source/doc/integration.html#unity3d) |
| Egret                      | √                                                            | √ [integration doc](https://github.com/AirtestProject/Poco-SDK/tree/master/Egret) |
| WeChat Applet & Webview    | √                                                            | √ [tutorial](https://airtest.doc.io.netease.com/en/IDEdocs/poco_framework/poco_webview/) [中文版本](https://airtest.doc.io.netease.com/IDEdocs/poco_framework/poco_webview/) |
| Netease engines            | √                                                            | √ [tutorial](http://git-qa.gz.netease.com/maki/netease-ide-plugin) |
| Other engines              | √                                                            | √ [implementation doc](https://poco-chinese.readthedocs.io/en/latest/source/doc/implementation_guide.html) |



## Android

Currently we are compatible with **most Android phones** (2.3 <= Android <= 11) on the market, and a few special Android tablets and devices.

- If you encounter problems during the connection, please refer to the device settings of this document according to the different mobile phone manufacturers: [Some manufacturer’s device special problems](https://airtest.doc.io.netease.com/en/IDEdocs/device_connection/2_android_faq/#2)
- For MIUI 11 or above of Xiaomi mobile phone, please use `cap_method=JAVACAP` mode to connect to the phone

目前我们兼容市面上**绝大多数的Android手机**（2.3 <= Android <= 11），和少数特殊Android平板和设备。

- 如果在连接中遇到问题，请根据手机厂商的不同，查看此文档的设备设置：[部分厂商设备特殊问题](https://airtest.doc.io.netease.com/IDEdocs/device_connection/2_android_faq/#2)
- 小米手机的MIUI 11 以上版本，请使用`cap_method=JAVACAP`模式连接手机



## Android Emulator 模拟器

The following emulators have been verified, [Android Emulator Connection Guidelines](https://airtest.doc.io.netease.com/en/IDEdocs/device_connection/3_emulator_connection/)

下列模拟器都经过验证，[Android模拟器连接指引](https://airtest.doc.io.netease.com/IDEdocs/device_connection/3_emulator_connection/)

*	[夜神 Nox](https://www.yeshen.com/)
*	[网易Mumu](https://mumu.163.com/)
*	[逍遥 Memuplay](https://www.xyaz.cn/)	
*	[iTools](https://pro.itools.cn/itools1)
*	[腾讯手游助手](http://www.ttmnq.com/)	
*	[BlueStacks](https://www.bluestacks.com/)
*	AVD

附录：我们对[常见模拟器版本的适配情况](https://juejin.cn/post/6844904194118254599)测试（2020.06，随着版本更新可能失效）



## iOS

According to [iOS-Tagent](https://github.com/AirtestProject/iOS-Tagent) document, the current support situation:

以[iOS-Tagent](https://github.com/AirtestProject/iOS-Tagent)文档为准，目前的支持情况：

| xcode   | iOS    |
| ------- | ------ |
| <= 11.5 | <=13.5 |

