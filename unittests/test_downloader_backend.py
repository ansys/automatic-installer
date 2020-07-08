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
        with mock.patch('sys.argv', ["__file__", r'-p', test_settings["settings_file"]]):
            self.downloader = downloader_backend.Downloader()

    def download_file_test(self):
        """
            Test getting link according to settings file and download of the build from server
            Uses following mock up is used:
                arguments mock up of settings_file
        """
        self.downloader.get_build_link()
        self.downloader.download_file()

    def uninstall_wb_test(self):
        """
            Test uninstallation of Workbench
            Uses following mock up from settings file:
                downloader.settings.install_path
                downloader.settings.version
        """
        self.downloader.uninstall_wb()

    def install_wb_test(self):
        """
            Test installation of Workbench
            Uses following mock up:
                arguments mock up of settings_file
                downloader.target_unpack_dir
        """
        self.downloader.target_unpack_dir = test_settings["target_unpack_dir"]
        self.downloader.install_wb()

    def uninstall_edt_test(self):
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

    def install_edt_test(self):
        """
            Test installation of ElectronicsDesktop
            Uses following mock up:
                arguments mock up of settings_file
                downloader.target_unpack_dir
        """
        self.downloader.target_unpack_dir = test_settings["target_unpack_dir"]
        self.downloader.install_edt()

    def install_all_test(self):
        """
            Test installation of ElectronicsDesktop or Workbench depending on settings
            !! be careful not to check delete zip in settings
            Uses following mock up:
                arguments mock up of settings_file
                downloader.zip_file
        """
        self.downloader.zip_file = test_settings["zip_file"]
        self.downloader.install()

    def clean_temp_test(self):
        """
            Test cleaning of temp directory from ZIP and unpacked folder
            Uses following mock up:
                arguments mock up of settings_file
                downloader.target_unpack_dir
                downloader.zip_file
        """
        self.downloader.target_unpack_dir = test_settings["target_unpack_dir"]
        self.downloader.clean_temp()

    def update_registry_test(self):
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

    def write_history_test(self):
        """
            Test if the history of installation was written correct
            Uses following mock up:
                arguments mock up of settings_file
        """
        self.downloader.update_installation_history("Failed", "VPN turned off")

    def statistics_test(self):
        """
        Verify how statistics is written to database
        :return:
        """
        self.downloader.send_statistics()

    def full_run_test(self):
        self.downloader.run()


if __name__ == '__main__':
    # unittest.main()
    suite = unittest.TestSuite()
    # suite.addTest(InstallUninstallTest("download_file_test"))
    # suite.addTest(InstallUninstallTest("install_edt_test"))
    # suite.addTest(InstallUninstallTest("uninstall_edt_test"))
    # suite.addTest(InstallUninstallTest("update_registry_test"))
    # suite.addTest(InstallUninstallTest("clean_temp_test"))
    # suite.addTest(InstallUninstallTest("uninstall_wb_test"))
    # suite.addTest(InstallUninstallTest("install_wb_test"))
    # suite.addTest(InstallUninstallTest("install_all_test"))
    # suite.addTest(InstallUninstallTest("write_history_test"))
    suite.addTest(InstallUninstallTest("statistics_test"))
    # suite.addTest(InstallUninstallTest("full_run_test"))
    runner = unittest.TextTestRunner()
    runner.run(suite)
