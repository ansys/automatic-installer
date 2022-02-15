import json
import unittest
from pathlib import Path

import downloader_backend

root_folder = Path(__file__).parent.parent.parent


class TestVersion(unittest.TestCase):
    version = None

    @classmethod
    def setUpClass(cls):
        """
        Grab Electron version from package.json
        Returns:

        """
        with open(root_folder.joinpath("electron_ui", "package.json")) as file:
            package = json.load(file)

        cls.version = package["version"]

    def test_downloader_backend_version(self):
        """
        Check that backend version was updated and the same as in package.json
        Returns:

        """
        self.assertEqual(self.version, downloader_backend.__version__)

    def test_whats_new_version(self):
        """
        Check that we have specified new information in what's new message window
        Returns:

        """
        with open(root_folder.joinpath("electron_ui", "web_pages", "js", "whats_new.json")) as file:
            whats_new = json.load(file)

        self.assertIn(self.version, whats_new)
