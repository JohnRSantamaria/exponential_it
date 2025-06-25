import requests
import dropbox
from dropbox.files import WriteMode, GetMetadataError
from dropbox.exceptions import ApiError
from .base import FileUploader
from app.core.settings import settings


class DropboxUploader(FileUploader):
    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        app_key: str,
        app_secret: str,
    ):
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount("https://", adapter)

        self.dbx = dropbox.Dropbox(
            oauth2_access_token=access_token,
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret,
            session=session,
        )

        self.dbx._session.timeout = (60, 180)

    def upload(self, local_path: str, remote_path: str):
        with open(local_path, "rb") as f:
            self.dbx.files_upload(
                f.read(),
                remote_path,
                mode=WriteMode("overwrite"),
            )

    def exists(self, remote_path: str) -> bool:
        try:
            self.dbx.files_get_metadata(remote_path)
            return True
        except ApiError as e:
            if (
                isinstance(e.error, GetMetadataError)
                and e.error.is_path()
                and e.error.get_path().is_not_found()
            ):
                return False
            raise
