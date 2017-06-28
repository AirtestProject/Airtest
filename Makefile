.PHONY: docs

init:
	pip install pipenv
	pipenv install --dev

test_env:
# This runs all of the tests. To run an individual test, run py.test with
# the -k flag, like "py.test -k test_path_is_not_double_encoded"
	pipenv run 
	pipenv run coverage run -m nose new_test -s -e \w*.owl --with-xunit --xunit-file=unittest_env.xml

	coverage report --omit="new_test/*,airtest/report/images2gif/*,airtest/core/ios/*,airtest/core/android/emulator/*" >cov_report_env.txt
	coverage html -i --omit="new_test/*,airtest/report/images2gif/*,airtest/core/ios/*,airtest/core/android/emulator/*" -d htmlcov 
	start htmlcov/index.html

test:
	- coverage run -m nose new_test -s -e \w*.owl --with-xunit --xunit-file=unittest.xml --with-html --html-file=result.html
	coverage report --omit="new_test/*,airtest/report/images2gif/*,airtest/core/ios/*,airtest/core/android/emulator/*" >cov_report.txt
	coverage html -i --omit="new_test/*,airtest/report/images2gif/*,airtest/core/ios/*,airtest/core/android/emulator/*" -d htmlcov
	start htmlcov/index.html

test_2:
	- coverage2 run -m nose new_test -s -e \w*.owl --with-xunit --xunit-file=unittest_2.xml
	coverage2 report --omit="new_test/*,airtest/report/images2gif/*,airtest/core/ios/*,airtest/core/android/emulator/*" >cov_report_2.txt
	coverage2 html -i --omit="new_test/*,airtest/report/images2gif/*,airtest/core/ios/*,airtest/core/android/emulator/*" -d htmlcov
	start htmlcov/index.html

test_3:
	- coverage3 run -m nose new_test -s -e \w*.owl --with-xunit --xunit-file=unittest_3.xml --with-html --html-file3=result_3.html
	coverage3 report --omit="new_test/*,airtest/report/images2gif/*,airtest/core/ios/*,airtest/core/android/emulator/*" >cov_report_3.txt
	coverage3 html -i --omit="new_test/*,airtest/report/images2gif/*,airtest/core/ios/*,airtest/core/android/emulator/*" -d htmlcov
	start htmlcov/index.html

build_egg:
# do build egg to checking is something wrong ,default python version
	python setup.py bdist_egg

build_egg_2:
# do build egg to checking is something wrong ,python 2
	py -2 setup.py bdist_egg

build_egg_3:
# do build egg to checking is something wrong ,python 3
	py -3 setup.py bdist_egg

build_egg_env:
# do build egg to checking is something wrong ,env
	pipenv run python setup.py bdist_egg

install:
	pip install -e .

install_2:
# install in python 2
	pip2 install -e .
install_3:
# install in python 3
	pip3 install -e .
install_env:
# install in python 3
	pipenv run pip install -e .






docs:
	cd docs && make html
	@echo "Build successful! View the docs homepage at docs/_build/html/index.html"
