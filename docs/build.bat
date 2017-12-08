rmdir /S /Q _build
rmdir /S /Q all_module
xcopy ..\README.rst .\ /Y
sphinx-apidoc -Me -o all_module ../airtest ../airtest/utils
make html
make -e SPHINXOPTS="-D language='zh_CN'" html_cn
pause