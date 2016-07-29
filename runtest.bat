rd /s /q cover
del .coverage
nosetests tests --with-coverage --cover-package ./moa --cover-html
pause
start cover/index.html

