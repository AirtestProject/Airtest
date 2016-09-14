rd /s /q cover
del .coverage
nosetests tests -s -e \w*.owl --with-coverage --cover-package ./airtest --cover-html
pause
start cover/index.html

