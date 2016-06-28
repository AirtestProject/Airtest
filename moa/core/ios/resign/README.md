### 本目录中存放重签是所需要的授权和条款文件

1. development_test.mobileprovision
2. entitlements.plist

第一个文件需要从apple官网上，利用重签使用的开发者账号生成，然后下载。
第二个文件可以自行编写，内容大致如下

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>application-identifier</key>
	<string>TeamID.appid</string>
	<key>com.apple.developer.team-identifier</key>
	<string>TeamID</string>
	<key>get-task-allow</key>
	<true/>
</dict>
</plist>
```

其中TeamID与appid需要和provision文件中相应的字段适配。
get-task-allow需要设为true，那么重签后的应用就可以通过debugserver启动。