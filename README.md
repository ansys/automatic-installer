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
Releases of the tool are published on [GitHub](https://github.com/beliaev-maksim/beta_build_downloader/releases).
In order to publish a release you will need a Personal Access Token to GitHub set as `GH_TOKEN` environment variable 
and then just run
~~~
npm run deploy
~~~

# SharePoint
Due to high demand of downloading from SharePoint (SP) new method was introduced that allows users to download latest 
builds from SP.

### Server Side for SP
We need to provide regular builds to SP. This is done via running _cron_ on CentOS machine. 
Cron runs [sharepoint_uploader.py](server/sharepoint_uploader.py) multiple times per day and python code gets new 
builds from Artifactory, uploads them SP and adds information about new build to SP List.

Secret keys configuration you can find in  [Upload To SharePoint](docs/upload_to_SharePoint.md)

To connect to SP system needs to know SP _client_id_ and _client_secret_. They are provided through environment 
variables. Also for successful download TEMP variable is required. These variables are set through 
_/home/electron/.bashrc_

Login as _electron_ user. Install cron and start it as service:
~~~
sudo yum install cronie
service crond start
chkconfig crond on
~~~

Configure cron to run every 3 hours:
~~~
crontab -l > .cron_settings
vim .cron_settings
~~~

In vim editor write:
~~~
0 */3 * * * . $HOME/.bash_profile; python3 /home/git/beta_downloader/server/sharepoint_uploader.py
~~~

Now activate cron to take this settings
~~~
crontab .cron_settings
~~~

To see emails from cron if something goes wrong:
~~~
vim /var/spool/mail/electron
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
To postprocess data [Grafana](https://grafana.com/) is used. To open Grafana use in web browser http://ottbld02:3000 and
connect to the datasource of InfluxDB.
You can use following query to create a plot:
~~~
SELECT sum("count") FROM "autogen"."downloads" WHERE $timeFilter GROUP BY time(1d), "tool"
~~~
Note: do not forget to set **Null value: null as zero** for a plot

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