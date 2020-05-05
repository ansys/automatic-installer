import argparse
import json
import logging
import os
import re
import shutil
import zipfile
import sys
from collections import namedtuple, OrderedDict

import requests

import set_log

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
        Main class that operates the download process:
        1. enables logs
        2. parses arguments to get settings file
        3. loads JSON to named tuple
        4. gets URL for selected version based on server
        5. downloads zip archive with BETA build
        """
    def __init__(self):
        """
        self.build_url (str): URL to the latest build that will be used to download .zip archive
        self.zip_file (str): path to the zip file on the PC
        self.target_unpack_dir (str): path where to unpack .zip
        self.product_id (str): product GUID extracted from iss template
        self.product_info_file_new (str): product.info file from downloaded build
        self.iss_template_content (list): content of EDT silent installation template
        """
        self.build_url = None
        self.zip_file = None
        self.target_unpack_dir = None
        self.product_id = None
        self.product_info_file_new = None
        self.iss_template_content = []

        settings_path = self.parse_args()
        with open(settings_path, "r") as file:
            self.settings = json.load(file, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

    def run(self):
        self.get_build_link()
        self.download_file()
        self.install()

    def check_directories(self):
        """
        Verify that installation and download path exists.
        If not tries to create a requested path
        """
        for path in ["install_path", "download_path"]:
            if not os.path.isdir(self.settings[path]):
                try:
                    os.makedirs(self.settings[path])
                except PermissionError:
                    logging.error(f"{path} could not be created due to insufficient permissions")
                    sys.exit(1)

    def get_build_link(self):
        """
        Function that sends HTTP request to JFrog and get the list of folders with builds for EDT and checks user
        password
        :modify: (str) self.build_url: URL link to the latest build that will be used to download .zip archive
        """
        password = getattr(self.settings.password, self.settings.artifactory)

        if not self.settings.username or not password:
            logging.error("Please provide username and artifactory password")
            sys.exit(1)

        server = artifactory_dict[self.settings.artifactory]
        try:
            with requests.get(server + "/api/repositories", auth=(self.settings.username, password),
                              timeout=30) as url_request:
                artifacts_list = json.loads(url_request.text)
        except requests.exceptions.ReadTimeout:
            logging.error("Timeout on connection, please verify your username and password for {}".format(
                self.settings.artifactory))
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            logging.error("Connection error, please verify that you are on VPN")
            sys.exit(1)

        # catch 401 for bad credentials or similar
        if url_request.status_code != 200:
            if url_request.status_code == 401:
                logging.error("Bad credentials, please verify your username and password for {}".format(
                    self.settings.artifactory))
            else:
                logging.error(artifacts_list["errors"][0]["message"])
            sys.exit(1)

        # fill the dictionary with EBU and WB keys since builds could be different
        # still parse the list because of different names on servers
        artifacts_dict = {}
        for artifact in artifacts_list:
            repo = artifact["key"]
            if "EBU_Certified" in repo:
                version = repo.split("_")[0] + "_EDT"
                if version not in artifacts_dict:
                    artifacts_dict[version] = repo
            elif "Certified" in repo and "Licensing" not in repo:
                version = repo.split("_")[0] + "_WB"
                if version not in artifacts_dict:
                    artifacts_dict[version] = repo

        try:
            repo = artifacts_dict[self.settings.version]
        except KeyError:
            logging.error(f"Version {self.settings.version} that you have specified " +
                          f"does not exists on {self.settings.artifactory}")
            sys.exit(1)

        if "EDT" in self.settings.version:
            url = server + "/api/storage/" + repo + "?list&deep=0&listFolders=1"
            with requests.get(url, auth=(self.settings.username, password), timeout=30) as url_request:
                folder_dict_list = json.loads(url_request.text)['files']

            builds_dates = []
            for folder_dict in folder_dict_list:
                folder_name = folder_dict['uri'][1:]
                try:
                    builds_dates.append(int(folder_name))
                except ValueError:
                    pass

            latest_build = max(builds_dates)

            version_number = self.settings.version.split('_')[0][1:]
            self.build_url = f"{server}/{repo}/{latest_build}/Electronics_{version_number}_winx64.zip"
        elif "WB" in self.settings.version:
            self.build_url = f"{server}/api/archive/download/{repo}-cache/winx64?archiveType=zip"

        if not self.build_url:
            logging.error("Cannot receive URL")
            sys.exit(1)

    def download_file(self, recursion=False):
        """
        Downloads file in chunks and saves to the temp.zip file
        Uses url to the zip archive or special JFrog API to download WB folder
        :param (bool) recursion: Some artifactories do not have cached folders with WB  and we need recursively run
        the same function but with new_url, however to prevent infinity loop we need this arg
        :modify: (str) zip_file: link to the zip file
        """
        password = getattr(self.settings.password, self.settings.artifactory)
        url = self.build_url.replace("-cache", "") if recursion else self.build_url

        with requests.get(url, auth=(self.settings.username, password), timeout=30, stream=True) as url_request:
            if url_request.status_code == 404 and not recursion:
                # in HQ cached build does not exist and will return 404. Recursively start download with new url
                self.download_file(recursion=True)
                return

            self.zip_file = os.path.join(self.settings.download_path, f"temp_build_{self.settings.version}.zip")
            logging.info(f"Start download file from {url} to {self.zip_file}")
            with open(self.zip_file, 'wb') as f:
                shutil.copyfileobj(url_request.raw, f)

            logging.info(f"File is downloaded to: {self.zip_file}")

            if not self.zip_file:
                logging.error("ZIP download failed")
                sys.exit(1)

    def install(self):
        # todo check that the same version is already installed or not before deletion
        self.target_unpack_dir = self.zip_file.replace(".zip", "")
        with zipfile.ZipFile(self.zip_file, "r") as zip_ref:
            zip_ref.extractall(self.target_unpack_dir)

        logging.info(f"File is unpacked to {self.target_unpack_dir}")

        if "EDT" in self.settings.version:
            self.install_edt()

    def install_edt(self):
        """
        Install Electronics Desktop. Make verification that the same version is not yet installed and makes
        silent installation
        :return: None
        """
        self.parse_iss()
        if self.product_id:
            logging.info(f"Product ID is {self.product_id}")
            if os.path.isfile(self.product_info_file_new):
                # file with build date exists and we can check version
                versions_different = self.compare_edt_version()
            else:
                # file does not exist for some reason, need to install any case
                pass
        else:

            return

    def uninstall(self):
        pass

    def compare_edt_version(self):
        """
        Function to compare build dates of just downloaded daily build and already installed version of EDT
        :return: (bool) True if builds dates are the same or False if different
        """
        build_date, product_version = self.get_build_date(self.product_info_file_new)

        installed_product = os.path.join(self.settings.install_path, "AnsysEM", f"AnsysEM{product_version}",
                                         "Win64", "product.info")

        installed_build_date, _unused = self.get_build_date(installed_product)

        if all([build_date, installed_build_date]) and build_date == installed_build_date:
            return True
        return False

    @staticmethod
    def get_build_date(product_info_file):
        """
        extract information about EDT build date and version
        :param product_info_file: path to the product.info
        :return:
        """
        build_date = False
        product_version = False
        if os.path.isfile(product_info_file):
            with open(product_info_file) as file:
                for line in file:
                    if "AnsProductBuildDate" in line:
                        build_date = line.split("=")[1]
                    elif "AnsProductVersion" in line:
                        product_version = line.split("=")[1]

        return build_date, product_version

    def parse_iss(self):
        """
        Open directory with unpacked build of EDT and search for SilentInstallationTemplate.iss to extract
        product ID which is GUID hash
        :modify: self.product_id: GUID of downloaded version
        :modify: self.product_info_file_new: path to the product.info file
        :modify: self.iss_template_content: append lines from template file
        """
        default_iss_file = ""
        product_id_match = []

        for dir_path, dir_names, file_names in os.walk(self.target_unpack_dir):
            for filename in file_names:
                if "AnsysEM" in dir_path and filename.endswith(".iss"):
                    default_iss_file = os.path.join(dir_path, filename)
                    self.product_info_file_new = os.path.join(dir_path, "product.info")
                    break

        if not default_iss_file:
            logging.error("SilentInstallationTemplate.iss does not exist")
            sys.exit(1)

        with open(default_iss_file, "r") as iss_file:
            for line in iss_file:
                self.iss_template_content.append(line)
                if "DlgOrder" in line:
                    guid_regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                    product_id_match = re.findall(guid_regex, line)

        if product_id_match:
            self.product_id = product_id_match[0]
        else:
            logging.error("Unable to extract product ID")
            sys.exit(1)

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
                logging.error("Settings file does not exist")
                sys.exit(1)

            logging.info(f"Settings path is set to {settings_path}")
            return settings_path


if __name__ == "__main__":
    set_log.set_logger()
    app = Downloader()
    app.run()
