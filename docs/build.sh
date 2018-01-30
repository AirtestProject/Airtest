echo "CANNOT BUILD WIN MODULES ON MAC"
#rm -r all_module
cp ../README.rst .
sphinx-apidoc -Me -o all_module ../airtest ../airtest/utils
make html
open _build/html/index.html
