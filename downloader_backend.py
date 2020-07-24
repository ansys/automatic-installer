import argparse
import datetime
import json
import logging
import os
import random
import re
import shutil
import subprocess
import traceback
import zipfile
from collections import namedtuple, OrderedDict

import psutil
import requests
import urllib3
from artifactory_du import artifactory_du
from influxdb import InfluxDBClient

import iss_templates

__author__ = "Maksim Beliaev"
__email__ = "maksim.beliaev@ansys.com"

STATISTICS_SERVER = "OTTBLD02"
STATISTICS_PORT = 8086

TIMEOUT = 90

artifactory_dict = OrderedDict([
    ('Austin', r'http://ausatsrv01.ansys.com:8080/artifactory'),
    ('Boulder', r'http://bouatsrv01:8080/artifactory'),
    ('Canonsburg', r'http://canartifactory.ansys.com:8080/artifactory'),
    ('Concord', r'http://convmartifact.win.ansys.com:8080/artifactory'),
    ('Darmstadt', r'http://darvmartifact.win.ansys.com:8080/artifactory'),
    ('Evanston', r'http://evavmartifact:8080/artifactory'),
    ('Gothenburg', r'http://gotvmartifact1:8080/artifactory'),
    ('Hannover', r'http://hanartifact1.ansys.com:8080/artifactory'),
    ('Horsham', r'http://horvmartifact1.ansys.com:8080/artifactory'),
    ('Lebanon', r'http://lebartifactory.win.ansys.com:8080/artifactory'),
    ('Lyon', r'http://lyovmartifact.win.ansys.com:8080/artifactory'),
    ('MiltonPark', r'http://milvmartifact.win.ansys.com:8080/artifactory'),
    ('Otterfing', r'http://ottvmartifact.win.ansys.com:8080/artifactory'),
    ('Pune', r'http://punvmartifact.win.ansys.com:8080/artifactory'),
    ('Sheffield', r'http://shfvmartifact.win.ansys.com:8080/artifactory'),
    ('SanJose', r'http://sjoartsrv01.ansys.com:8080/artifactory'),
    ('Waterloo', r'http://watatsrv01.ansys.com:8080/artifactory')
])


class Downloader:
    """
        Main class that operates the download and installation process:
        1. enables logs
        2. parses arguments to get settings file
        3. loads JSON to named tuple
        4. gets URL for selected version based on server
        5. downloads zip archive with BETA build
        6. unpacks it to download folder
        7. depending on the choice proceeds to installation of EDT or WB
        8. uninstalls previous build if one exists
        9. updates registry of EDT
        10. sends statistics to the server

        Performs checks:
        1. if the same build date is already installed, then do not proceed to download
        2. if some process is running from installation folder it will abort download

        Notes:
        Software attempts to download 4 times, if connection is still bad will abort
    """
    def __init__(self):
        """
        self.build_url (str): URL to the latest build that will be used to download .zip archive
        self.zip_file (str): path to the zip file on the PC
        self.target_unpack_dir (str): path where to unpack .zip
        self.product_id (str): product GUID extracted from iss template
        self.installshield_version (str): version of the InstallShield
        self.installed_product_info (str): path to the product.info of the installed build
        self.product_root_path (str): root path of Ansys Electronics Desktop/ Workbench installation
        self.product_version (str): version to use in env variables eg 202
        self.setup_exe (str): path to the setup.exe from downloaded and unpacked zip
        self.connection_attempt (int): number of attempts to download
        self.hash (str): hash code used for this run of the program
        self.pid: pid (process ID of the current Python run, required to allow kill in UI)
        """
        self.build_url = ""
        self.zip_file = ""
        self.target_unpack_dir = ""
        self.product_id = ""
        self.installshield_version = ""
        self.installed_product_info = ""
        self.product_root_path = ""
        self.product_version = ""
        self.setup_exe = ""

        self.connection_attempt = 1

        self.pid = str(os.getpid())

        self.hash = generate_hash_str()
        self.settings_folder = os.path.join(os.environ["APPDATA"], "build_downloader")
        self.check_and_make_directories(self.settings_folder)

        self.history = OrderedDict()
        self.history_file = os.path.join(self.settings_folder, "installation_history.json")
        self.get_installation_history()

        logging_file = os.path.join(self.settings_folder, "downloader.log")
        set_logger(logging_file)

        self.settings_path = self.parse_args()
        with open(self.settings_path, "r") as file:
            self.settings = json.load(file, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

        if "ElectronicsDesktop" in self.settings.version:
            self.product_version = self.settings.version[1:4]
            self.product_root_path = os.path.join(self.settings.install_path, "AnsysEM", "AnsysEM" +
                                                  self.product_version[:2] + "." + self.product_version[2:], "Win64")

            self.installed_product_info = os.path.join(self.product_root_path, "product.info")
        elif "Workbench" in self.settings.version:
            self.product_root_path = os.path.join(self.settings.install_path, "ANSYS Inc", self.settings.version[:4])

    def run(self):
        """
        Function that executes the download-installation process
        :return: None
        """
        try:
            self.check_and_make_directories(self.settings.install_path, self.settings.download_path)
            self.check_process_lock()
            self.get_build_link()
            if self.settings.force_install or not self.versions_identical():
                self.download_file()
                self.check_process_lock()  # download can take time, better to recheck again
                self.install()
                try:
                    self.send_statistics()
                except:
                    # do not really care about stats
                    pass
            else:
                raise SystemExit("Versions are up to date. If issue occurred please use force install flag")
            return
        except SystemExit as e:
            logging.error(e)
            self.update_installation_history(status="Failed", details=str(e))
        except requests.exceptions.ReadTimeout:
            self.catch_timeout()
        except requests.exceptions.ConnectionError:
            self.catch_timeout()
        except urllib3.exceptions.ProtocolError:
            self.catch_timeout()
        except urllib3.exceptions.ReadTimeoutError:
            self.catch_timeout()
        except Exception:
            logging.error(traceback.format_exc())
            self.update_installation_history(status="Failed", details="Unexpected error, see logs")
            self.send_statistics(error=traceback.format_exc())
        self.clean_temp()

    @staticmethod
    def check_and_make_directories(*paths):
        """
        Verify that installation and download path exists.
        If not tries to create a requested path
        :parameter: paths: list of paths that we need to check and create
        """
        for path in paths:
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                except PermissionError:
                    raise SystemExit(f"{path} could not be created due to insufficient permissions")

    def check_process_lock(self):
        """
        Verify if some executable is running from installation folder
        Abort installation if any process is running from installation folder
        :return: None
        """
        process_list = []
        for process in psutil.process_iter():
            try:
                if self.product_root_path in process.exe():
                    process_list.append(process.name())
            except psutil.AccessDenied:
                pass

        if process_list:
            process_list.sort(key=len)  # to fit into UI
            raise SystemExit("Following processes are running from installation directory: " +
                             f"{', '.join(process_list)}. Please stop all processes and try again")

    def versions_identical(self):
        """
        verify if version on the server is the same as installed one
        :return: (bool): False if versions are different or no version installed, True if identical
        """
        if "Workbench" in self.settings.version:
            product_installed = os.path.join(self.product_root_path, "package.id")
        else:
            product_installed = self.installed_product_info

        if os.path.isfile(product_installed):
            if "Workbench" in self.settings.version:
                with open(product_installed) as file:
                    product_version = next(file).rstrip().split()[-1]  # get first line
                    try:
                        product_version = int(product_version.split("P")[0])
                    except ValueError:
                        return False
                url = self.build_url.replace(r"/api/archive/download", "").replace(r"?archiveType=zip",
                                                                                   "") + "/package.id"
            else:
                product_version = self.get_edt_build_date(product_installed)
                url = self.build_url.split("/Electronics")[0] + "/product_windows.info"

            logging.info(f"Installed version of {self.settings.version} is {product_version}")
            logging.info(f"Request info about new package: {url}")
            new_product_version = self.get_build_info_file_from_artifactory(url)
            logging.info(f"Version on artifactory is {new_product_version}")

            if all([new_product_version, product_version]) and new_product_version <= product_version:
                return True
        return False

    def get_build_link(self):
        """
        Function that sends HTTP request to JFrog and get the list of folders with builds for Electronics Desktop and
        checks user password
        :modify: (str) self.build_url: URL link to the latest build that will be used to download .zip archive
        """
        self.update_installation_history(status="In-Progress", details=f"Search latest build URL")
        password = getattr(self.settings.password, self.settings.artifactory)

        if not self.settings.username or not password:
            raise SystemExit("Please provide username and artifactory password")

        server = artifactory_dict[self.settings.artifactory]

        with requests.get(server + "/api/repositories", auth=(self.settings.username, password),
                          timeout=TIMEOUT) as url_request:
            artifacts_list = json.loads(url_request.text)

        # catch 401 for bad credentials or similar
        if url_request.status_code != 200:
            if url_request.status_code == 401:
                raise SystemExit("Bad credentials, please verify your username and password for {}".format(
                    self.settings.artifactory))
            else:
                raise SystemExit(artifacts_list["errors"][0]["message"])

        # fill the dictionary with Electronics Desktop and Workbench keys since builds could be different
        # still parse the list because of different names on servers
        artifacts_dict = {}
        for artifact in artifacts_list:
            repo = artifact["key"]
            if "EBU_Certified" in repo:
                version = repo.split("_")[0] + "_ElectronicsDesktop"
                if version not in artifacts_dict:
                    artifacts_dict[version] = repo
            elif "Certified" in repo and "Licensing" not in repo:
                version = repo.split("_")[0] + "_Workbench"
                if version not in artifacts_dict:
                    artifacts_dict[version] = repo

        try:
            repo = artifacts_dict[self.settings.version]
        except KeyError:
            raise SystemExit(f"Version {self.settings.version} that you have specified " +
                             f"does not exist on {self.settings.artifactory}")

        if "ElectronicsDesktop" in self.settings.version:
            url = server + "/api/storage/" + repo + "?list&deep=0&listFolders=1"

            with requests.get(url, auth=(self.settings.username, password), timeout=TIMEOUT) as url_request:
                folder_dict_list = json.loads(url_request.text)['files']

            builds_dates = []
            for folder_dict in folder_dict_list:
                folder_name = folder_dict['uri'][1:]
                try:
                    builds_dates.append(int(folder_name))
                except ValueError:
                    pass

            latest_build = self.verify_remote_build_existence(server, repo, password, sorted(builds_dates))
            if not latest_build:
                raise SystemExit("Artifact does not exist")

            version_number = self.settings.version.split('_')[0][1:]
            self.build_url = f"{server}/{repo}/{latest_build}/Electronics_{version_number}_winx64.zip"
        elif "Workbench" in self.settings.version:
            self.build_url = f"{server}/api/archive/download/{repo}-cache/winx64?archiveType=zip"

        if not self.build_url:
            raise SystemExit("Cannot receive URL")

    def verify_remote_build_existence(self, server, repo, password, builds_list):
        """
        Check that folder with Electronics Desktop is not just empty (the case if artifact is not yet uploaded)
        :param server: server URL
        :param repo: repo name
        :param password: user password
        :param builds_list: list of folders with Electronics Desktop builds
        :return: latest availble folder where .zip is present
        """
        while builds_list:
            latest = builds_list.pop()
            url = f"{server}/api/storage/{repo}/{latest}"
            with requests.get(url, auth=(self.settings.username, password), timeout=TIMEOUT) as url_request:
                all_files = json.loads(url_request.text)["children"]
                for child in all_files:
                    if "Electronics" in child["uri"] and "winx" in child["uri"]:
                        return latest

    def download_file(self, recursion=False):
        """
        Downloads file in chunks and saves to the temp.zip file
        Uses url to the zip archive or special JFrog API to download Workbench folder
        :param (bool) recursion: Some artifactories do not have cached folders with Workbench  and we need recursively
        run the same function but with new_url, however to prevent infinity loop we need this arg
        :modify: (str) zip_file: link to the zip file
        """
        password = getattr(self.settings.password, self.settings.artifactory)
        url = self.build_url.replace("-cache", "") if recursion else self.build_url

        with requests.get(url, auth=(self.settings.username, password), timeout=TIMEOUT, stream=True) as url_request:
            if url_request.status_code == 404 and not recursion:
                # in HQ cached build does not exist and will return 404. Recursively start download with new url
                self.download_file(recursion=True)
                return

            self.zip_file = os.path.join(self.settings.download_path, f"temp_build_{self.settings.version}.zip")
            logging.info(f"Start download file from {url} to {self.zip_file}")

            if url_request.status_code != 200:
                raise SystemExit(f"Cannot download file. Server returned status code: {url_request.status_code}")

            try:
                file_size = int(url_request.headers['Content-Length'])
            except TypeError:
                file_size = 7e+9
            except KeyError:
                # Workbench has not content-length
                regex = re.match("(.*)/api/archive/download/(.*)/winx64", url)
                try:
                    aql_query_dict, max_depth_print = artifactory_du.prepare_aql(file="/winx64", max_depth=0,
                                                                                 repository=regex[2],
                                                                                 without_downloads="", older_than="")

                    artifacts = artifactory_du.artifactory_aql(artifactory_url=regex[1], aql_query_dict=aql_query_dict,
                                                               username=self.settings.username, password=password)

                    file_size = artifactory_du.out_as_du(artifacts, max_depth_print, human_readable=False)
                    file_size = int(file_size.strip("/"))
                    logging.info(f"Workbench real file size is {file_size}")
                except TypeError:
                    file_size = 11e+9
                except ValueError:
                    file_size = 11e+9

            percent = 0
            with open(self.zip_file, 'wb') as zip_file:
                while True:
                    chunk = url_request.raw.read(int(file_size/100))
                    if not chunk:
                        break
                    val = min(100, percent)
                    logging.info(f"Download progress: {val}%")
                    self.update_installation_history(status="In-Progress", details=f"Download progress: {val}%")
                    percent += 1
                    zip_file.write(chunk)

        if not self.zip_file:
            raise SystemExit("ZIP download failed")

        logging.info(f"File is downloaded to: {self.zip_file}")

    def install(self, local_lang=False):
        """
        Unpack downloaded zip and proceed to installation. Different executions for Electronics Desktop and Workbench
        :param local_lang: if not specified then use English as default installation language
        :return: None
        """
        self.update_installation_history(status="In-Progress", details=f"Start unpacking")
        self.target_unpack_dir = self.zip_file.replace(".zip", "")
        try:
            with zipfile.ZipFile(self.zip_file, "r") as zip_ref:
                zip_ref.extractall(self.target_unpack_dir)
        except OSError:
            raise SystemExit("No disk space available in download folder!")
        except zipfile.BadZipFile:
            raise SystemExit("Zip file is broken. Please try again later or use another artifactory.")

        logging.info(f"File is unpacked to {self.target_unpack_dir}")

        if "ElectronicsDesktop" in self.settings.version:
            self.install_edt()
        elif "Workbench" in self.settings.version:
            self.install_wb(local_lang)
        else:
            self.install_license_manager()

        self.update_installation_history(status="In-Progress", details=f"Clean temp directory")
        self.clean_temp()

        self.update_installation_history(status="Success", details="Normal completion")

    def install_edt(self):
        """
        Install Electronics Desktop. Make verification that the same version is not yet installed and makes
        silent installation
        Get Workbench installation path from environment variable and enables integration if exists.
        :return: None
        """
        self.parse_iss()
        self.uninstall_edt()

        install_iss_file = os.path.join(self.target_unpack_dir, "install.iss")
        install_log_file = os.path.join(self.target_unpack_dir, "install.log")

        integrate_wb = 0
        awp_env_var = "AWP_ROOT" + self.product_version
        if awp_env_var in os.environ:
            run_wb = os.path.join(os.environ[awp_env_var], "Framework", "bin", "Win64", "RunWB2.exe")
            if os.path.isfile(run_wb):
                integrate_wb = 1
                logging.info("Integration with Workbench turned ON")

        # the "shared files" is created at the same level as the "AnsysEMxx.x" so if installing to unique folders,
        # the Shared Files folder will be unique as well. Thus we can check install folder for license
        if os.path.isfile(os.path.join(self.settings.install_path, "AnsysEM", "Shared Files",
                                       "Licensing", "ansyslmd.ini")):
            install_iss = iss_templates.install_iss + iss_templates.existing_server
            logging.info("Install using existing license configuration")
        else:
            install_iss = iss_templates.install_iss + iss_templates.new_server
            logging.info("Install using 127.0.0.1, Otterfing and HQ license servers")

        with open(install_iss_file, "w") as file:
            file.write(install_iss.format(self.product_id, os.path.join(self.settings.install_path, "AnsysEM"),
                                          os.environ["TEMP"], integrate_wb, self.installshield_version))

        command = [f'"{self.setup_exe}"', '-s', fr'-f1"{install_iss_file}"', fr'-f2"{install_log_file}"']
        command = " ".join(command)
        self.update_installation_history(status="In-Progress", details=f"Start installation")
        logging.info(f"Execute installation")
        self.subprocess_call(command)

        self.check_result_code(install_log_file)
        self.update_edt_registry()

    def uninstall_edt(self):
        """
        Silently uninstall build of the same version
        :return: None
        """
        if not os.path.isfile(self.setup_exe):
            raise SystemExit("setup.exe does not exist")

        if os.path.isfile(self.installed_product_info):
            uninstall_iss_file = os.path.join(self.target_unpack_dir, "uninstall.iss")
            uninstall_log_file = os.path.join(self.target_unpack_dir, "uninstall.log")
            with open(uninstall_iss_file, "w") as file:
                file.write(iss_templates.uninstall_iss.format(self.product_id, self.installshield_version))

            command = [f'"{self.setup_exe}"', '-uninst', '-s', fr'-f1"{uninstall_iss_file}"',
                       fr'-f2"{uninstall_log_file}"']
            command = " ".join(command)
            logging.info(f"Execute uninstallation")
            self.update_installation_history(status="In-Progress", details=f"Uninstall previous build")
            self.subprocess_call(command)

            self.check_result_code(uninstall_log_file, False)
            em_main_dir = os.path.dirname(self.product_root_path)
            if os.path.isdir(em_main_dir):
                shutil.rmtree(em_main_dir)
        else:
            logging.info("Version is not installed, skip uninstallation")

    @staticmethod
    def check_result_code(log_file, installation=True):
        """
        Verify result code of the InstallShield log file
        :param log_file: installation log file
        :param installation: True if verify log after installation elif after uninstallation False
        :return: None
        """
        success = "New build was successfully installed" if installation else "Previous build was uninstalled"
        fail = "Installation went wrong" if installation else "Uninstallation went wrong"
        if not os.path.isfile(log_file):
            raise SystemExit(f"{fail}. Check that UAC disabled or confirm UAC question manually")

        with open(log_file) as file:
            for line in file:
                if "ResultCode=0" in line:
                    logging.info(success)
                    break
            else:
                raise SystemExit(fail)

    @staticmethod
    def get_edt_build_date(product_info_file):
        """
        extract information about Electronics Desktop build date and version
        :param product_info_file: path to the product.info
        :return: build_date, product_version
        """
        build_date = False
        if os.path.isfile(product_info_file):
            with open(product_info_file) as file:
                for line in file:
                    if "AnsProductBuildDate" in line:
                        full_build_date = line.split("=")[1].replace('"', '').replace("-", "")
                        build_date = full_build_date.split()[0]
                        break
        try:
            build_date = int(build_date)
        except ValueError:
            return False
        return build_date

    def parse_iss(self):
        """
        Open directory with unpacked build of Electronics Desktop and search for SilentInstallationTemplate.iss to
        extract product ID which is GUID hash
        :modify: self.product_id: GUID of downloaded version
        :modify: self.iss_template_content: append lines from template file
        :modify: self.setup_exe: set path to setup.exe if exists
        :modify: self.installshield_version: set version from file
        """
        default_iss_file = ""
        product_id_match = []

        for dir_path, dir_names, file_names in os.walk(self.target_unpack_dir):
            for filename in file_names:
                if "AnsysEM" in dir_path and filename.endswith(".iss"):
                    default_iss_file = os.path.join(dir_path, filename)
                    self.setup_exe = os.path.join(dir_path, "setup.exe")
                    break

        if not default_iss_file:
            raise SystemExit("SilentInstallationTemplate.iss does not exist")

        with open(default_iss_file, "r") as iss_file:
            for line in iss_file:
                if "DlgOrder" in line:
                    guid_regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                    product_id_match = re.findall(guid_regex, line)
                if "InstallShield Silent" in line:
                    self.installshield_version = next(iss_file).split("=")[1]

        if product_id_match:
            self.product_id = product_id_match[0]
            logging.info(f"Product ID is {self.product_id}")
        else:
            raise SystemExit("Unable to extract product ID")

    def install_license_manager(self):
        self.setup_exe = os.path.join(self.target_unpack_dir, "setup.exe")

        if os.path.isfile(self.setup_exe):
            install_path = os.path.join(self.settings.install_path, "ANSYS Inc")
            command = [self.setup_exe, '-silent', '-install_dir', install_path, "-lang", "en",
                       "-licfilepath", self.settings.license_file]
            self.update_installation_history(status="In-Progress", details=f"Start installation")
            logging.info(f"Execute installation")
            self.subprocess_call(command)
        else:
            raise SystemExit("No LicenseManager setup.exe file detected")

    def install_wb(self, local_lang=False):
        """
        Install Workbench to the target installation directory
        :param local_lang: if not specified then use English as default installation language
        """
        self.setup_exe = os.path.join(self.target_unpack_dir, "setup.exe")

        if os.path.isfile(self.setup_exe):
            uninstall_exe = self.uninstall_wb()

            install_path = os.path.join(self.settings.install_path, "ANSYS Inc")
            command = [self.setup_exe, '-silent', '-install_dir', install_path]
            if not local_lang:
                command += ["-lang", "en"]
            command += self.settings.wb_flags.split()

            # the "shared files" is created at the same level as the "ANSYS Inc" so if installing to unique folders,
            # the Shared Files folder will be unique as well. Thus we can check install folder for license
            if (os.path.isfile(os.path.join(install_path, "Shared Files", "Licensing", "ansyslmd.ini")) or
                    "ANSYSLMD_LICENSE_FILE" in os.environ):
                logging.info("Install using existing license configuration")
            else:
                command += ['-licserverinfo', '2325:1055:127.0.0.1,OTTLICENSE5,PITRH6LICSRV1']
                logging.info("Install using 127.0.0.1, Otterfing and HQ license servers")

            self.update_installation_history(status="In-Progress", details=f"Start installation")
            logging.info(f"Execute installation")
            self.subprocess_call(command)

            if os.path.isfile(uninstall_exe):
                logging.info("New build was installed")
            else:
                raise SystemExit("Workbench installation failed. " +
                                 f"If you see this error message by mistake please report to {__email__}")
        else:
            raise SystemExit("No Workbench setup.exe file detected")

    def uninstall_wb(self):
        """
        Uninstall Workbench if such exists in the target installation directory
        :return: uninstall_exe: name of the executable of uninstaller"""

        uninstall_exe = os.path.join(self.product_root_path, "Uninstall.exe")
        if os.path.isfile(uninstall_exe):
            command = [uninstall_exe, '-silent']
            self.update_installation_history(status="In-Progress", details=f"Uninstall previous build")
            logging.info(f"Execute uninstallation")
            self.subprocess_call(command)
            if os.path.isdir(self.product_root_path):
                shutil.rmtree(self.product_root_path)
            logging.info("Previous build was uninstalled")
        else:
            logging.info("No Workbench Uninstall.exe file detected")
        return uninstall_exe

    def get_build_info_file_from_artifactory(self, url, recursion=False):
        """
        Downloads file in chunks and saves to the temp.zip file
        Uses url to the zip archive or special JFrog API to download Workbench folder
        :param (bool) recursion: Some artifactories do not have cached folders with Workbench  and we need recursively
        run the same function but with new_url, however to prevent infinity loop we need this arg
        :param (str) url: url to the package_id file
        :return: (NoneType/str): None if some issue occurred during retrieving ID or package_id if extracted
        """
        password = getattr(self.settings.password, self.settings.artifactory)

        with requests.get(url, auth=(self.settings.username, password), timeout=TIMEOUT, stream=True) as url_request:
            if url_request.status_code == 404 and not recursion:
                # in HQ cached build does not exist and will return 404. Recursively start download with new url
                return self.get_build_info_file_from_artifactory(url.replace("-cache", ""), recursion=True)

            if url_request.status_code == 200:
                try:
                    if "Workbench" in self.settings.version:
                        first_line = url_request.text.split("\n")[0]
                        product_info = first_line.rstrip().split()[-1]
                        try:
                            product_info = int(product_info.split("P")[0])
                        except ValueError:
                            return False
                    else:
                        prod_info_file = os.path.join(os.environ["TEMP"], "new_prod.info")
                        with open(prod_info_file, "w") as file:
                            file.write(url_request.text)
                        product_info = self.get_edt_build_date(prod_info_file)
                    return product_info
                except IndexError:
                    pass
        return None

    def clean_temp(self):
        """
        Cleans downloaded zip and unpacked folder with content
        :return: None
        """
        try:
            if os.path.isfile(self.zip_file) and self.settings.delete_zip:
                os.remove(self.zip_file)
                logging.info("ZIP deleted")

            if os.path.isdir(self.target_unpack_dir):
                shutil.rmtree(self.target_unpack_dir)
                logging.info("Unpacked directory removed")
        except PermissionError:
            logging.error("Temp files could not be removed due to permission error")

    def update_edt_registry(self):
        """
        Update Electronics Desktop registry based on the files in the HPC_Options folder that are added from UI
        :return: None
        """
        hpc_folder = os.path.join(self.settings_folder, "HPC_Options")

        update_registry_exe = os.path.join(self.product_root_path, "UpdateRegistry.exe")
        productlist_file = os.path.join(self.product_root_path, "config", "ProductList.txt")

        with open(productlist_file) as file:
            product_version = next(file).rstrip()  # get first line

        self.update_installation_history(status="In-Progress", details=f"Update registry")
        if os.path.isdir(hpc_folder):
            for file in os.listdir(hpc_folder):
                if ".acf" in file:
                    options_file = os.path.join(hpc_folder, file)
                    command = [update_registry_exe, '-ProductName', product_version, '-FromFile', options_file]
                    logging.info(f"Update registry")
                    self.subprocess_call(command)

    def update_installation_history(self, status, details):
        """
        Update ordered dictionary with new data and write it to the file
        :param status: Failed | Success | In-Progress (important, used in JS)
        :param details: Message for details field
        :return:
        """
        self.get_installation_history()  # in case if file was deleted during run of installation
        time_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        shorten_path = self.settings_path.replace(os.environ["APPDATA"], "%APPDATA%")
        self.history[self.hash] = [
            status, self.settings.version, time_now, shorten_path, details, self.pid
        ]
        with open(self.history_file, "w") as file:
            json.dump(self.history, file, indent=4)

    def get_installation_history(self):
        """
        Read a file with installation history
        create a file if does not exist
        :return: OrderedDict with history or empty in case if file was deleted during run of installation
        """
        if os.path.isfile(self.history_file):
            try:
                with open(self.history_file) as file:
                    self.history = json.load(file, object_pairs_hook=OrderedDict)
            except json.decoder.JSONDecodeError:
                return
        else:
            self.history = OrderedDict()

    def catch_timeout(self):
        """
        On timeout error try to restart the download. If timeout more than 3 times, then abort
        :return: None
        """
        total_attempts = 4
        self.connection_attempt += 1
        if self.connection_attempt <= total_attempts:
            logging.warning(f"Timeout on connection, attempt: {self.connection_attempt}/{total_attempts}")
            self.run()
        else:
            error = (f"Timeout on connection, please verify that you are on VPN, your connection is stable " +
                     f"and username and password for {self.settings.artifactory} are correct. " +
                     f"Number of attempts: {total_attempts}/{total_attempts}")
            logging.error(error)
            self.update_installation_history(status="Failed", details=str(error))

    def send_statistics(self, error=None):
        """
        Send usage statistics to the database.
        Collect username, time, version and software installed
        in case of crash send also crash data
        :parameter: error: error message of what went wrong
        :return: None
        """
        client = InfluxDBClient(host=STATISTICS_SERVER, port=STATISTICS_PORT)
        db_name = "downloads" if not error else "crashes"
        client.switch_database(db_name)

        version, tool = self.settings.version.split("_")
        time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        json_body = [
            {
                "measurement": db_name,
                "tags": {
                    "username": self.settings.username,
                    "version": version,
                    "tool": tool,
                    "artifactory": self.settings.artifactory
                },
                "time": time,
                "fields": {
                    "count": 1
                }
            }
        ]

        if error:
            json_body[0]["tags"]["log"] = error

        client.write_points(json_body)

    @staticmethod
    def subprocess_call(command):
        """
        Wrapper for subprocess call to handle non admin run or UAC issue
        :param command: (str) command to run
        :return:
        """
        try:
            if isinstance(command, list):
                command_str = subprocess.list2cmdline(command)
            else:
                command_str = command
            logging.info(command_str)

            subprocess.call(command)
        except OSError:
            raise SystemExit("Please run as administrator and disable Windows UAC")
    
    @staticmethod
    def parse_args():
        """
        Function to parse arguments provided to the script. Search for -p key to get settings path
        :return: settings_path: path to the configuration file
        """
        parser = argparse.ArgumentParser()
        # Add long and short argument
        parser.add_argument("--path", "-p", help="set path to the settings file generated by UI")
        args = parser.parse_args()

        if args.path:
            settings_path = args.path
            if not os.path.isfile(settings_path):
                raise SystemExit("Settings file does not exist")

            logging.info(f"Settings path is set to {settings_path}")
            return settings_path
        else:
            raise SystemExit("Please provide --path argument")


def generate_hash_str():
    """
    generate random hash. Letter A at the end is important to preserver Order in JS
    :return: hash code (str)
    """
    return f"{random.getrandbits(32):x}A".strip()


def set_logger(logging_file):
    """
    Function to setup logging output to stream and log file. Will be used by UI and backend
    :param: logging_file (str): path to the log file
    :return: None
    """

    work_dir = os.path.dirname(logging_file)
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)

    # add logging to console and log file
    logging.basicConfig(filename=logging_file, format='%(asctime)s (%(levelname)s) %(message)s', level=logging.DEBUG,
                        datefmt='%d.%m.%Y %H:%M:%S')
    logging.getLogger().addHandler(logging.StreamHandler())


if __name__ == "__main__":
    app = Downloader()
    app.run()
