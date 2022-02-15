import io
import json
import os
import shutil
import unittest
from collections import namedtuple
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import BadZipFile
from zlib import error as zlib_err

import psutil
import responses

import downloader_backend

INPUT_DIR = Path(__file__).parent.joinpath("input")
MOCK_DATA_DIR = INPUT_DIR.joinpath("mocked_data")


class BaseSetup(unittest.TestCase):
    def setUp(self, settings_file=""):
        assert settings_file
        aedt_settings = str(INPUT_DIR.joinpath(settings_file))
        self.downloader = downloader_backend.Downloader(
            0, settings_path=aedt_settings, settings_folder=INPUT_DIR.parent
        )

        with open(MOCK_DATA_DIR.joinpath("backend_mock.json")) as file:
            self.mocked_data = json.load(file)


class DownloaderTest(BaseSetup):
    def setUp(self, settings_file=""):
        super().setUp("v221_ElectronicsDesktop_sp.json")

    def test_parse_args(self):
        with patch("sys.argv", ["__file__", r"-p", "test_file.json"]):
            with self.assertRaises(downloader_backend.DownloaderError) as err:
                self.downloader.parse_args(version=downloader_backend.__version__)

            self.assertEqual(str(err.exception), "Settings file does not exist")

        with patch("sys.argv", ["__file__"]):
            with self.assertRaises(downloader_backend.DownloaderError) as err:
                self.downloader.parse_args(version=downloader_backend.__version__)

            self.assertEqual(str(err.exception), "Please provide --path argument")

        with patch("sys.argv", ["__file__", r"-p", str(INPUT_DIR.joinpath("v221_ElectronicsDesktop_sp.json"))]):
            path = self.downloader.parse_args(version=downloader_backend.__version__)
            self.assertEqual(path, str(INPUT_DIR.joinpath("v221_ElectronicsDesktop_sp.json")))

        with patch("sys.argv", ["__file__", r"-V"]):
            with self.assertRaises(SystemExit):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                    self.downloader.parse_args(version=downloader_backend.__version__)
            self.assertEqual(mock_stdout.getvalue(), f"__file__ version: {downloader_backend.__version__}\n")

    def test_check_free_space(self):
        _ntuple_diskusage = namedtuple("usage", "free")
        with patch("shutil.disk_usage", return_value=_ntuple_diskusage(free=10 * (2 ** 30))):
            with self.assertRaises(downloader_backend.DownloaderError) as err:
                self.downloader.check_free_space("some/path", required=20)

            self.assertEqual(
                str(err.exception), "Disk space in some/path is less than 20GB. This would not be enough to proceed"
            )

    def test_check_and_make_directories(self):
        with patch("os.makedirs", side_effect=OSError("Test error")):
            with self.assertRaises(downloader_backend.DownloaderError) as err:
                self.downloader.check_and_make_directories("0/1/2")

            self.assertEqual(str(err.exception), "Test error")

        with patch("os.makedirs", side_effect=OSError("BitLocker protected drive")):
            with self.assertRaises(downloader_backend.DownloaderError) as err:
                self.downloader.check_and_make_directories("0/1/2")

            self.assertEqual(str(err.exception), "Your drive is locked by BitLocker. Please unlock!")

        with patch("os.makedirs", side_effect=PermissionError("permission")):
            with self.assertRaises(downloader_backend.DownloaderError) as err:
                self.downloader.check_and_make_directories("0/1/2")

            self.assertEqual(str(err.exception), "0/1/2 could not be created due to insufficient permissions")

    def test_check_process_lock(self):
        proc = psutil.Process(pid=0)
        proc._exe = r"C:\Program Files\AnsysEM\v221\Win64\ansysedt.exe"
        proc._name = "ansysedt.exe"
        with patch("psutil.process_iter", return_value=[proc]):
            with self.assertRaises(downloader_backend.DownloaderError) as err:
                # call without decorator
                self.downloader.check_process_lock.__wrapped__(self.downloader)

        self.assertEqual(
            str(err.exception),
            "Following processes are running from installation directory: ansysedt.exe. Please stop all processes.",
        )

    def test_subprocess_call(self):
        """
        Need to run always with shell since echo is a shell command
        Returns:

        """
        result = self.downloader.subprocess_call("echo test_str", shell=True, popen=True)
        self.assertEqual(result, "test_str")

        result = self.downloader.subprocess_call(["echo", "test_str"], shell=True, popen=True)
        self.assertEqual(result, "test_str")

        with patch("subprocess.call") as call:
            result = self.downloader.subprocess_call(["echo", "test_str"], shell=True)

            call.assert_called_with(["echo", "test_str"], shell=True)
            self.assertEqual(result, "")

        result = self.downloader.subprocess_call(["echo", "test_str"], shell=True)
        self.assertEqual(result, "")

        with patch("subprocess.call", side_effect=OSError("Test error")):
            with self.assertRaises(downloader_backend.DownloaderError) as err:
                self.downloader.subprocess_call(["echo", "test_str"])

            self.assertEqual(str(err.exception), "Please run as administrator and disable Windows UAC")

    def test_parse_iss_template(self):
        with self.assertRaises(downloader_backend.DownloaderError) as err:
            self.downloader.parse_iss_template(MOCK_DATA_DIR)
            self.assertEqual(str(err.exception), "SilentInstallationTemplate.iss does not exist")

        with TemporaryDirectory() as tmp:
            unpack_folder = os.path.join(tmp, "AnsysEM")
            os.mkdir(unpack_folder)
            shutil.copy2(MOCK_DATA_DIR.joinpath("SilentInstallationTemplate.iss"), unpack_folder)
            with self.assertRaises(downloader_backend.DownloaderError) as err:
                self.downloader.parse_iss_template(unpack_folder)
            self.assertEqual(str(err.exception), "setup.exe does not exist")

            setup_exe_tmp = os.path.join(unpack_folder, "setup.exe")
            with open(setup_exe_tmp, "w") as file:
                file.write("test")

            setup_exe, product_id, installshield_version = self.downloader.parse_iss_template(unpack_folder)
            self.assertEqual(setup_exe_tmp, setup_exe)
            self.assertEqual("22139510-d048-4650-9db9-582ee8ede17b", product_id)
            self.assertEqual("v7.00\n", installshield_version)

    def test_unpack_archive(self):
        with TemporaryDirectory() as tmp:
            arch_name = os.path.join(tmp, "test")
            self.downloader.zip_file = shutil.make_archive(arch_name, "zip", MOCK_DATA_DIR)

            self.assertFalse(os.path.isfile(os.path.join(tmp, "test", "SilentInstallationTemplate.iss")))
            self.downloader.unpack_archive()
            self.assertTrue(os.path.isfile(os.path.join(tmp, "test", "SilentInstallationTemplate.iss")))

        self.downloader.zip_file = "test.zip"
        with self.assertRaises(downloader_backend.DownloaderError) as err:
            self.downloader.unpack_archive()
        self.assertEqual(str(err.exception), "Cannot unpack due to [Errno 2] No such file or directory: 'test.zip'")

        with TemporaryDirectory() as tmp:
            arch_name = os.path.join(tmp, "test")
            self.downloader.zip_file = shutil.make_archive(arch_name, "zip", MOCK_DATA_DIR)

            self.assertFalse(os.path.isfile(os.path.join(tmp, "test", "SilentInstallationTemplate.iss")))
            with patch("zipfile.ZipFile.extractall", side_effect=OSError(28, "")):
                with self.assertRaises(downloader_backend.DownloaderError) as err:
                    self.downloader.unpack_archive()

                self.assertEqual(str(err.exception), "No disk space available in download folder!")

            with patch("zipfile.ZipFile.extractall", side_effect=zlib_err()):
                with self.assertRaises(downloader_backend.DownloaderError) as err:
                    self.downloader.unpack_archive()

                self.assertEqual(
                    str(err.exception), "Zip file is broken. Please try again later or use another repository."
                )

            with patch("zipfile.ZipFile.extractall", side_effect=BadZipFile()):
                with self.assertRaises(downloader_backend.DownloaderError) as err:
                    self.downloader.unpack_archive()

                self.assertEqual(
                    str(err.exception), "Zip file is broken. Please try again later or use another repository."
                )


class SharepointElectronicsTest(BaseSetup):
    def setUp(self, settings_file=""):
        super().setUp("v221_ElectronicsDesktop_sp.json")

    def test_versions_identical(self):
        # test aedt is not installed
        self.downloader.installed_product_info = r"test\install\dir\product.info"
        self.assertTrue(self.downloader.newer_version_exists)

        # test aedt is installed and same version
        self.downloader.installed_product_info = MOCK_DATA_DIR.joinpath("product.info")
        self.downloader.remote_build_date = "20210830"
        self.assertFalse(self.downloader.newer_version_exists)

        # test aedt is installed and remote version newer
        self.downloader.installed_product_info = MOCK_DATA_DIR.joinpath("product.info")
        self.downloader.remote_build_date = "20210930"
        self.assertTrue(self.downloader.newer_version_exists)

        # test wrong parsed remote build date
        self.downloader.installed_product_info = MOCK_DATA_DIR.joinpath("product.info")
        self.downloader.remote_build_date = "str to int"
        self.assertTrue(self.downloader.newer_version_exists)


class SharepointWorkbenchTest(BaseSetup):
    def setUp(self, settings_file=""):
        super().setUp("v221_Workbench_sp.json")

    def mock_sharepoint_auth(self):
        """
        Mock responses to authenticate Sharepoint
        Returns:
        """
        responses.add(
            responses.HEAD,
            url="https://ansys.sharepoint.com/sites/BetaDownloader",
            status=401,
            headers={
                "WWW-Authenticate": 'Bearer realm="look_at_my_burning_bear"',
            },
        )
        responses.add(
            responses.POST,
            url="https://accounts.accesscontrol.windows.net/look_at_my_burning_bear/tokens/OAuth/2",
            status=200,
            json={
                "token_type": "Bearer",
                "expires_in": "86399",
                "not_before": "1630994919",
                "expires_on": "1631081619",
                "resource": "00000003-0000/ansys.sharepoint.com@34c6ce67-15b8",
                "access_token": "my_crazy_shi_token",
            },
        )
        secrets = self.mocked_data["secrets_output"]
        with (patch("downloader_backend.Downloader.subprocess_call", return_value=secrets)):
            self.downloader.ctx = self.downloader.authorize_sharepoint()

    @responses.activate
    @patch("downloader_backend.AuthenticationContext")
    def test_authorize_sharepoint(self, token):
        self.mock_sharepoint_auth()

        token.assert_called_with(url=downloader_backend.SHAREPOINT_SITE_URL)
        token().acquire_token_for_app.assert_called_with(client_id="90906b56-2bc8-4", client_secret="bzJwrRIQJmjvZ8N")

    def test_versions_identical(self):
        # test if product is not installed
        self.downloader.product_root_path = r"test\install\dir"
        self.assertTrue(self.downloader.newer_version_exists)

        # test WB is installed and remote version newer
        self.downloader.product_root_path = MOCK_DATA_DIR
        self.downloader.remote_build_date = "202109300040"
        self.assertTrue(self.downloader.newer_version_exists)

        # test WB is installed and same version
        self.downloader.product_root_path = MOCK_DATA_DIR
        self.downloader.remote_build_date = "202108300040"
        self.assertFalse(self.downloader.newer_version_exists)

    @responses.activate
    def test_get_build_link(self):
        self.mock_sharepoint_auth()
        sharepoint_lists = self.mocked_data["sharepoint_lists"]
        responses.add(
            responses.GET,
            url="https://ansys.sharepoint.com/sites/BetaDownloader/_api/Web/lists/GetByTitle('product_list')/items",
            status=200,
            json=sharepoint_lists,
        )

        self.downloader.get_build_link()
        self.assertEqual(
            self.downloader.build_artifactory_path,
            "Shared Documents/winx64/Workbench/v221/20210902_1213/v221_Workbench.zip",
        )
        self.assertEqual(self.downloader.remote_build_date, 202109020040)

        # test exception raised
        self.downloader.settings.version = "unknown_product"
        with self.assertRaises(downloader_backend.DownloaderError) as err:
            self.downloader.get_build_link()
        self.assertEqual(str(err.exception), "No version of unknown_product is available on SharePoint")


def add_responses_for_repos(mocked_data, status=200):
    if status == 200:
        arti_get_repos = mocked_data["arti_get_repos"]
        responses.add(
            responses.GET,
            url="http://ottvmartifact.win.ansys.com:8080/artifactory/api/repositories",
            status=status,
            json=arti_get_repos,
        )
    elif status == 403:
        responses.add(
            responses.GET,
            url="http://ottvmartifact.win.ansys.com:8080/artifactory/api/repositories",
            status=status,
            json={"errors": ["Bad credentials"]},
        )
    else:
        responses.add(
            responses.GET,
            url="http://ottvmartifact.win.ansys.com:8080/artifactory/api/repositories",
            status=status,
            json={"errors": ["some error"]},
        )

    responses.add(
        responses.GET,
        url="http://ottvmartifact.win.ansys.com:8080/artifactory/api/repositories/v221_Certified",
        status=200,
        json={
            "key": "v221_Certified",
            "packageType": "maven",
            "description": " (local file cache)",
            "url": "http://azwec7artsrv01:8080/artifactory/v221_Certified",
            "rclass": "remote",
        },
    )

    responses.add(
        responses.GET,
        url="http://ottvmartifact.win.ansys.com:8080/artifactory/api/repositories/v221_EBU_Certified",
        status=200,
        json={
            "key": "v221_EBU_Certified",
            "packageType": "maven",
            "description": "",
            "url": "http://azwec7artsrv01.ansys.com:8080/artifactory/v221_EBU_Certified-cache/",
            "rclass": "remote",
        },
    )

    responses.add(
        responses.GET,
        url="http://ottvmartifact.win.ansys.com:8080/artifactory/api/repositories/v221_Development",
        status=200,
        json={
            "key": "v221_Development",
            "packageType": "maven",
            "description": " (local file cache)",
            "url": "http://azwec7artsrv01:8080/artifactory/v221_Development",
            "rclass": "remote",
        },
    )

    responses.add(
        responses.GET,
        url="http://ottvmartifact.win.ansys.com:8080/artifactory/api/repositories/v221_Licensing_Certified",
        status=200,
        json={
            "key": "v221_Licensing_Certified",
            "packageType": "maven",
            "description": " (local file cache)",
            "url": "http://azwec7artsrv01:8080/artifactory/v221_Licensing_Certified",
            "rclass": "remote",
        },
    )

    # add responses for .stat()
    responses.add(
        responses.GET,
        url="http://ottvmartifact.win.ansys.com:8080/artifactory/api/storage/v221_Certified",
        status=200,
        json={
            "repo": "v221_Certified-cache",
            "path": "/",
            "created": "2020-04-29T18:50:05.135+02:00",
            "lastModified": "2020-04-29T18:50:05.135+02:00",
            "lastUpdated": "2020-04-29T18:50:05.135+02:00",
            "children": [{"uri": "/linx64", "folder": True}, {"uri": "/winx64", "folder": True}],
            "uri": "http://ottvmartifact.win.ansys.com:8080/artifactory/api/storage/v221_Certified-cache",
        },
    )

    responses.add(
        responses.GET,
        url="http://ottvmartifact.win.ansys.com:8080/artifactory/api/storage/v221_Licensing_Certified",
        status=200,
        json={
            "repo": "v221_Licensing_Certified-cache",
            "path": "/",
            "created": "2020-09-22T16:50:03.439+02:00",
            "lastModified": "2020-09-22T16:50:03.439+02:00",
            "lastUpdated": "2020-09-22T16:50:03.439+02:00",
            "children": [
                {"uri": "/enterprise", "folder": True},
                {"uri": "/licregs", "folder": True},
                {"uri": "/linx64", "folder": True},
                {"uri": "/lsclient", "folder": True},
                {"uri": "/winx64", "folder": True},
            ],
            "uri": "http://ottvmartifact.win.ansys.com:8080/artifactory/api/storage/v221_Licensing_Certified-cache",
        },
    )


def add_responses_for_aedt_folders():
    arti_link = "http://ottvmartifact.win.ansys.com:8080/artifactory"
    for date in ["20210901", "20210902", "20210903"]:
        responses.add(
            responses.GET,
            url=f"{arti_link}/api/storage/v221_EBU_Certified-cache/{date}",
            status=200,
            json={
                "repo": "v221_EBU_Certified-cache",
                "path": "/20210902",
                "created": "2021-09-02T15:49:13.306+02:00",
                "lastModified": "2021-09-02T15:49:13.306+02:00",
                "lastUpdated": "2021-09-02T15:49:13.306+02:00",
                "children": [
                    {"uri": "/Electronics_221_linx64.tgz", "folder": False},
                    {"uri": "/Electronics_221_winx64.zip", "folder": False},
                    {"uri": "/package.info", "folder": False},
                    {"uri": "/product_linux.info", "folder": False},
                    {"uri": "/product_windows.info", "folder": False},
                ],
                "uri": f"{arti_link}/api/storage/v221_EBU_Certified-cache/{date}",
            },
        )

    responses.add(
        responses.GET,
        url=f"{arti_link}/api/storage/v221_EBU_Certified-cache/Electronics_221_winx64",
        status=200,
        json={
            "repo": "v221_EBU_Certified-cache",
            "path": "/Electronics_221_linx64",
            "created": "2021-03-31T17:43:24.603+02:00",
            "lastModified": "2021-03-31T17:43:24.603+02:00",
            "lastUpdated": "2021-03-31T17:43:24.603+02:00",
            "children": [],
            "uri": f"{arti_link}/api/storage/v221_EBU_Certified-cache/Electronics_221_winx64",
        },
    )


def add_aedt_responses(artifactory_link):
    bld_path = f"{artifactory_link}/api/storage/v221_EBU_Certified"
    for url in [bld_path, bld_path + "-cache"]:
        responses.add(
            responses.GET,
            url=url,
            status=200,
            json={
                "repo": "v221_EBU_Certified-cache",
                "path": "/",
                "created": "2021-03-31T15:47:13.460+02:00",
                "lastModified": "2021-03-31T15:47:13.460+02:00",
                "lastUpdated": "2021-03-31T15:47:13.460+02:00",
                "children": [
                    {"uri": "/20210901", "folder": True},
                    {"uri": "/20210902", "folder": True},
                    {"uri": "/20210903", "folder": True},
                    {"uri": "/Electronics_221_winx64", "folder": True},
                ],
                "uri": f"{artifactory_link}/api/storage/v221_EBU_Certified-cache",
            },
        )


class ArtifactoryElectronicsTest(BaseSetup):
    def setUp(self, settings_file=""):
        super().setUp("v221_ElectronicsDesktop_arti.json")

    @responses.activate
    def test_get_build_link(self):
        add_responses_for_repos(self.mocked_data)

        artifactory_link = "http://ottvmartifact.win.ansys.com:8080/artifactory"
        add_aedt_responses(artifactory_link)
        add_responses_for_aedt_folders()
        self.downloader.get_build_link()

        self.assertIsInstance(self.downloader.build_artifactory_path, downloader_backend.ArtifactoryPath)
        self.assertEqual(
            str(self.downloader.build_artifactory_path),
            f"{artifactory_link}/v221_EBU_Certified-cache/20210903/Electronics_221_winx64.zip",
        )

    @responses.activate
    def test_get_build_link_error_404(self):
        add_responses_for_repos(self.mocked_data, status=404)
        with self.assertRaises(downloader_backend.DownloaderError) as err:
            self.downloader.get_build_link()

        self.assertEqual(
            str(err.exception),
            ("Cannot retrieve repositories. Error: some error"),
        )

    @responses.activate
    def test_get_build_link_error_403(self):
        add_responses_for_repos(self.mocked_data, status=403)
        with self.assertRaises(downloader_backend.DownloaderError) as err:
            self.downloader.get_build_link()

        self.assertEqual(
            str(err.exception),
            "Cannot retrieve repositories. Error: Bad credentials",
        )

    def test_get_build_link_error_auth(self):
        username = self.downloader.settings.username
        self.downloader.settings.username = ""
        with self.assertRaises(downloader_backend.DownloaderError) as err:
            self.downloader.get_build_link()

        self.assertEqual(
            str(err.exception),
            "Please provide username and artifactory password",
        )

        # set username and remove password
        self.downloader.settings.username = username
        self.downloader.settings.password.Otterfing = ""
        with self.assertRaises(downloader_backend.DownloaderError) as err:
            self.downloader.get_build_link()

        self.assertEqual(
            str(err.exception),
            "Please provide username and artifactory password",
        )

        # remove password field for artifactory
        self.downloader.settings.username = username
        self.downloader.settings.artifactory = "arti_name"
        with self.assertRaises(downloader_backend.DownloaderError) as err:
            self.downloader.get_build_link()

        self.assertEqual(
            str(err.exception),
            "Please provide password for arti_name",
        )

    @responses.activate
    def test_versions_identical(self):
        artifactory_link = "http://ottvmartifact.win.ansys.com:8080/artifactory"
        bld_path = f"{artifactory_link}/v221_EBU_Certified/20210903/Electronics_221_winx64.zip"

        # test aedt is installed and remote version is newer
        self.downloader.build_artifactory_path = downloader_backend.ArtifactoryPath(bld_path, auth=("reader", "reader"))
        self.downloader.installed_product_info = MOCK_DATA_DIR.joinpath("product.info")

        responses.add(
            responses.GET,
            url=f"{artifactory_link}/v221_EBU_Certified/20210903/product_windows.info",
            status=200,
            body=(
                'AnsProductName="ANSYS Electromagnetics"\r\nAnsProductVersion="22.1"\r\n'
                'AnsProductOS="Windows"\r\nAnsProductBuildDate="2021-09-02 23:47:44"\r\n'
            ),
        )
        self.assertTrue(self.downloader.newer_version_exists)

        # test aedt is installed but remote version is older (the same)
        responses.remove(responses.GET, url=f"{artifactory_link}/v221_EBU_Certified/20210903/product_windows.info")
        responses.add(
            responses.GET,
            url=f"{artifactory_link}/v221_EBU_Certified/20210903/product_windows.info",
            status=200,
            body=(
                'AnsProductName="ANSYS Electromagnetics"\r\nAnsProductVersion="22.1"\r\n'
                'AnsProductOS="Windows"\r\nAnsProductBuildDate="2021-08-30 23:47:44"\r\n'
            ),
        )
        self.assertFalse(self.downloader.newer_version_exists)


class ArtifactoryWorkbenchTest(BaseSetup):
    def setUp(self, settings_file=""):
        super().setUp("v221_Workbench_arti.json")

    @responses.activate
    def test_get_build_link(self):
        add_responses_for_repos(self.mocked_data)
        artifactory_link = "http://ottvmartifact.win.ansys.com:8080/artifactory"
        add_aedt_responses(artifactory_link)
        self.downloader.get_build_link()

        self.assertIsInstance(self.downloader.build_artifactory_path, downloader_backend.ArtifactoryPath)
        self.assertEqual(
            str(self.downloader.build_artifactory_path),
            f"{artifactory_link}/v221_Certified-cache/winx64",
        )

    @responses.activate
    def test_versions_identical(self):
        # test installed and remote version is newer
        bld_path = "http://ottvmartifact.win.ansys.com:8080/artifactory/v221_Certified-cache/winx64"
        self.downloader.build_artifactory_path = downloader_backend.ArtifactoryPath(bld_path, auth=("reader", "reader"))
        self.downloader.product_root_path = MOCK_DATA_DIR

        responses.add(
            responses.GET,
            url=f"{bld_path}/package.id",
            status=200,
            body="Unified Package Created: 202109020040P00\nUnified Package Name: 2021-09-02 00:40 P00\n",
        )
        self.assertTrue(self.downloader.newer_version_exists)

        # test installed and remote version is older
        responses.remove(responses.GET, url=f"{bld_path}/package.id")
        responses.add(
            responses.GET,
            url=f"{bld_path}/package.id",
            status=200,
            body="Unified Package Created: 202107020040P00\nUnified Package Name: 2021-07-02 00:40 P00\n",
        )
        self.assertFalse(self.downloader.newer_version_exists)


class InstallWorkbenchTest(BaseSetup):
    def setUp(self, settings_file=""):
        super().setUp("v221_Workbench_arti.json")

    def test_uninstall_wb(self):
        with TemporaryDirectory() as tmp:
            self.downloader.product_root_path = tmp
            setup_exe_tmp = os.path.join(tmp, "Uninstall.exe")
            with open(setup_exe_tmp, "w") as file:
                file.write("test")

            with (patch("downloader_backend.Downloader.subprocess_call", wraps=lambda *args: "")) as mock_call:
                self.downloader.uninstall_wb()
                mock_call.assert_called_once_with([setup_exe_tmp, "-silent"])

                self.assertFalse(os.path.isdir(tmp))

            os.mkdir(tmp)  # recover tmp folder since it was removed during uninstall


class InstallElectronicsTest(BaseSetup):
    def setUp(self, settings_file=""):
        super().setUp("v221_ElectronicsDesktop_arti.json")

    @patch("downloader_backend.Downloader.check_result_code", wraps=lambda *args: "")
    @patch("downloader_backend.Downloader.subprocess_call", wraps=lambda *args: "")
    def test_uninstall_aedt(self, mock_subprocess, mock_check_code):
        with TemporaryDirectory() as tmp:
            self.downloader.target_unpack_dir = tmp
            self.downloader.product_root_path = os.path.join(tmp, "AnsysEM")
            self.downloader.installed_product_info = MOCK_DATA_DIR.joinpath("product.info")
            setup_exe_tmp = os.path.join(tmp, "setup.exe")
            with open(setup_exe_tmp, "w") as file:
                file.write("test")

            self.downloader.uninstall_edt(setup_exe=setup_exe_tmp, product_id="test_id", installshield_version="V1")
            mock_subprocess.assert_called_once_with(
                " ".join(
                    [
                        f'"{setup_exe_tmp}"',
                        "-uninst",
                        "-s",
                        f'-f1"{os.path.join(tmp, "uninstall.iss")}"',
                        f'-f2"{os.path.join(tmp, "uninstall.log")}"',
                    ]
                )
            )

            mock_check_code.assert_called_once()

            self.assertFalse(os.path.isdir(tmp))

            os.mkdir(tmp)  # recover tmp folder since it was removed during uninstall

    @patch("downloader_backend.Downloader.remove_aedt_shortcuts", wraps=lambda *args: "")
    @patch("downloader_backend.Downloader.update_edt_registry", wraps=lambda *args: "")
    @patch("downloader_backend.Downloader.uninstall_edt", wraps=lambda *args: "")
    @patch("downloader_backend.Downloader.check_result_code", wraps=lambda *args: "")
    @patch("downloader_backend.Downloader.subprocess_call", wraps=lambda *args: "")
    def test_install_aedt(self, mock_subprocess, mock_check_code, mock_uninstall, mock_registry, mock_shortcuts):
        with TemporaryDirectory() as tmp:
            self.downloader.target_unpack_dir = tmp
            self.downloader.product_root_path = os.path.join(tmp, "AnsysEM")
            self.downloader.installed_product_info = MOCK_DATA_DIR.joinpath("product.info")
            setup_exe_tmp = os.path.join(tmp, "setup.exe")
            with open(setup_exe_tmp, "w") as file:
                file.write("test")

            with patch(
                "downloader_backend.Downloader.parse_iss_template",
                wraps=lambda *args: "",
                return_value=(setup_exe_tmp, "22139510-d048-4650-9db9-582ee8ede17b", "v7.00\n"),
            ):
                self.downloader.install_edt()

            mock_subprocess.assert_called_once_with(
                " ".join(
                    [
                        f'"{setup_exe_tmp}"',
                        "-s",
                        f'-f1"{os.path.join(tmp, "install.iss")}"',
                        f'-f2"{os.path.join(tmp, "install.log")}"',
                    ]
                )
            )

            mock_uninstall.assert_called_once()
            mock_check_code.assert_called_once()
            mock_registry.assert_called_once()
            mock_shortcuts.assert_called_once()


class InstallLicenseManagerTest(BaseSetup):
    def setUp(self, settings_file=""):
        super().setUp("v221_LicenseManager_arti.json")

    def test_get_license_manager_build_date(self):
        self.downloader.product_root_path = "test/dir"
        with self.assertRaises(downloader_backend.DownloaderError) as err:
            date = self.downloader.get_license_manager_build_date()
        self.assertEqual(str(err.exception), "lmcenter_blddate.txt is not available")

        self.downloader.product_root_path = MOCK_DATA_DIR
        date = self.downloader.get_license_manager_build_date()
        self.assertEqual(date, 20210617)

        self.downloader.product_root_path = MOCK_DATA_DIR.joinpath("fail_files")
        with self.assertRaises(downloader_backend.DownloaderError) as err:
            date = self.downloader.get_license_manager_build_date()
        self.assertEqual(str(err.exception), "Cannot extract build date of installed License Manager")
