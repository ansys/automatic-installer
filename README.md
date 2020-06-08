# Introduction 
Current project is created to help in creation of automated flow of Ansys Internal build download.
This software is going to replace manual operations required by engineers to download and install Beta Version of 
Ansys Electronics Desktop and of Ansys Workbench.  
Two modes are possible: 
1. half automatic and user installs build only once by button click
2. scheduled autoupdate at specific days and time

# Getting Started
Current software is build on [Electron framework](https://www.electronjs.org/)  
Python is used as backend 

In order to work with project you need to 
1. Install [npm (node package manager)](https://nodejs.org/en/download/)
2. Open PowerShell/CMD in project folder and run: 
    - Installation of Electron globally
    ~~~ 
        npm install electron -g
    ~~~ 
    - Rest packages could be installed automatically from package.json
    ~~~
        npm install
    ~~~

3. Finally to launch Electron app (see package.json for command)
    ~~~
        electron .
    ~~~ 

# Build and Test
### Auto build via Azure Pipeline
Generally builds would be created during branch merge via Azure Pipeline (see configuration in azure-pipelines.yml)  

### Test on your local machine 
All commands below you run from electron_ui folder (app folder)  

First create an executable from python using Pyinstaller.  
You may need a fresh environment for the build (in order to exclude unused modules from Python)
~~~
python -m pip install --user pipenv
python -m venv D:\build_env
D:\build_env\Scripts\pip.exe install pyinstaller
D:\build_env\Scripts\pyinstaller.exe ..\downloader_backend.py --distpath python_build --workpath %TEMP% --exclude-module tkinter --onefile
~~~

To package an electron use electron packager (can be used for quick debug before building, otherwise can be skipped):
~~~
electron-packager  ./ --platform=win32 --arch=x64 --electron-version=8.2.3  --out=electron_build --overwrite --ignore="^.*\.py" --ignore="__pycache__"
~~~

To generate build (executable) (see scripts section in package.json):
~~~
npm run dist
~~~

To run the server install PM2 package
~~~
npm install pm2 -g
~~~
Then to run the server in production mode use following CMD snippet on server startup:
~~~
set PORT=1337
cd  C:\GIT\electron_server
pm2 start app.js  -x -- -prod
timeout /T 5
pm2 stop 0
timeout /T 5
pm2 delete app
timeout /T 5
pm2 start app.js  -x -- -prod
CMD /Q /K
~~~

# Contribute
Please go ahead and contribute in any way you can:
1. Submit your code changes
2. Open a defect
3. Open user story (feature)

You can always write your suggestion directly to: [Maksim Beliaev](mailto:maksim.beliaev@ansys.com)

# Testing
For testing you can use python _unittest_ module.  
Use _test_downloader_backend.py_ script from _unittests_ folder and _input_ folder to mock up input parameters.  
At this moment you can mock up input for the downloader and test following features:
- Installation test: uninstall version if exists and install new one
- Uninstallation test: only uninstallation
- Updating of EDT registry
- Cleaning temp folder after installation
- Full test including: get recent build, download, unpack, uninstall, install, update registry 