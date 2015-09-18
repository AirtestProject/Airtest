## moa
## Developing

该项目起源于[airtest](https://github.com/netease/airtest), 是一个通过图像识别技术，操作手机App的技术

## 常用指令

	amstart(appname) # 启动一个应用

## TODO
* Use aircv instead of air-opencv
* Use adbclient instead of air-adb

## 接口说明

- set_address((host, port))

	设置adb的host和port

- set_serialno(sn)

	设置手机的序列号, 支持*匹配,如果结果是多台手机的话，会报错MoaError

		set_serialno('cff*')

- connect(url)

	使用了这个函数，就可以省去设置set_address和set_serialno了.

		connect('moa://127.0.0.1:5037/cffab*')

- set_basedir(base_dir)

	设置你的工作目录，日志，图片都会以这个基准去查找

- set_logfile(filename, inbase=True)

	设置日志文件的路径，如果inbase为true的话，日志会保存到basedir目录下

- gevent_run(func)

	用于windows或mac上的调试功能

- log(tag, data)

	data一定是需要json.dumps支持的格式才行.

- shell(cmd, shell=True)

	执行shell命令，然后返回，有点类似subprocess

		print shell('echo hello')
		# output: hello
		print shell(['echo', 'hello'], False)
		# output: hello

- pmstart(package)

	am: android manager的简称

		amstart('com.netease.moa') # 启动应用

- pmstop(package)

	强制停止应用，等同于`am force-stop <package>`

- pmclear(package)

	清空应用中的数据，等同于`pm clear <package>`

- snapshot(filename=None)

	保存手机上的截图到filename这个文件。然后返回图像的二进制内容
