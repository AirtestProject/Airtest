rmdir /S /Q all_module
sphinx-apidoc -Me -o all_module ../airtest ../airtest/report/images2gif ../airtest/core/utils ../airtest/core/android/apkparser
make html
pause