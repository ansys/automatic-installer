from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from sharepoint_uploader import SHAREPOINT_SITE_URL  # noqa: E402
from sharepoint_uploader import Downloader  # noqa: E402
from sharepoint_uploader import app_principal  # noqa: E402


class DataHolder:
    pass


class TransferStats(Downloader):
    def __init__(self):
        self.settings = DataHolder()

        context_auth = AuthenticationContext(url=SHAREPOINT_SITE_URL)
        context_auth.acquire_token_for_app(
            client_id=app_principal["client_id"], client_secret=app_principal["client_secret"]
        )

        self.ctx = ClientContext(SHAREPOINT_SITE_URL, context_auth)

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
            self.settings.username = item.properties["Title"]
            error = item.properties.get("error", None)

            if not item.properties["in_influx"]:
                item.set_property("in_influx", True)
                item.update()
                self.ctx.execute_query()

                self.send_statistics_to_influx(
                    tool=item.properties["tool"],
                    version=item.properties["version"],
                    time_now=item.properties["Date"],
                    error=error,
                    downloader_ver=item.properties.get("downloader_ver", "2.0.0"),
                )


if __name__ == "__main__":
    transfer = TransferStats()
    transfer.run()
