pyinstaller ..\downloader_backend.py --distpath python_build --workpath %TEMP% --exclude-module tkinter --onefile --noconsole --hidden-import plyer.platforms.win.notification

Xcopy /E /I /Y python_build  C:\git\BETA_downloader\electron_ui\dist\win-unpacked\resources\app.asar.unpacked\python_build 