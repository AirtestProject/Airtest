rd /s /q cover
del .coverage
python -m nose tests -s -e \w*.owl --with-coverage --cover-package ./airtest --cover-html --cover-inclusive
pause
start cover/index.html

