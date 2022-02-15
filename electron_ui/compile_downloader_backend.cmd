@echo OFF
:: check for admin permission
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO You should run as administrator!
    exit
)

pushd ..

:: create python virtual environment
python -m pip install --user pipenv
if not exist venv_dev (
    python -m venv venv_dev
)

:: activate virtual environment only via .bat
set act_bat=venv_dev\Scripts\activate.bat
if not exist %act_bat% (
    echo %act_bat% doesn't exist
    exit 2
)
call %act_bat%

python -m pip install -r requirements.txt

:: NOTE: --noconsole suppresses all the output from terminal, but you can redirect output to the file
pyinstaller downloader_backend.py --distpath electron_ui\python_build --workpath %TEMP% --exclude-module tkinter --onefile --noconsole --hidden-import plyer.platforms.win.notification

IF exist electron_ui\dist (
	Xcopy /E /I /Y electron_ui\python_build  electron_ui\dist\win-unpacked\resources\app.asar.unpacked\python_build 
) ELSE (
	echo No electron dist folder
)
call venv\Scripts\deactivate.bat
popd