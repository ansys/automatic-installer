import argparse
import datetime
import errno
import json
import logging
import os
import random
import re
import shutil
import subprocess
import sys
import time
import traceback
import zipfile
import zlib
from functools import wraps
from types import SimpleNamespace

import psutil
import py7zr
from artifactory import ArtifactoryPath
from artifactory import md5sum
from artifactory_du import artifactory_du
from dohq_artifactory import ArtifactoryException
from influxdb import InfluxDBClient
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.runtime.client_request_exception import ClientRequestException
from office365.sharepoint.client_context import ClientContext
from plyer import notification
from requests.exceptions import RequestException
from urllib3.exceptions import HTTPError

import iss_templates

__author__ = "Maksim Beliaev"
__email__ = "maksim.beliaev@ansys.com"
__version__ = "3.0.1"

STATISTICS_SERVER = "OTTBLD02"
STATISTICS_PORT = 8086

TIMEOUT = 90

ARTIFACTORY_DICT = {
    "Azure": "http://azwec7artsrv01.ansys.com:8080/artifactory",
    "Austin": "http://ausatsrv01.ansys.com:8080/artifactory",
    "Boulder": "http://bouartifact.ansys.com:8080/artifactory",
    "Canonsburg": "http://canartifactory.ansys.com:8080/artifactory",
    "Concord": "http://convmartifact.win.ansys.com:8080/artifactory",
    "Darmstadt": "http://darvmartifact.win.ansys.com:8080/artifactory",
    "Evanston": "http://evavmartifact:8080/artifactory",
    "Hannover": "http://hanartifact1.ansys.com:8080/artifactory",
    "Horsham": "http://horvmartifact1.ansys.com:8080/artifactory",
    "Lebanon": "http://lebartifactory.win.ansys.com:8080/artifactory",
    "Lyon": "http://lyovmartifact.win.ansys.com:8080/artifactory",
    "Otterfing": "http://ottvmartifact.win.ansys.com:8080/artifactory",
    "Pune": "http://punvmartifact.win.ansys.com:8080/artifactory",
    "Sheffield": "http://shfvmartifact.win.ansys.com:8080/artifactory",
    "SanJose": "http://sjoartsrv01.ansys.com:8080/artifactory",
    "Waterloo": "https://watartifactory.win.ansys.com:8443/artifactory",
}

SHAREPOINT_SITE_URL = r"https://ansys.sharepoint.com/sites/BetaDownloader"


class DownloaderError(Exception):
    pass


def retry(exceptions, tries=4, delay=3, backoff=1, logger=None, proc_lock=False):
    """
        Retry calling the decorated function using an exponential backoff.

    Args:
        exceptions (Exception or tuple): the exception to check. may be a tuple of exceptions to check
        tries (int): number of times to try (not retry) before giving up
        delay (int): initial delay between retries in seconds
        backoff (int): backoff multiplier e.g. value of 2 will double the delay each retry
        logger (logging): logger to use. If None, print
        proc_lock (bool): if retry is applied to proc lock function

    Returns: decorator

    """

    def deco_retry(func):
        @wraps(func)
        def f_retry(self, *args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return func(self, *args, **kwargs)
                except exceptions as e:
                    msg = f"{e}. Error occurred, attempt: {tries - mtries + 1}/{tries}"

                    if proc_lock:
                        # only applied for process lock
                        err = "Stop all processes running from installation folder. "
                        err += f"Attempt: {tries - mtries + 1}/{tries}"
                        if mtries > 1:
                            err += " Autoretry in 60sec."
                            Downloader.toaster_notification("Failed", err)
                        else:
                            raise DownloaderError(msg)

                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            else:
                error = (
                    "Please verify that your connection is stable, avoid switching state of VPN during download. "
                    "For artifactory you have to be on VPN. "
                    f"Number of attempts: {tries}/{tries}"
                )

                if logger:
                    raise DownloaderError(error)
                else:
                    print(error)

        return f_retry  # true decorator

    return deco_retry


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

    def __init__(self, version, settings_folder="", settings_path=""):
        """
        :parameter: version: version of the file, used if invoke file with argument -V to get version

        self.build_artifactory_path (ArtifactoryPath): URL to the latest build that will be used to download archive
        self.zip_file (str): path to the zip file on the PC
        self.target_unpack_dir (str): path where to unpack .zip
        self.installed_product_info (str): path to the product.info of the installed build
        self.product_root_path (str): root path of Ansys Electronics Desktop/ Workbench installation
        self.product_version (str): version to use in env variables eg 202
        self.setup_exe (str): path to the setup.exe from downloaded and unpacked zip
        self.remote_build_date (str): build date that receive from SharePoint
        self.hash (str): hash code used for this run of the program
        self.pid: pid (process ID of the current Python run, required to allow kill in UI)
        self.ctx: context object to authorize in SharePoint using office365 module
        self.settings_folder (str): default folder where all configurations would be saved
        self.history_file (str): file where installation progress would be written (this file is tracked by UI)
        self.history (dict): dict with history of installation processes
        self.logging_file (str): file where detailed log for all runs is saved

        """
        self.build_artifactory_path = ArtifactoryPath()
        self.zip_file = ""
        self.target_unpack_dir = ""
        self.installed_product_info = ""
        self.product_root_path = ""
        self.product_version = ""
        self.setup_exe = ""
        self.remote_build_date = ""

        self.pid = str(os.getpid())
        self.ctx = None
        self.warnings_list = []

        self.hash = generate_hash_str()
        if not settings_folder:
            self.settings_folder = os.path.join(os.environ["APPDATA"], "build_downloader")
        else:
            self.settings_folder = settings_folder

        self.check_and_make_directories(self.settings_folder)

        self.history = {}
        self.history_file = os.path.join(self.settings_folder, "installation_history.json")
        self.get_installation_history()

        self.logging_file = os.path.join(self.settings_folder, "downloader.log")

        self.settings_path = settings_path if settings_path else self.parse_args(version)
        with open(self.settings_path, "r") as file:
            self.settings = json.load(file, object_hook=lambda d: SimpleNamespace(**d))

        # this part of the code creates attributes that were added. Required for compatibility
        if not hasattr(self.settings, "replace_shortcut"):
            # v2.0.0
            self.settings.replace_shortcut = True

        if not hasattr(self.settings, "custom_flags"):
            # v2.2.0
            self.settings.custom_flags = ""

        if not hasattr(self.settings, "license_file"):
            # v3.0.0
            self.settings.license_file = ""

        if not hasattr(self.settings, "wb_assoc"):
            # v3.0.0
            self.settings.wb_assoc = ""

        if "ElectronicsDesktop" in self.settings.version:
            self.product_version = self.settings.version[1:4]
            if float(self.product_version) >= 221:
                self.product_root_path = os.path.join(
                    self.settings.install_path, "AnsysEM", f"v{self.product_version}", "Win64"
                )
            else:
                self.product_root_path = os.path.join(
                    self.settings.install_path,
                    "AnsysEM",
                    "AnsysEM" + self.product_version[:2] + "." + self.product_version[2:],
                    "Win64",
                )

            self.installed_product_info = os.path.join(self.product_root_path, "product.info")
        elif "Workbench" in self.settings.version:
            self.product_root_path = os.path.join(self.settings.install_path, "ANSYS Inc", self.settings.version[:4])
        elif "LicenseManager" in self.settings.version:
            self.product_root_path = os.path.join(
                self.settings.install_path, "ANSYS Inc", "Shared Files", "Licensing", "tools", "lmcenter"
            )

    def authorize_sharepoint(self):
        """
        Function that uses PnP to authorize user in SharePoint using Windows account and to get actual client_id and
        client_secret
        Returns: ctx: authorization context for Office365 library

        """
        self.update_installation_history(status="In-Progress", details="Authorizing in SharePoint")

        command = "powershell.exe "
        command += "Connect-PnPOnline -Url https://ansys.sharepoint.com/sites/BetaDownloader -UseWebLogin;"
        command += '(Get-PnPListItem -List secret_list -Fields "Title","client_id","client_secret").FieldValues'
        out_str = self.subprocess_call(command, shell=True, popen=True)

        secret_list = []
        try:
            for line in out_str.splitlines():
                if "Title" in line:
                    secret_dict = {"Title": line.split()[1]}
                elif "client_id" in line:
                    secret_dict["client_id"] = line.split()[1]
                elif "client_secret" in line:
                    secret_dict["client_secret"] = line.split()[1]
                    secret_list.append(secret_dict)
        except NameError:
            raise DownloaderError("Cannot retrieve authentication tokens for SharePoint")

        secret_list.sort(key=lambda elem: elem["Title"], reverse=True)

        context_auth = AuthenticationContext(url=SHAREPOINT_SITE_URL)
        context_auth.acquire_token_for_app(
            client_id=secret_list[0]["client_id"], client_secret=secret_list[0]["client_secret"]
        )

        ctx = ClientContext(SHAREPOINT_SITE_URL, context_auth)
        return ctx

    def run(self):
        """
        Function that executes the download-installation process
        :return: None
        """
        try:
            set_logger(self.logging_file)
            logging.info(f"Settings path is set to {self.settings_path}")

            if self.settings.artifactory == "SharePoint":
                self.ctx = self.authorize_sharepoint()

            self.update_installation_history(status="In-Progress", details="Verifying configuration")
            self.check_and_make_directories(self.settings.install_path, self.settings.download_path)
            if "ElectronicsDesktop" in self.settings.version or "Workbench" in self.settings.version:
                space_required = 15

                # License Manager can be updated even if running
                self.check_process_lock()
            else:
                if not self.settings.license_file:
                    raise DownloaderError("No license file defined. Please select it in Advanced Settings")

                if not os.path.isfile(self.settings.license_file):
                    raise DownloaderError(f"No license file was detected under {self.settings.license_file}")

                space_required = 1

            self.check_free_space(self.settings.download_path, space_required)
            self.check_free_space(self.settings.install_path, space_required)

            self.get_build_link()
            if self.settings.force_install or self.newer_version_exists:
                self.download_file()

                if "ElectronicsDesktop" in self.settings.version or "Workbench" in self.settings.version:
                    self.check_process_lock()  # download can take time, better to recheck again
                self.install()
                try:
                    self.send_statistics()
                except Exception:
                    self.warnings_list.append("Connection to product improvement server failed")
                self.update_installation_history(status="Success", details="Normal completion")
            else:
                raise DownloaderError("Versions are up to date. If issue occurred please use force install flag")
            return
        except DownloaderError as e:
            # all caught errors are here
            logging.error(e)
            self.update_installation_history(status="Failed", details=str(e))
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
                    raise DownloaderError(f"{path} could not be created due to insufficient permissions")
                except OSError as err:
                    if "BitLocker" in str(err):
                        raise DownloaderError("Your drive is locked by BitLocker. Please unlock!")
                    else:
                        raise DownloaderError(err)

    @staticmethod
    def check_free_space(path, required):
        """
        Verifies that enough disk space is available. Raises error if not enough space
        :param path: path where to check
        :param required: value in GB that should be available on drive to pass the check
        :return:
        """
        free_space = shutil.disk_usage(path).free // (2**30)
        if free_space < required:
            err = f"Disk space in {path} is less than {required}GB. This would not be enough to proceed"
            raise DownloaderError(err)

    @retry((DownloaderError,), tries=3, delay=60, logger=logging, proc_lock=True)
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
            raise DownloaderError(
                "Following processes are running from installation directory: "
                + f"{', '.join(set(process_list))}. Please stop all processes."
            )

    @property
    def newer_version_exists(self):
        """
        verify if version on the server is newer compared to installed
        Returns:
            (bool) True if remote is newer or no version is installed, False if remote is the same or older
        """
        if "Workbench" in self.settings.version:
            product_installed = os.path.join(self.product_root_path, "package.id")
        elif "LicenseManager" in self.settings.version:
            # always update LM
            return True
        else:
            product_installed = self.installed_product_info

        if os.path.isfile(product_installed):
            if "Workbench" in self.settings.version:
                with open(product_installed) as file:
                    installed_product_version = next(file).rstrip().split()[-1]  # get first line
                    try:
                        installed_product_version = int(installed_product_version.split("P")[0])
                    except ValueError:
                        installed_product_version = 0
            else:
                installed_product_version = self.get_edt_build_date(product_installed)

            logging.info(f"Installed version of {self.settings.version} is {installed_product_version}")
            new_product_version = self.get_new_build_date()

            if not all([new_product_version, installed_product_version]):
                # some of the versions could not be parsed, need installation
                return True

            if new_product_version <= installed_product_version:
                return False
        return True

    def get_new_build_date(self, distribution="winx64"):
        """
        Create URL for new build extraction or extract version from self.remote_build_date for SharePoint download
        Returns:
            new_product_version (int) version of the product on the server
        """
        if self.settings.artifactory != "SharePoint":
            if "Workbench" in self.settings.version:
                url = self.build_artifactory_path.joinpath("package.id")
            elif "ElectronicsDesktop" in self.settings.version:
                system = "windows" if distribution == "winx64" else "linux"
                url = self.build_artifactory_path.parent.joinpath(f"product_{system}.info")
            else:
                # todo add license manager handling
                return 0

            logging.info(f"Request info about new package: {url}")
            new_product_version = self.get_build_info_file_from_artifactory(url)
        else:
            try:
                new_product_version = int(self.remote_build_date)
            except ValueError:
                return 0

        logging.info(f"Version on artifactory/SP is {new_product_version}")
        return new_product_version

    @retry((HTTPError, RequestException, ConnectionError, ConnectionResetError), 4, logger=logging)
    def get_build_link(self, distribution="winx64"):
        """
        Function that sends HTTP request to JFrog and get the list of folders with builds for Electronics Desktop and
        checks user password
        If use SharePoint then readdress to SP list
        :modify: (str) self.build_artifactory_path: URL link to the latest build that will be used to download archive
        """
        self.update_installation_history(status="In-Progress", details="Search latest build URL")
        if self.settings.artifactory == "SharePoint":
            self.get_sharepoint_build_info()
            return

        if not hasattr(self.settings.password, self.settings.artifactory):
            raise DownloaderError(f"Please provide password for {self.settings.artifactory}")

        password = getattr(self.settings.password, self.settings.artifactory)

        if not self.settings.username or not password:
            raise DownloaderError("Please provide username and artifactory password")

        server = ARTIFACTORY_DICT[self.settings.artifactory]

        art_path = ArtifactoryPath(server, auth=(self.settings.username, password), timeout=TIMEOUT)
        try:
            repos_list = art_path.get_repositories(lazy=True)
        except ArtifactoryException as err:
            raise DownloaderError(f"Cannot retrieve repositories. Error: {err}")

        # fill the dictionary with Electronics Desktop and Workbench keys since builds could be different
        # still parse the list because of different names on servers
        artifacts_dict = {}
        for repo in repos_list:
            repo_name = repo.name
            if "EBU_Certified" in repo_name:
                version = repo_name.split("_")[0] + "_ElectronicsDesktop"
            elif "Certified" in repo_name and "Licensing" not in repo_name:
                version = repo_name.split("_")[0] + "_Workbench"
            elif "Certified" in repo_name and "Licensing" in repo_name:
                version = repo_name.split("_")[0] + "_LicenseManager"
            else:
                continue

            if version not in artifacts_dict:
                # extract real repo name in case it is cached
                if art_path.joinpath(repo_name).exists():
                    # repo might be syncing (happens on new release addition)
                    artifacts_dict[version] = art_path.joinpath(repo_name).stat().repo

        try:
            repo = artifacts_dict[self.settings.version]
        except KeyError:
            raise DownloaderError(
                f"Version {self.settings.version} that you have specified "
                + f"does not exist on {self.settings.artifactory}"
            )

        path = ""
        art_path = art_path.joinpath(str(repo))
        if "ElectronicsDesktop" in self.settings.version:
            archive = "winx64.zip" if distribution == "winx64" else "linx64.tgz"
            builds_dates = []
            for relative_p in art_path:
                try:
                    archive_exists = list(relative_p.glob(f"Electronics*{archive}"))
                    if archive_exists:
                        builds_dates.append(int(relative_p.name))
                except ValueError:
                    pass

            if not builds_dates:
                raise DownloaderError("Artifact does not exist")

            latest_build = sorted(builds_dates)[-1]

            art_path = art_path.joinpath(str(latest_build))
            for path in art_path:
                if archive in path.name:
                    break
            else:
                raise DownloaderError(f"Cannot find {distribution} archive file")

        elif "Workbench" in self.settings.version or "LicenseManager" in self.settings.version:
            path = art_path.joinpath(distribution)

        if not path:
            raise DownloaderError("Cannot receive URL")

        self.build_artifactory_path = path

    def get_sharepoint_build_info(self):
        """
        Gets link to the latest build from SharePoint and builddate itself
        Returns: None

        """
        product_list = self.ctx.web.lists.get_by_title("product_list")
        items = product_list.items
        self.ctx.load(items).execute_query()

        build_list = []
        for item in items:
            title = item.properties["Title"]
            if title != self.settings.version:
                continue

            build_dict = {
                "Title": title,
                "build_date": item.properties["build_date"],
                "relative_url": item.properties["relative_url"],
            }
            build_list.append(build_dict)

        build_list.sort(key=lambda elem: elem["build_date"], reverse=True)

        build_dict = build_list[0] if build_list else {}
        if not build_dict:
            raise DownloaderError(f"No version of {self.settings.version} is available on SharePoint")

        self.build_artifactory_path = build_dict["relative_url"]
        self.remote_build_date = build_dict["build_date"]

    def download_file(self):
        """
        Downloads file in chunks and saves to the temp.zip file
        Uses url to the zip archive or special JFrog API to download Workbench folder
        :modify: (str) zip_file: link to the zip file
        """
        if self.settings.artifactory == "SharePoint" or "win" in self.build_artifactory_path.name:
            archive_type = "zip"
        else:
            archive_type = "tgz"

        self.zip_file = os.path.join(self.settings.download_path, f"{self.settings.version}.{archive_type}")
        chunk_size = 50 * 1024 * 1024
        if self.settings.artifactory == "SharePoint":
            self.download_from_sharepoint(chunk_size=chunk_size)
        else:
            self.download_from_artifactory(archive_type, chunk_size=chunk_size)

        logging.info(f"File is downloaded to {self.zip_file}")

    @retry((HTTPError, RequestException, ConnectionError, ConnectionResetError), 4, logger=logging)
    def download_from_artifactory(self, archive_type, chunk_size):
        """
        Download file from Artifactory
        Args:
            archive_type: type of the archive, zip or tgz
            chunk_size: (int) chunk size in bytes when download

        Returns: None
        """
        if not self.build_artifactory_path.replication_status["status"] in ["ok", "never_run"]:
            raise DownloaderError("Currently Artifactory repository is replicating, please try later")

        logging.info(f"Start download file from {self.build_artifactory_path} to {self.zip_file}")
        self.update_installation_history(
            status="In-Progress", details=f"Downloading file from {self.settings.artifactory}"
        )
        if "ElectronicsDesktop" in self.settings.version:
            file_stats = self.build_artifactory_path.stat()
            arti_file_md5 = file_stats.md5
            logging.info(f"Artifactory hash: {arti_file_md5}")

            try:
                self.build_artifactory_path.writeto(
                    out=self.zip_file, chunk_size=chunk_size, progress_func=self.print_download_progress
                )
            except RuntimeError as err:
                raise DownloaderError(f"Cannot download file. Server returned status code: {err}")

            local_md5_hash = md5sum(self.zip_file)
            logging.info(f"Local file hash: {local_md5_hash}")
            if local_md5_hash != arti_file_md5:
                raise DownloaderError("Downloaded file MD5 hash is different")

        elif "Workbench" in self.settings.version or "LicenseManager" in self.settings.version:
            try:
                file_size = self.get_artifactory_folder_size()
                logging.info(f"Workbench/License Manager real file size is {file_size}")
            except (TypeError, ValueError):
                file_size = 14e9

            archive_url = self.build_artifactory_path.archive(archive_type=archive_type)
            archive_url.writeto(
                out=self.zip_file,
                chunk_size=chunk_size,
                progress_func=lambda x, y: self.print_download_progress(x, file_size),
            )

    def get_artifactory_folder_size(self):
        aql_query_dict, max_depth_print = artifactory_du.prepare_aql(
            file=f"/{self.build_artifactory_path.name}",
            max_depth=0,
            repository=self.build_artifactory_path.repo,
            without_downloads="",
            older_than="",
        )
        artifacts = artifactory_du.artifactory_aql(
            artifactory_url=str(self.build_artifactory_path.drive),
            aql_query_dict=aql_query_dict,
            username=self.build_artifactory_path.auth[0],
            password=self.build_artifactory_path.auth[1],
            kerberos=False,
            verify=False,
        )
        file_size = artifactory_du.out_as_du(artifacts, max_depth_print, human_readable=False)
        file_size = int(file_size.strip("/"))
        return file_size

    @retry(
        (HTTPError, RequestException, ConnectionError, ConnectionResetError, ClientRequestException),
        tries=4,
        logger=logging,
    )
    def download_from_sharepoint(self, chunk_size):
        """
        Downloads file from Sharepoint
        Args:
            chunk_size: (int) chunk size in bytes when download
        Returns: None
        """
        self.update_installation_history(status="In-Progress", details="Downloading file from SharePoint")
        remote_file = self.ctx.web.get_file_by_server_relative_url(
            f"/sites/BetaDownloader/{self.build_artifactory_path}"
        )
        remote_file.get()
        try:
            self.ctx.execute_query()
        except ClientRequestException as err:
            logging.error(str(err))
            raise DownloaderError(
                "URL on SharePoint is broken. Report an issue to betadownloader@ansys.com. "
                "In meantime please switch to any other repository."
            )

        file_size = remote_file.length
        self.check_free_space(self.settings.download_path, file_size / 1024 / 1024 / 1024)

        with open(self.zip_file, "wb") as zip_file:
            try:
                remote_file.download_session(
                    zip_file,
                    lambda offset: self.print_download_progress(offset, total_size=file_size),
                    chunk_size=chunk_size,
                )
                self.ctx.execute_query()
            except OSError as err:
                if err.errno == errno.ENOSPC:
                    raise DownloaderError("No disk space available in download folder!")
                else:
                    raise

        if not self.zip_file:
            raise DownloaderError("ZIP download failed")

        if abs(os.path.getsize(self.zip_file) - file_size) > 0.05 * file_size:
            raise DownloaderError("File size difference is more than 5%")

    def print_download_progress(self, offset, total_size):
        msg = "Downloaded {}/{}MB...[{}%]".format(
            int(offset / 1024 / 1024), int(total_size / 1024 / 1024), min(round(offset / total_size * 100, 2), 100)
        )
        logging.info(msg)
        self.update_installation_history(status="In-Progress", details=msg)

    def install(self, local_lang=False):
        """
        Unpack downloaded zip and proceed to installation. Different executions for Electronics Desktop and Workbench
        :param local_lang: if not specified then use English as default installation language
        :return: None
        """
        self.unpack_archive()

        if "ElectronicsDesktop" in self.settings.version:
            self.install_edt()
        elif "Workbench" in self.settings.version:
            self.install_wb(local_lang)
        else:
            self.install_license_manager()

        self.update_installation_history(status="In-Progress", details="Clean temp directory")
        self.clean_temp()

    def unpack_archive(self):
        self.update_installation_history(status="In-Progress", details="Start unpacking")
        self.target_unpack_dir = self.zip_file.replace(".zip", "")
        try:
            with zipfile.ZipFile(self.zip_file, "r") as zip_ref:
                zip_ref.extractall(self.target_unpack_dir)
        except OSError as err:
            if err.errno == errno.ENOSPC:
                raise DownloaderError("No disk space available in download folder!")
            else:
                raise DownloaderError(f"Cannot unpack due to {err}")
        except (zipfile.BadZipFile, zlib.error):
            raise DownloaderError("Zip file is broken. Please try again later or use another repository.")
        logging.info(f"File is unpacked to {self.target_unpack_dir}")

    def install_edt(self):
        """
        Install Electronics Desktop. Make verification that the same version is not yet installed and makes
        silent installation
        Get Workbench installation path from environment variable and enables integration if exists.
        :return: None
        """
        setup_exe, product_id, installshield_version = self.parse_iss_template(self.target_unpack_dir)
        self.uninstall_edt(setup_exe, product_id, installshield_version)

        install_iss_file, install_log_file = self.create_install_iss_file(installshield_version, product_id)

        command = [f'"{setup_exe}"', "-s", rf'-f1"{install_iss_file}"', rf'-f2"{install_log_file}"']
        command = " ".join(command)
        self.update_installation_history(status="In-Progress", details="Start installation")
        logging.info("Execute installation")
        self.subprocess_call(command)

        self.check_result_code(install_log_file)
        self.update_edt_registry()
        self.remove_aedt_shortcuts()

    def create_install_iss_file(self, installshield_version, product_id):
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
        if os.path.isfile(
            os.path.join(self.settings.install_path, "AnsysEM", "Shared Files", "Licensing", "ansyslmd.ini")
        ):
            install_iss = iss_templates.install_iss + iss_templates.existing_server
            logging.info("Install using existing license configuration")
        else:
            install_iss = iss_templates.install_iss + iss_templates.new_server
            logging.info("Install using 127.0.0.1, Otterfing and HQ license servers")
        with open(install_iss_file, "w") as file:
            file.write(
                install_iss.format(
                    product_id,
                    os.path.join(self.settings.install_path, "AnsysEM"),
                    os.environ["TEMP"],
                    integrate_wb,
                    installshield_version,
                )
            )
        return install_iss_file, install_log_file

    def uninstall_edt(self, setup_exe, product_id, installshield_version):
        """
        Silently uninstall build of the same version
        :return: None
        """
        if os.path.isfile(self.installed_product_info):
            uninstall_iss_file = os.path.join(self.target_unpack_dir, "uninstall.iss")
            uninstall_log_file = os.path.join(self.target_unpack_dir, "uninstall.log")
            with open(uninstall_iss_file, "w") as file:
                file.write(iss_templates.uninstall_iss.format(product_id, installshield_version))

            command = [
                f'"{setup_exe}"',
                "-uninst",
                "-s",
                rf'-f1"{uninstall_iss_file}"',
                rf'-f2"{uninstall_log_file}"',
            ]
            command = " ".join(command)
            logging.info("Execute uninstallation")
            self.update_installation_history(status="In-Progress", details="Uninstall previous build")
            self.subprocess_call(command)

            self.check_result_code(uninstall_log_file, False)
            em_main_dir = os.path.dirname(self.product_root_path)
            self.remove_path(em_main_dir)

            if os.path.isdir(em_main_dir):
                raise DownloaderError(f"Failed to remove {em_main_dir}. Probably directory is locked.")
        else:
            logging.info("Version is not installed, skip uninstallation")

    def check_result_code(self, log_file, installation=True):
        """
        Verify result code of the InstallShield log file
        :param log_file: installation log file
        :param installation: True if verify log after installation elif after uninstallation False
        :return: None
        """
        success = "New build was successfully installed" if installation else "Previous build was uninstalled"
        fail = "Installation went wrong" if installation else "Uninstallation went wrong"
        if not os.path.isfile(log_file):
            raise DownloaderError(f"{fail}. Check that UAC disabled or confirm UAC question manually")

        msg = fail
        regex = "ResultCode=(.*)"
        with open(log_file) as file:
            for line in file:
                code = re.findall(regex, line)
                if code:
                    if code[0] == "0":
                        logging.info(success)
                        break
                    elif code[0] == "-3" and installation:
                        msg += " Electronics Desktop cannot coexist in another location. Change installation path"
                        raise DownloaderError(msg)
            else:
                if not installation:
                    msg = "Official uninstaller failed, make hard remove"
                    logging.error(msg)
                    self.warnings_list.append(msg)
                else:
                    raise DownloaderError(msg)

    @staticmethod
    def get_edt_build_date(product_info_file="", file_content=None):
        """
        extract information about Electronics Desktop build date and version
        Args:
            product_info_file: path to the product.info
            file_content (list): accepts list with file content as well instead of file

        Returns: (int) build_date

        """
        if os.path.isfile(product_info_file):
            with open(product_info_file) as file:
                file_content = file.readlines()

        for line in file_content:
            if "AnsProductBuildDate" in line:
                full_build_date = line.split("=")[1].replace('"', "").replace("-", "")
                build_date = full_build_date.split()[0]
                break
        else:
            # cannot find line with build date
            return 0

        try:
            return int(build_date)
        except ValueError:
            return 0

    @staticmethod
    def parse_iss_template(unpacked_dir):
        """
        Open directory with unpacked build of Electronics Desktop and search for SilentInstallationTemplate.iss to
        extract product ID which is GUID hash
        Args:
            unpacked_dir: directory where AEDT package was unpacked
        Returns:
            product_id: product GUID extracted from iss template
            setup_exe: set path to setup.exe if exists
            installshield_version: set version from file
        """
        default_iss_file = ""
        setup_exe = ""
        product_id_match = []

        for dir_path, dir_names, file_names in os.walk(unpacked_dir):
            for filename in file_names:
                if "AnsysEM" in dir_path and filename.endswith(".iss"):
                    default_iss_file = os.path.join(dir_path, filename)
                    setup_exe = os.path.join(dir_path, "setup.exe")
                    break

        if not default_iss_file:
            raise DownloaderError("SilentInstallationTemplate.iss does not exist")

        if not os.path.isfile(setup_exe):
            raise DownloaderError("setup.exe does not exist")

        with open(default_iss_file, "r") as iss_file:
            for line in iss_file:
                if "DlgOrder" in line:
                    guid_regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                    product_id_match = re.findall(guid_regex, line)
                if "InstallShield Silent" in line:
                    installshield_version = next(iss_file).split("=")[1]

        if product_id_match:
            product_id = product_id_match[0]
            logging.info(f"Product ID is {product_id}")
        else:
            raise DownloaderError("Unable to extract product ID")

        return setup_exe, product_id, installshield_version

    def install_license_manager(self):
        """
        Install license manager and feed it with license file
        """
        self.setup_exe = os.path.join(self.target_unpack_dir, "setup.exe")

        if os.path.isfile(self.setup_exe):
            install_path = os.path.join(self.settings.install_path, "ANSYS Inc")
            if not os.path.isfile(self.settings.license_file):
                raise DownloaderError(f"No license file was detected under {self.settings.license_file}")

            command = [
                self.setup_exe,
                "-silent",
                "-LM",
                "-install_dir",
                install_path,
                "-lang",
                "en",
                "-licfilepath",
                self.settings.license_file,
            ]
            self.update_installation_history(status="In-Progress", details="Start installation")
            logging.info("Execute installation")
            self.subprocess_call(command)

            package_build = self.parse_lm_installer_builddate()
            installed_build = self.get_license_manager_build_date()
            if all([package_build, installed_build]) and package_build == installed_build:
                self.update_installation_history(status="Success", details="Normal completion")
            else:
                raise DownloaderError("License Manager was not installed")
        else:
            raise DownloaderError("No LicenseManager setup.exe file detected")

    def parse_lm_installer_builddate(self):
        """
        Check build date of installation package of License Manager
        """

        build_file = os.path.join(self.target_unpack_dir, "builddate.txt")
        lm_center_archive = os.path.join(self.target_unpack_dir, "lmcenter", "WINX64.7z")

        if not os.path.isfile(build_file) and os.path.isfile(lm_center_archive):
            with py7zr.SevenZipFile(lm_center_archive, "r") as archive:
                archive.extractall(path=os.path.join(self.target_unpack_dir, "lmcenter"))
            build_file = os.path.join(
                self.target_unpack_dir,
                "lmcenter",
                "Shared Files",
                "licensing",
                "tools",
                "lmcenter",
                "lmcenter_blddate.txt",
            )

        if not os.path.isfile(build_file):
            # check again if file was unpacked
            logging.warning("builddate.txt was not found in installation package")
            return

        with open(build_file) as file:
            for line in file:
                if "license management center" in line.lower():
                    lm_build_date = line.split()[-1]
                    try:
                        logging.info(f"Build date of License Manager in installation package {lm_build_date}")
                        lm_build_date = int(lm_build_date)
                        return lm_build_date
                    except TypeError:
                        raise DownloaderError("Cannot extract build date of installation package")

    def get_license_manager_build_date(self):
        """
        Check build date of installed License Manager
        """
        build_date_file = os.path.join(self.product_root_path, "lmcenter_blddate.txt")
        if not os.path.isfile(build_date_file):
            raise DownloaderError("lmcenter_blddate.txt is not available")

        with open(build_date_file) as file:
            lm_build_date = next(file).split()[-1]
            try:
                logging.info(f"Newly installed build date of License Manager: {lm_build_date}")
                lm_build_date = int(lm_build_date)
                return lm_build_date
            except (TypeError, ValueError):
                raise DownloaderError("Cannot extract build date of installed License Manager")

    def install_wb(self, local_lang=False):
        """
        Install Workbench to the target installation directory
        :param local_lang: if not specified then use English as default installation language
        """
        self.setup_exe = os.path.join(self.target_unpack_dir, "setup.exe")

        if os.path.isfile(self.setup_exe):
            uninstall_exe = self.uninstall_wb()

            install_path = os.path.join(self.settings.install_path, "ANSYS Inc")
            command = [self.setup_exe, "-silent", "-install_dir", install_path]
            if not local_lang:
                command += ["-lang", "en"]
            command += self.settings.wb_flags.split()

            # the "shared files" is created at the same level as the "ANSYS Inc" so if installing to unique folders,
            # the Shared Files folder will be unique as well. Thus we can check install folder for license
            if (
                os.path.isfile(os.path.join(install_path, "Shared Files", "Licensing", "ansyslmd.ini"))
                or "ANSYSLMD_LICENSE_FILE" in os.environ
            ):
                logging.info("Install using existing license configuration")
            else:
                command += ["-licserverinfo", "2325:1055:127.0.0.1,OTTLICENSE5,PITRH6LICSRV1"]
                logging.info("Install using 127.0.0.1, Otterfing and HQ license servers")

            # convert command to string to easy append custom flags
            command = subprocess.list2cmdline(command)
            command += " " + self.settings.custom_flags

            self.update_installation_history(status="In-Progress", details="Start installation")
            logging.info("Execute installation")
            self.subprocess_call(command)

            if os.path.isfile(uninstall_exe):
                logging.info("New build was installed")
            else:
                raise DownloaderError(
                    "Workbench installation failed. "
                    + f"If you see this error message by mistake please report to {__email__}"
                )

            if self.settings.wb_assoc:
                wb_assoc_exe = os.path.join(self.settings.wb_assoc, "commonfiles", "tools", "winx64", "fileassoc.exe")
                if not os.path.isfile(wb_assoc_exe):
                    self.warnings_list.append(f"Cannot find {wb_assoc_exe}")
                else:
                    logging.info("Run WB file association")
                    self.subprocess_call(wb_assoc_exe)
        else:
            raise DownloaderError("No Workbench setup.exe file detected")

    def uninstall_wb(self):
        """
        Uninstall Workbench if such exists in the target installation directory
        :return: uninstall_exe: name of the executable of uninstaller"""

        uninstall_exe = os.path.join(self.product_root_path, "Uninstall.exe")
        if os.path.isfile(uninstall_exe):
            command = [uninstall_exe, "-silent"]
            self.update_installation_history(status="In-Progress", details="Uninstall previous build")
            logging.info("Execute uninstallation")
            self.subprocess_call(command)
            logging.info("Previous build was uninstalled using uninstaller")
        else:
            logging.info("No Workbench Uninstall.exe file detected")

        self.remove_path(self.product_root_path)

        return uninstall_exe

    def remove_path(self, path):
        """
        Function to safely remove path if rmtree fails
        :param path:
        :return:
        """

        def hard_remove():
            try:
                # try this dirty method to force remove all files in directory
                all_files = os.path.join(path, "*.*")
                command = ["DEL", "/F", "/Q", "/S", all_files, ">", "NUL"]
                self.subprocess_call(command, shell=True)

                command = ["rmdir", "/Q", "/S", path]
                self.subprocess_call(command, shell=True)
            except Exception as err:
                logging.error(str(err))
                logging.error("Failed to remove directory via hard_remove")
                self.warnings_list.append("Failed to remove directory")

        logging.info(f"Removing {path}")
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except PermissionError:
                logging.warning("Permission error. Switch to CMD force mode")
                hard_remove()
                self.warnings_list.append("Clean remove failed due to Permissions Error")
            except (FileNotFoundError, OSError, Exception):
                logging.warning("FileNotFoundError or other error. Switch to CMD force mode")
                hard_remove()
                self.warnings_list.append("Clean remove failed due to Not Found or OS Error")

        elif os.path.isfile(path):
            os.remove(path)

    def get_build_info_file_from_artifactory(self, build_info):
        """
        Downloads product info file from artifactory

        :param (ArtifactoryPath) build_info: arti path to the package_id file
        :return: (int): package_id if extracted
        """
        product_info = 0
        package_info = build_info.read_text()
        try:
            if "Workbench" in self.settings.version:
                first_line = package_info.split("\n")[0]
                product_info = first_line.rstrip().split()[-1]
                try:
                    product_info = int(product_info.split("P")[0])
                except ValueError:
                    pass
            else:
                product_info = self.get_edt_build_date(file_content=package_info.split("\n"))
        except IndexError:
            pass

        return product_info

    def clean_temp(self):
        """
        Cleans downloaded zip and unpacked folder with content
        :return: None
        """
        try:
            if os.path.isfile(self.zip_file) and self.settings.delete_zip:
                self.remove_path(self.zip_file)
                logging.info("ZIP deleted")

            if os.path.isdir(self.target_unpack_dir):
                self.remove_path(self.target_unpack_dir)
                logging.info("Unpacked directory removed")
        except PermissionError:
            logging.error("Temp files could not be removed due to permission error")

    def remove_aedt_shortcuts(self):
        """
        Function to remove newly created AEDT shortcuts and replace them with new one
        """
        if not self.settings.replace_shortcut:
            return

        # include Public, user folder and user folder when OneDrive sync is enabled
        for user in ["Public", os.getenv("username"), os.path.join(os.getenv("username"), "OneDrive - ANSYS, Inc")]:
            desktop = os.path.join("C:\\", "Users", user, "Desktop")

            for shortcut in [
                "ANSYS Savant",
                "ANSYS EMIT",
                "ANSYS SIwave",
                "ANSYS Twin Builder",
                "Ansys Nuhertz FilterSolutions",
            ]:
                self.remove_path(os.path.join(desktop, shortcut + ".lnk"))

            new_name = os.path.join(
                desktop, f"20{self.product_version[:2]}R{self.product_version[2:]} Electronics Desktop.lnk"
            )
            aedt_shortcut = os.path.join(desktop, "ANSYS Electronics Desktop.lnk")
            if not os.path.isfile(new_name):
                try:
                    os.rename(aedt_shortcut, new_name)
                except FileNotFoundError:
                    pass
            else:
                self.remove_path(aedt_shortcut)

    def update_edt_registry(self):
        """
        Update Electronics Desktop registry based on the files in the HPC_Options folder that are added from UI
        :return: None
        """
        hpc_folder = os.path.join(self.settings_folder, "HPC_Options")

        update_registry_exe = os.path.join(self.product_root_path, "UpdateRegistry.exe")
        productlist_file = os.path.join(self.product_root_path, "config", "ProductList.txt")

        if not os.path.isfile(productlist_file):
            raise DownloaderError("Cannot update registry. Probably Electronics Desktop installation failed")

        with open(productlist_file) as file:
            product_version = next(file).rstrip()  # get first line

        self.update_installation_history(status="In-Progress", details="Update registry")
        if os.path.isdir(hpc_folder):
            for file in os.listdir(hpc_folder):
                if ".acf" in file:
                    options_file = os.path.join(hpc_folder, file)
                    command = [update_registry_exe, "-ProductName", product_version, "-FromFile", options_file]
                    logging.info("Update registry")
                    self.subprocess_call(command)

    def update_installation_history(self, status, details):
        """
        Update ordered dictionary with new data and write it to the file
        :param status: Failed | Success | In-Progress (important, used in JS)
        :param details: Message for details field
        :return:
        """
        if status == "Failed" or status == "Success":
            try:
                self.toaster_notification(status, details)
            except Exception:
                msg = "Toaster notification did not work"
                logging.error(msg)
                self.warnings_list.append(msg)

        self.get_installation_history()  # in case if file was deleted during run of installation
        time_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        shorten_path = self.settings_path.replace(os.getenv("APPDATA", "@@@"), "%APPDATA%")

        if status == "Failed" or status == "Success":
            if self.warnings_list:
                details += "\nSome warnings occurred during process:\n" + "\n".join(self.warnings_list)

        self.history[self.hash] = [status, self.settings.version, time_now, shorten_path, details, self.pid]
        with open(self.history_file, "w") as file:
            json.dump(self.history, file, indent=4)

    @staticmethod
    def toaster_notification(status, details):
        """
        Send toaster notification
        :param status: Failed | Success | In-Progress
        :param details: Message for details field
        :return:
        """
        icon = "fail.ico" if status == "Failed" else "success.ico"

        root_path = os.path.dirname(sys.argv[0])
        icon_path = os.path.join(root_path, "notifications", icon)

        if not os.path.isfile(icon_path):
            root_path = os.path.dirname(os.path.realpath(__file__))
            icon_path = os.path.join(root_path, "notifications", icon)  # dev path

        notification.notify(title=status, message=details, app_icon=icon_path, timeout=15)

    def get_installation_history(self):
        """
        Read a file with installation history
        create a file if does not exist
        :return: dict with history or empty in case if file was deleted during run of installation
        """
        if os.path.isfile(self.history_file):
            try:
                with open(self.history_file) as file:
                    self.history = json.load(file)
            except json.decoder.JSONDecodeError:
                return
        else:
            self.history = {}

    def send_statistics(self, error=None):
        """
        Send usage statistics to the database.
        Collect username, time, version and software installed
        in case of crash send also crash data
        :parameter: error: error message of what went wrong
        :return: None
        """

        version, tool = self.settings.version.split("_")
        time_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.settings.username = os.getenv("username", self.settings.username)

        if self.settings.artifactory == "SharePoint":
            self.send_statistics_to_sharepoint(tool, version, time_now, error)
        else:
            self.send_statistics_to_influx(tool, version, time_now, error)

    def send_statistics_to_influx(self, tool, version, time_now, error):
        """
        Send statistics to InfluxDB
        Args:
            tool: product that is installed
            version: version
            time_now: time
            error: error if some crash occurred
        Returns:
            None
        """
        client = InfluxDBClient(host=STATISTICS_SERVER, port=STATISTICS_PORT)
        db_name = "downloads" if not error else "crashes"
        client.switch_database(db_name)
        json_body = [
            {
                "measurement": db_name,
                "tags": {
                    "username": self.settings.username,
                    "version": version,
                    "tool": tool,
                    "artifactory": self.settings.artifactory,
                    "downloader_ver": __version__,
                },
                "time": time_now,
                "fields": {"count": 1},
            }
        ]

        if error:
            json_body[0]["tags"]["log"] = error

        client.write_points(json_body)

    def send_statistics_to_sharepoint(self, tool, version, time_now, error):
        """
        Send statistics to SharePoint list
        Args:
            time_now: time
            tool: product that is installed
            version: version
            error: error if some crash occurred
        Returns:
            None
        """
        list_name = "statistics" if not error else "crashes"
        target_list = self.ctx.web.lists.get_by_title(list_name)

        item = {
            "Title": self.settings.username,
            "Date": str(time_now),
            "tool": tool,
            "version": version,
            "in_influx": False,
            "downloader_ver": __version__,
        }

        if error:
            error = error.replace("\n", "#N").replace("\r", "")
            item["error"] = error

        target_list.add_item(item)
        self.ctx.execute_query()

    @staticmethod
    def subprocess_call(command, shell=False, popen=False):
        """
        Wrapper for subprocess call to handle non admin run or UAC issue

        Args:
            command: (str/list) command to run
            shell: call with shell mode or not
            popen: in case if you need output we need to use Popen. Pyinstaller compiles in -noconsole, need
              to explicitly define stdout, in, err

        Returns:
            output (str), output of the command run
        """

        output = ""
        try:
            if isinstance(command, list):
                command_str = subprocess.list2cmdline(command)
            else:
                command_str = command
            logging.info(command_str)

            if popen:
                p = subprocess.Popen(
                    command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell
                )

                byte_output = p.stdout.read()
                output = byte_output.decode("utf-8").rstrip()
                p.communicate()
            else:
                subprocess.call(command, shell=shell)

            return output
        except OSError:
            raise DownloaderError("Please run as administrator and disable Windows UAC")

    @staticmethod
    def parse_args(version):
        """
        Function to parse arguments provided to the script. Search for -p key to get settings path
        :return: settings_path: path to the configuration file
        """
        parser = argparse.ArgumentParser()
        # Add long and short argument
        parser.add_argument("--path", "-p", help="set path to the settings file generated by UI")
        parser.add_argument("--version", "-V", action="version", version=f"%(prog)s version: {version}")
        args = parser.parse_args()

        if args.path:
            settings_path = args.path
            if not os.path.isfile(settings_path):
                raise DownloaderError("Settings file does not exist")

            return settings_path
        else:
            raise DownloaderError("Please provide --path argument")


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
    # If you set the log level to INFO, it will include INFO, WARNING, ERROR, and CRITICAL messages
    logging.basicConfig(
        filename=logging_file,
        format="%(asctime)s (%(levelname)s) %(message)s",
        level=logging.INFO,
        datefmt="%d.%m.%Y %H:%M:%S",
    )
    logging.getLogger().addHandler(logging.StreamHandler())


if __name__ == "__main__":
    app = Downloader(__version__)
    app.run()
