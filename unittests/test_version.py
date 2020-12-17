import os
import json
import sys
import unittest

root_folder = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
import downloader_backend


class TestVersion(unittest.TestCase):
    version = None
    root_folder = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @classmethod
    def setUpClass(cls):
        """
        Grab Electron version from package.json
        Returns:

        """
        with open(os.path.join(cls.root_folder, "electron_ui", "package.json")) as file:
            package = json.load(file)

        cls.version = package["version"]

    def test_downloader_backend_version(self):
        """
        Check that backend version was updated and the same as in package.json
        Returns:

        """
        self.assertEqual(TestVersion.version, downloader_backend.__version__)

    def test_whats_new_version(self):
        """
        Check that we have specified new information in what's new message window
        Returns:

        """
        with open(os.path.join(TestVersion.root_folder, "electron_ui", "js", "whats_new.json")) as file:
            whats_new = json.load(file)

        self.assertIn(TestVersion.version, whats_new)


if __name__ == '__main__':
    unittest.main()
