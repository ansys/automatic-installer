import json
import os
import shutil
import unittest
from unittest import mock

import downloader_backend

with open("tests_config.json") as file:
    test_settings = json.load(file)


class InstallUninstallTest(unittest.TestCase):
    def setUp(self):
        root_folder = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
        settings_file = os.path.join(root_folder, test_settings["settings_file"])

        with mock.patch('sys.argv', ["__file__", r'-p', settings_file]):
            self.downloader = downloader_backend.Downloader(version="Test")
            if self.downloader.settings.artifactory == "SharePoint":
                self.downloader.ctx = self.downloader.authorize_sharepoint()

    def test_01_download_file(self):
        """
            Test getting link according to settings file and download of the build from server
            Uses following mock up is used:
                arguments mock up of settings_file
        """
        self.downloader.get_build_link()
        self.downloader.download_file()

    def test_02_uninstall_wb(self):
        """
            Test uninstallation of Workbench
            Uses following mock up from settings file:
                downloader.settings.install_path
                downloader.settings.version
        """
        self.downloader.uninstall_wb()

    def test_03_install_wb(self):
        """
            Test installation of Workbench
            Uses following mock up:
                arguments mock up of settings_file
                downloader.target_unpack_dir
        """
        self.downloader.target_unpack_dir = test_settings["target_unpack_dir"]
        self.downloader.install_wb()

    def test_04_uninstall_edt(self):
        """
            Test uninstallation of ElectronicsDesktop
            Uses following mock up:
                arguments mock up of settings_file
                downloader.target_unpack_dir
                downloader.installed_product
        """
        self.downloader.target_unpack_dir = test_settings["target_unpack_dir"]
        self.downloader.parse_iss()
        self.downloader.uninstall_edt()

    def test_05_install_edt(self):
        """
            Test installation of ElectronicsDesktop
            Uses following mock up:
                arguments mock up of settings_file
                downloader.target_unpack_dir
        """
        self.downloader.target_unpack_dir = test_settings["target_unpack_dir"]
        self.downloader.install_edt()

    def test_06_install_all(self):
        """
            Test installation of ElectronicsDesktop or Workbench depending on settings
            !! be careful not to check delete zip in settings
            Uses following mock up:
                arguments mock up of settings_file
                downloader.zip_file
        """
        self.downloader.zip_file = test_settings["zip_file"]
        self.downloader.install()

    def test_07_clean_temp(self):
        """
            Test cleaning of temp directory from ZIP and unpacked folder
            Uses following mock up:
                arguments mock up of settings_file
                downloader.target_unpack_dir
                downloader.zip_file
        """
        self.downloader.target_unpack_dir = test_settings["target_unpack_dir"]
        self.downloader.clean_temp()

    def test_08_update_registry(self):
        """
        Test update of the registry in the AEDT
        :return:
        """
        hpc_folder = os.path.join(os.environ["APPDATA"], "build_downloader", "HPC_Options")
        if not os.path.isdir(hpc_folder):
            os.makedirs(hpc_folder)

        for file in os.listdir(os.path.join("input", "hpc_test")):
            if ".acf" in file:
                shutil.copy(os.path.join("input", "hpc_test", file), os.path.join(hpc_folder, file))

        self.downloader.update_edt_registry()

    def test_09_write_history(self):
        """
            Test if the history of installation was written correct
            Uses following mock up:
                arguments mock up of settings_file
        """
        self.downloader.update_installation_history("Failed", "VPN turned off")

    def test_10_statistics(self):
        """
        Verify how statistics is written to database
        :return:
        """
        self.downloader.send_statistics()
        self.downloader.send_statistics(error="test\nline 121")

    def test_11_full_run(self):
        self.downloader.run()

    def test_12_get_sharepoint_url(self):
        """
        Gets latest url for the build located on SP
        """
        list_str = self.downloader.get_sharepoint_build_info()
        print(self.downloader.build_url)

    def test_13_remove_shortcuts(self):

        self.downloader.remove_aedt_shortcuts()


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(InstallUninstallTest("full_run"))
    runner = unittest.TextTestRunner()
    runner.run(suite)
