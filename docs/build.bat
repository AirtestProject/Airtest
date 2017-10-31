rmdir /S /Q _build
rmdir /S /Q all_module
xcopy ..\README.md .\ /Y
sphinx-apidoc -Me -o all_module ../airtest ../airtest/utils
make html
pause