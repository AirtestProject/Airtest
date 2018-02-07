echo "CANNOT BUILD WIN MODULES ON MAC"
rem rm -r all_module
xcopy ..\README.rst . /y /Q
sphinx-apidoc -Me -o all_module ../airtest ../airtest/utils
./make.bat html
start _build/html/index.html
