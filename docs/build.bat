rmdir /S /Q all_module
sphinx-apidoc -Me -o all_module ../airtest ../airtest/utils
make html
pause