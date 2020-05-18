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
    - Installation of Electron
    ~~~ 
        npm install electron --save-dev
        npm install -g electron 
    ~~~ 
    - Pyshell for communication with Python backend
    ~~~
        npm install python-shell
    ~~~
    - Axios for sending requests to the server from JS
    ~~~
        npm install axios
    ~~~
    - Packager to create electron build
    ~~~
        npm install electron-packager --save-dev
        npm install -g electron electron-packager
    ~~~
3. Finally to launch Electron app (see package.json for command)
    ~~~
        electron .
    ~~~ 

# Build and Test
To package an electron use electron packager:
~~~
electron-packager  ./ --platform=win32 --arch=x64 --electron-version=8.2.3  --out=electron_build --overwrite --ignore="^.*\.py" --ignore="\/node_modules" --ignore="__pycache__"
~~~

To create an executable from python use Pyinstaller.  
You may need a fresh environment for the buidl (in order to exclude unused modules from Python)
~~~
pip install --user pipenv
python -m venv D:\build_env
D:\build_env\Scripts\pip.exe install pyinstaller
D:\build_env\Scripts\pyinstaller.exe electron_backend.py --distpath python_build --workpath %TEMP% --exclude-module tkinter --onefiles
~~~

For downloader backend:
~~~
pyinstaller ..\downloader_backend.py --distpath python_build --workpath %TEMP% --exclude-module tkinter --onefile
~~~

# Project tricks
1. Make backend running even if we compile it to exe

modify python-shell to make it run exe files, also I use a trick that I say path to python is my compile python_code.exe
and my script is null, then I commented lines in python-shell where check for script length occurred
In communicator.js for the build version use:
~~~
let options = {
  mode: 'text',
  pythonPath: "resources/app/python_build/electron_backend.exe"
};
pyshell = new PythonShell(' ', options);
~~~

while for development Pyshell will grab your Python installation from env. variables. So we need only to provide a .py file path
~~~
pyshell = new PythonShell('electron_backend.py');
~~~

In order to make it run please change source of the pyshell module, comment following:
~~~
// if (scriptPath.trim().length == 0)
    // throw Error("scriptPath cannot be empty! You must give a script for python to run");
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
At this momement you can mock up input for the downloader and test following features:
- Installation test: uninstall version if exists and install new one
- Uninstallation test: only uninstallation
- Updating of EDT registry
- Cleaning temp folder after installation
- Full test including: get recent build, download, unpack, uninstall, install, update registry 