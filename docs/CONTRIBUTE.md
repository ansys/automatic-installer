
# Getting Started
Current software is build on [Electron framework](https://www.electronjs.org/)  
Python is used as backend to download the software (compiled to .exe to avoid Python dependency)

In order to work with project you need to 
1. Install [npm (node package manager)](https://nodejs.org/en/download/)
2. Open PowerShell/CMD in project folder and run: 
    - Installation of Electron globally
        ~~~ 
        cd electron_ui
        npm install electron -g
        ~~~ 
    - Rest packages could be installed automatically from package.json
        ~~~
        npm install
        cd ..
        ~~~
3. Install all required Python modules
    ~~~
    python -m pip install -r requirements.txt
    ~~~
4. Compile python code to the executable (see [Test on your local machine](#Test-on-your-local-machine))
5. Finally to launch Electron app (see package.json for command)
    ~~~
    cd electron_ui     
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
cd electron_ui
python -m pip install --user pipenv
python -m venv D:\build_env
D:\build_env\Scripts\pip.exe install pyinstaller
D:\build_env\Scripts\pyinstaller.exe ..\downloader_backend.py --distpath python_build --workpath %TEMP% --exclude-module tkinter --onefile
~~~

To generate build (executable) [electron-builder](https://www.electron.build/) is used (see scripts section in package.json):
~~~
npm run build
~~~

# Distribution
Releases of the tool are published on [GitHub](https://github.com/ansys/pre-release-installer/releases).
In order to publish a release you will need a Personal Access Token to GitHub set as `GH_TOKEN` environment variable 
and then just run
~~~
npm run deploy
~~~

# SharePoint
Due to high demand of downloading from SharePoint (SP) new method was introduced that allows users to download latest 
builds from SP.

# Statistics
We collect statistics in two ways:
1. Download count for each version via 
[GitHub API](https://api.github.com/repos/ansys/pre-release-installer/releases). 
2. Downloads count sent from user machine. See send_statistics() function in backend. This will send data to the 
[InfluxDB](https://www.influxdata.com/). 
To postprocess data [Grafana](https://grafana.com/) is used. To open Grafana use in web browser http://ottbld02:3000 and
connect to the datasource of InfluxDB.
For more info read [server.md](server.md)

Note: do not forget to set **Null value: null as zero** for a plot

# Testing
For testing you can use python _unittest_ module.  
Use _test_downloader_backend.py_ script from _unittests_ folder and _input_ folder to mock up input parameters.  
At this moment you can mock up input for the downloader and test following features:
- Download test: download specified version
- History test: verify that installation history is written
- Installation test: uninstall version if exists and install new one
- Uninstallation test: only uninstallation
- Updating of Electronics Desktop registry
- Cleaning temp folder after installation
- Full test including: get recent build, download, unpack, uninstall, install, update registry, update of history