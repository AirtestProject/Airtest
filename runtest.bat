rd /s /q cover
del .coverage
nosetests tests --with-coverage --cover-package ./airtest --cover-html
pause
start cover/index.html

