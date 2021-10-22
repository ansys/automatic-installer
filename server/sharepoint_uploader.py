#  The app identifier has been successfully created.
# Client Id:   	os.environ["client_id"]
# Client Secret:   	os.environ["client_secret"]
# Title:   	python_api_2020_11_13
# App Domain:   	localhost
# Redirect URI:   	https://localhost
import datetime
import logging
import os
import sys

from pid import PidFile, PidFileError

root_folder = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)

from downloader_backend import Downloader, set_logger, retry, SHAREPOINT_SITE_URL
from pathlib import Path
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext

app_principal = {"client_id": os.environ["client_id"], "client_secret": os.environ["client_secret"]}

__version__ = "v2.0.0"


class UploaderError(Exception):
    pass


def main():
    """
    Main function that runs only if process is not locked (cannot run in parallel)
    parses folder with all settings files and starts a process for each of them
    Returns:

    """
    settings_folder = r"/home/electron/downloader_settings"
    set_logger(os.path.join(settings_folder, "uploader.log"))
    with PidFile():
        for file in os.listdir(settings_folder):
            settings_file = os.path.join(settings_folder, file)
            _, file_extension = os.path.splitext(settings_file)
            if file_extension == ".json" and "installation_history.json" not in settings_file:
                for dist in ["winx64", "linx64"]:
                    try:
                        upload_to_sharepoint(settings_file, distribution=dist)
                    except:
                        continue


@retry(Exception, 4, logger=logging)
def upload_to_sharepoint(settings_file, distribution):
    """
    Check that latest build is not yet on Sharepoint. Download from Artifactory and upload to Sharepoint.
    Add new build date to list of product on SP
    Args:
        settings_file: path to file with download settings
        distribution: linux or windows distribution selection

    Returns:

    """
    sp = SharepointUpload(settings_file)
    sp.get_build_link(distribution=distribution)

    # validate that we do not have such build already
    if "LicenseManager" in sp.settings.version:
        # todo once with have builddate.txt on Artifactory we need to change it
        build_date = int(datetime.datetime.now().strftime("%Y%m%d"))
    else:
        build_date = sp.get_new_build_date(distribution=distribution)

    all_items = sp.get_list_items(distribution=distribution)
    for item in all_items:
        if item.properties["Title"] == sp.settings.version and item.properties["build_date"] == build_date:
            logging.info(f"Build is up to date {item.properties['build_date']} == {build_date}")
            return

    sp.download_file()

    archive_file = Path(sp.zip_file)

    version, product = sp.settings.version.split("_")
    time_now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    folder_url = sp.prepare_upload(archive_file, distribution, product, version, time_now)

    if not folder_url:
        raise UploaderError("folder_url is None")

    sp.add_list_item(f"{folder_url}/{archive_file.name}", int(build_date), folder_url, distribution=distribution)
    archive_file.unlink()


class SharepointUpload(Downloader):
    def __init__(self, settings_path):
        super().__init__(__version__, r"/home/electron/downloader_settings", settings_path)
        context_auth = AuthenticationContext(url=SHAREPOINT_SITE_URL)
        context_auth.acquire_token_for_app(
            client_id=app_principal["client_id"], client_secret=app_principal["client_secret"]
        )

        self.ctx = ClientContext(SHAREPOINT_SITE_URL, context_auth)

    def prepare_upload(self, file_path, *remote_path):
        """
        Create remote folder and call upload a file
        Args:
            file_path: local file path
            *remote_path: list with subfolders for remote path

        Returns: (str) URL with remote path to the folder

        """
        folder_url = "/".join(["Shared Documents"] + list(remote_path))
        target_folder = self.ctx.web.ensure_folder_path(folder_url)
        self.ctx.execute_query()  # execute, otherwise upload stuck

        size_chunk_mb = 100
        size_chunk = size_chunk_mb * 1024 * 1024
        logging.info(f"Start uploading {file_path} to {folder_url}")
        try:
            self.upload_file(file_path, size_chunk, target_folder)
        except UploaderError:
            target_folder.recycle()

        return folder_url

    @retry(Exception, 10, delay=60, backoff=1, logger=logging)
    def upload_file(self, file_path, size_chunk, target_folder):
        """
        Upload a file to Sharepoint and validate its size
        Args:
            file_path: local file path
            size_chunk: size of chunks to upload, in bytes
            target_folder: office365 folder object

        Returns: None
        """

        file_size = file_path.stat().st_size
        result_file = target_folder.files.create_upload_session(
            str(file_path), size_chunk, self.print_upload_progress, file_size
        )

        self.ctx.execute_query_retry(
            max_retry=100,
            exceptions=(Exception,),
            failure_callback=lambda attempt, err: self.log_fail(attempt, err, total=100),
        )

        remote_size = result_file.length
        if remote_size is None or abs(file_size - remote_size) > 0.03 * file_size:
            logging.warning(f"Remote size is {remote_size}. Local is {file_size}. File isn't fully uploaded, recycle")
            result_file.recycle()
            self.ctx.execute_query()
            raise UploaderError("File size difference is more than 3%")

        logging.info("File {0} has been uploaded successfully".format(result_file.serverRelativeUrl))

    @retry(Exception, 4, logger=logging)
    def add_list_item(self, file_url, build_date, folder_url, distribution):
        """
        Add information about uploaded file to Sharepoint list
        Args:
            file_url: direct download URL of the build file
            build_date: parsed build date of the file
            folder_url: URL of the folder where archive is locate
            distribution: lin or win
        Returns: None
        """

        title = "product_list" if distribution == "winx64" else "linux_product_list"

        product_list = self.ctx.web.lists.get_by_title(title)
        product_list.add_item(
            {
                "Title": self.settings.version,
                "build_date": build_date,
                "relative_url": file_url,
                "shareable_folder": f"{SHAREPOINT_SITE_URL}/{folder_url}",
            }
        )
        self.ctx.execute_query()

    @retry(Exception, 4, logger=logging)
    def get_list_items(self, distribution):
        """
        Get list of all items available on SP
        Args:
            distribution: linx64 or winx64

        Returns: (list) list of all items

        """
        title = "product_list" if distribution == "winx64" else "linux_product_list"
        product_list = self.ctx.web.lists.get_by_title(title)
        items = product_list.items
        self.ctx.load(items)
        self.ctx.execute_query()
        return items

    @staticmethod
    def print_upload_progress(offset, total_size):
        logging.info(
            "Uploaded '{}' MB from '{}'...[{}%]".format(
                round(offset / 1024 / 1024, 2), round(total_size / 1024 / 1024, 0), round(offset / total_size * 100, 2)
            )
        )

    @staticmethod
    def log_fail(attempt, err, total):
        logging.warning(f"Attempt: {attempt}/{total}. Execution failed due to {err}")


if __name__ == "__main__":
    try:
        main()
    except PidFileError:
        logging.info("Process is already running")
