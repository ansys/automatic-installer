# Description 
Current project serves to help in automation of Ansys Internal build download and installation processes.
This software is going to replace manual operations required by engineers to download and install Beta Version of 
Ansys Electronics Desktop, Ansys Workbench and Ansys License Manager. 

Two modes are possible: 
1. Partially automated: user installs build by clicking "Install Now" button
2. Fully automated: scheduled auto-update at specific days and time without any user interaction

User can install builds either from one of available Ansys Artifactories (requires VPN or Ansys Network) or 
from Ansys Sharepoint (no VPN)

# Ansys Build Downloader Installation
You can download latest version of Ansys Beta Build Installer from 
[GitHub Releases](https://github.com/ansys/pre-release-installer/releases).
If you have any version of Ansys Build Downloader already installed it will be [auto-updated](#tool-autoupdate) on next 
launch.
![img](docs/images/ui.jpg)


User can always monitor download and installation progress on _Installation History_ panel_.
If you want to abort the process you can do it from the same page just by clicking on the row with running process.
![img](docs/images/install_history.jpg)

# Usage
Almost every menu item is supplied with tooltips to help with navigation.

There are two options as source for beta build that you can select under the Repository menu:
1. SharePoint (default): no VPN connection required
2. Ansys Artifactory (recommended for Workstations and in office machines)

To download from Artifactory you have to be on VPN and use your API key. 
Click on the "Key" button and provide your Ansys SSO password to request Artifactory API key

Once you decide the repository source, you can install software on demand by clicking _"Install Now"_ button or 
schedule installation on weekly basis by clicking _Schedule Installation_. Tool is runs in the background non-graphically. 
Once you click _Install Now_ or _Schedule Installation_ you can close the window.

If you want, you can set the following advanced settings:
1. Installation and download path
2. HPC or registry options files for Ansys Electronics Desktop
3. Select only specific products from Workbench to be installed
4. Decide to keep or delete installation package after installation


# FAQ and Features
1. If you run Ansys software (the same BETA version e.g. 2022R1), then download and installation would be skipped. 
This is done to prevent corruption of the build since during software run some files might be locked and thus can 
cause damaged package. 
2. Software will be downloaded and installed only if newer version exists in selected repository.
3. You cannot download the partial installation package of Workbench, instead, schedule installation 
    outside of your working hours.
4. Currently the tool supports only Windows OS and should be run as an elevated user (admin).


## Tool Automatic Update
 App will be autoupdated on the start of the UI  
![img](docs/images/autoupdate.jpg)

# Contribution
If you would like to contribute to the current project please do it in a way you can:
1. Submit your code changes, see [CONTRIBUTE.md](docs/CONTRIBUTE.md)
2. Open an issue (defect) on GitHub issues
3. Open user story (feature suggestion) on GitHub issues

You can always write your suggestion directly to: [Our Team](mailto:betadownloader@ansys.com)
