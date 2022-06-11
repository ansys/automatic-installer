from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from sharepoint_uploader import SHAREPOINT_SITE_URL
from sharepoint_uploader import SharepointUpload
from sharepoint_uploader import app_principal


class SharepointCleaner(SharepointUpload):
    def __init__(self):
        context_auth = AuthenticationContext(url=SHAREPOINT_SITE_URL)
        context_auth.acquire_token_for_app(
            client_id=app_principal["client_id"], client_secret=app_principal["client_secret"]
        )

        self.ctx = ClientContext(SHAREPOINT_SITE_URL, context_auth)

    def remove_files(self, dry_run=True):
        """
        Loops through Windows and Linux lists and deletes all folder except latest for each product
        Args:
            dry_run: (bool) if True just prints output without actual deletion

        Returns: None
        """
        for dist in ["linx64", "winx64"]:
            items = super().get_list_items(dist)
            items_to_keep = {}
            for item in items:
                title = item.properties["Title"]
                if title not in items_to_keep:
                    # ensure at least one item to be kept
                    items_to_keep[title] = item
                    continue

                if item.properties["build_date"] > items_to_keep[title].properties["build_date"]:
                    item_to_delete = items_to_keep.pop(title)
                    items_to_keep[title] = item
                else:
                    item_to_delete = item

                if dry_run:
                    print(f"Will delete {title}: {item_to_delete.properties['build_date']} ({dist})")
                else:
                    folder_url = item_to_delete.properties["relative_url"].rsplit("/", maxsplit=1)[0]
                    remote_folder = self.ctx.web.get_folder_by_server_relative_url(
                        f"/sites/BetaDownloader/{folder_url}"
                    )
                    self.ctx.execute_query()
                    remote_folder.delete_object()
                    item_to_delete.delete_object()

            if dry_run:
                print("#" * 30)
                for key, val in items_to_keep.items():
                    print(f"Will keep {key}: {val.properties['build_date']} ({dist})")
                print("#" * 30, "\n\n\n")

        self.ctx.execute_query()


def main():
    cleaner = SharepointCleaner()
    cleaner.remove_files(dry_run=False)


if __name__ == "__main__":
    main()
