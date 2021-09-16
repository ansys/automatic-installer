:: run black styling on tests
black -l 120 .

pushd ..\..\
call venv\scripts\activate.bat
:: run unittests with coverage
coverage run --omit=**\tests\*,**\venv\*,iss_templates.py -m unittest tests.unittests.test_backend
coverage html

:: open report in browser
start htmlcov\index.html
popd