echo "CANNOT BUILD WIN MODULES ON MAC"
#rm -r all_module
cp ../README.md .
sphinx-apidoc -Me -o all_module ../airtest ../airtest/report/images2gif ../airtest/core/utils ../airtest/core/android/apkparser
make html
open _build/html/index.html
