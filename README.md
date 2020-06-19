# Introduction 
Current project is created to help in creation of automated flow of Ansys Internal build download.
This software is going to replace manual operations required by engineers to download and install Beta Version of 
Ansys Electronics Desktop and of Ansys Workbench.  
Two modes are possible: 
1. half automatic and user installs build only once by button click
2. scheduled autoupdate at specific days and time

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

# Distribution
For distribution [Electron Release Server (ERS)](https://github.com/ArekSredzki/electron-release-server) is used.
My fork of the server you can find in the same project in Azure [Electron Release Server Fork](https://dev.azure.com/EMEA-FES-E/AnsysSoftwareManagement/_git/Electron_Release_Server).

To handle releases [PostgreSQL](https://www.postgresql.org/) database is used. See ERS docs how to configure it.

In the app autoupdate is inbuilt for the purpose of distribution of patches and new versions to the existing users. On 
start of the app it will connect to OTTBLD01:1337 machine and verify if new version of downloader exists. 

To run the server install PM2 package
~~~
npm install pm2 -g
~~~
Then to run the release server in production mode use following CMD snippet on server startup:
~~~
set PORT=1337
cd  C:\GIT\electron_server
pm2 start app.js  -x -- -prod
pm2 save
~~~

# Statistics
We collect statistics in two ways:
1. Download count for each version via ERS. To see stats you may open either _PostgreSQL_ database directly or 
download [pgAdmin](https://www.pgadmin.org/) that will connect to database and you will be able to see tables in UI.
After it is opened in web browser connect to database using admin password.  
Navigate in the menu to:  Servers -> PostgreSQL 9.5 -> Databases -> electron_release_server -> Schemas -> Public -> 
Tables -> RMB on Asset -> View/Edit Data -> All Rows
2. Downloads count sent from user machine. See send_statistics() function in backend. This will send data to the 
[InfluxDB](https://www.influxdata.com/). To run the server just download official installation package and 
use config file from our [InfluxDB](https://dev.azure.com/EMEA-FES-E/AnsysSoftwareManagement/_git/InfluxDB) repo. 
To postprocess data [Grafana](https://grafana.com/) is used. To open Grafana use in web browser http://ottbld01:3000 and
connect to the datasource of InfluxDB.
You can use following query to create a plot:
~~~
SELECT sum("count") FROM "autogen"."downloads" WHERE $timeFilter GROUP BY time(1d), "tool"
~~~
Note: do not forget to set **Null value: null as zero** for a plot

# Auto startup
### Electron release server
Since ERS is launched through PM2 then we need to start through PM2 startup manager:
1. we need to prepare PM2 environment (if not done before)
~~~
    set PORT=1337
    cd  C:\GIT\electron_server
    pm2 start app.js  -x -- -prod
    pm2 save
~~~
2. Install pm2-windows-service and fix the bug through:
~~~
npm install -g pm2-windows-service
npm install -g npm-check-updates

cd %USERPROFILE%\AppData\Roaming\npm\node_modules\pm2-windows-service
ncu inquirer -u
npm install
~~~
3. Create a folder _C:\GIT\.pm2_ and set it to PATH and PM2_HOME environment variables
4. Run in command windows
~~~
pm2-service-install -n PM2


? Perform environment setup (recommended)? Yes
? Set PM2_HOME? Yes
? PM2_HOME value (this path should be accessible to the service user and
should not contain any “user-context” variables [e.g. %APPDATA%]): C:\GIT\.pm2\
? Set PM2_SERVICE_SCRIPTS (the list of start-up scripts for pm2)? No
? Set PM2_SERVICE_PM2_DIR (the location of the global pm2 to use with the service)? [recommended] Yes
? Specify the directory containing the pm2 version to be used by the
service C:\USERS\<USER>\APPDATA\ROAMING\NPM\node_modules\pm2\index.js
~~~

### InfluxDB
To run database on startup download: [NSSM - the Non-Sucking Service Manager](https://nssm.cc/download)  
~~~
nssm install influxDB
~~~
This will open settings window:
1. Path C:\GIT\InfluxDB\influxdb-1.8.0-1\influxd.exe
2. Arguments: -config "C:\GIT\InfluxDB\influxdb-1.8.0-1\influxdb.conf"
3. Click Install Service

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
- Download test: download specified version
- History test: verify that installation history is written
- Installation test: uninstall version if exists and install new one
- Uninstallation test: only uninstallation
- Updating of Electronics Desktop registry
- Cleaning temp folder after installation
- Full test including: get recent build, download, unpack, uninstall, install, update registry, update of history