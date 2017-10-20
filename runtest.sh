rm -r cover
rm .coverage
python -m nose tests -s -e \w*.owl --with-coverage --cover-package ./airtest --cover-html --cover-inclusive
open cover/index.html

