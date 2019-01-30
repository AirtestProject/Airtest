echo "CANNOT BUILD WIN MODULES ON MAC"
rem rm -r all_module
set SPHINXOPTS=-D language=zh_CN
sphinx-apidoc -Me -o all_module ../airtest ../airtest/utils
./make.bat html
start _build/html/index.html
