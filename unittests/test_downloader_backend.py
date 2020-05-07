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

            # following setup is overwritten in full_run_test
            self.downloader.installed_product = test_settings["installed_product"]
            self.downloader.target_unpack_dir = test_settings["target_unpack_dir"]
            self.downloader.product_version = test_settings["product_version"]

    def uninstall_test(self):
        self.downloader.parse_iss()
        self.downloader.uninstall_edt()

    def install_test(self):
        self.downloader.install_edt()

    def clean_temp_test(self):
        self.downloader.clean_temp()

    def update_registry_test(self):
        hpc_folder = os.path.join(os.environ["APPDATA"], "build_downloader", "HPC_Options")
        if not os.path.isdir(hpc_folder):
            os.makedirs(hpc_folder)

        for file in os.listdir(os.path.join("input", "hpc_test")):
            if ".acf" in file:
                shutil.copy(os.path.join("input", "hpc_test", file), os.path.join(hpc_folder, file))

        self.downloader.update_edt_registry()

    def full_run_test(self):
        self.downloader.run()


if __name__ == '__main__':
    # unittest.main()
    suite = unittest.TestSuite()
    # suite.addTest(InstallUninstallTest("install_test"))
    # suite.addTest(InstallUninstallTest("uninstall_test"))
    # suite.addTest(InstallUninstallTest("update_registry_test"))
    # suite.addTest(InstallUninstallTest("clean_temp_test"))
    suite.addTest(InstallUninstallTest("full_run_test"))
    runner = unittest.TextTestRunner()
    runner.run(suite)
