rm -r cover
rm .coverage
python -m nose tests -s -e \w*.air --with-coverage --cover-package ./airtest --cover-html  #  --cover-inclusive
open cover/index.html

