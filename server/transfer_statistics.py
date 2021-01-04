import os
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext
import sys

root_folder = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
from sharepoint_uploader import app_principal, site_url
import downloader_backend


class DataHolder:
    pass

class TransferStats(downloader_backend.Downloader):
    def __init__(self):
        self.settings = DataHolder()

        context_auth = AuthenticationContext(url=site_url)
        context_auth.acquire_token_for_app(client_id=app_principal['client_id'],
                                           client_secret=app_principal['client_secret'])

        self.ctx = ClientContext(site_url, context_auth)

    def run(self):
        """
        Start parsing sharepoint lists
        Returns:
        """
        for database in ["statistics", "crashes"]:
            list_source = self.ctx.web.lists.get_by_title(database)
            items = list_source.items
            self.ctx.load(items)
            self.ctx.execute_query()

            self.transfer_items(items)

    def transfer_items(self, items):
        """
        Transfers items from SharePoint list items to InfluxDB
        Args:
            items: SharePoint list of items

        Returns:
            None
        """
        for item in items:
            self.settings.artifactory = "SharePoint"
            self.settings.username = item.properties['Title']
            error = item.properties.get("error", None)

            if item.properties['downloader_ver']:
                downloader_backend.__version__ = item.properties['downloader_ver']
            else:
                downloader_backend.__version__ = "2.0.0"

            if not item.properties["in_influx"]:
                item.set_property('in_influx', True)
                item.update()
                self.ctx.execute_query()

                self.send_statistics_to_influx(tool=item.properties['tool'],
                                               version=item.properties['version'],
                                               time_now=item.properties['Date'],
                                               error=error)


if __name__ == '__main__':
    transfer = TransferStats()
    transfer.run()
