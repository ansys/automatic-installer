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

root_folder = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)

from downloader_backend import Downloader, set_logger, retry
from pathlib import Path
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext

site_url = "https://ansys.sharepoint.com/sites/BetaDownloader"

app_principal = {
    'client_id': os.environ["client_id"],
    'client_secret': os.environ["client_secret"]
}

__version__ = "v1.0.0"


def main():
    settings_folder = r"/home/downloader_settings"
    set_logger(os.path.join(settings_folder, "uploader.log"))

    for file in os.listdir(settings_folder):
        settings_file = os.path.join(settings_folder, file)
        _, file_extension = os.path.splitext(settings_file)
        if file_extension == ".json" and "installation_history.json" not in settings_file:
            upload_to_sharepoint(settings_file)


@retry(Exception, 4)
def upload_to_sharepoint(settings_file):
    sp = SharepointUpload(settings_file)
    sp.get_build_link()

    # validate that we do not have such build already
    build_date = sp.get_new_build_date()
    all_items = sp.get_list_items()
    for item in all_items:
        if item.properties['Title'] == sp.settings.version and item.properties['build_date'] == build_date:
            print("Build is up to date")
            return

    sp.download_file()

    zip_file = Path(sp.zip_file)
    new_name = zip_file.parent.joinpath(sp.settings.version + ".zip")
    zip_file.rename(new_name)

    version, product = sp.settings.version.split("_")
    time_now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    try:
        folder_url = sp.upload_file_to_sp(str(new_name), product, version, time_now)
    except SystemExit:
        # recreate upload session
        sp = SharepointUpload(settings_file)
        folder_url = sp.upload_file_to_sp(str(new_name), product, version, time_now)

    sp.add_list_item(f"{folder_url}/{new_name.name}", int(build_date), folder_url)
    new_name.unlink()


class SharepointUpload(Downloader):
    def __init__(self, settings_path):
        super().__init__(__version__, r"/home/downloader_settings", settings_path)
        context_auth = AuthenticationContext(url=site_url)
        context_auth.acquire_token_for_app(client_id=app_principal['client_id'],
                                           client_secret=app_principal['client_secret'])

        self.ctx = ClientContext(site_url, context_auth)

    @retry(Exception, 4, delay=60, backoff=2)
    def upload_file_to_sp(self, file_path, *remote_path):
        folder_url = "/".join(["Shared Documents", "beta_builds"] + list(remote_path))
        target_folder = self.ctx.web.ensure_folder_path(folder_url)

        size_chunk = 100 * 1024 * 1024  # MB
        file_size = os.path.getsize(file_path)

        if file_size > size_chunk:
            result_file = target_folder.files.create_upload_session(file_path, size_chunk,
                                                                    self.print_upload_progress, file_size)
        else:
            with open(file_path, 'rb') as content_file:
                file_content = content_file.read()
            name = os.path.basename(file_path)
            result_file = target_folder.upload_file(name, file_content)
        self.ctx.execute_query()
        print('File {0} has been uploaded successfully'.format(result_file.serverRelativeUrl))
        return folder_url

    @retry(Exception, 4)
    def add_list_item(self, file_url, build_date, folder_url):
        product_list = self.ctx.web.lists.get_by_title("product_list")
        product_list.add_item({"Title": self.settings.version,
                               "build_date": build_date,
                               "relative_url": file_url,
                               "shareable_folder": f"{site_url}/{folder_url}"})
        self.ctx.execute_query()

    @retry(Exception, 4)
    def get_list_items(self):
        product_list = self.ctx.web.lists.get_by_title("product_list")
        items = product_list.items
        self.ctx.load(items)
        self.ctx.execute_query()
        return items

    @staticmethod
    def print_upload_progress(offset, total_size):
        logging.info("Uploaded '{}' MB from '{}'...[{}%]".format(round(offset/1024/1024, 2),
                                                                 round(total_size/1024/1024, 0),
                                                                 round(offset/total_size * 100, 2)))


if __name__ == '__main__':
    main()
