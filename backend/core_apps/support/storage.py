import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupportPrivateStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(file_permissions_mode=0o600, directory_permissions_mode=0o700)

    @property
    def base_location(self):
        return getattr(
            settings,
            "SUPPORT_PRIVATE_MEDIA_ROOT",
            str(settings.BASE_DIR / "private_support_media"),
        )

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        raise NotImplementedError("Support attachments require an authorized read.")
