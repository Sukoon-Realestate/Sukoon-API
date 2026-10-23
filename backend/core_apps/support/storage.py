from django.utils.deconstruct import deconstructible
from core_apps.common.private_storage import DurablePrivateStorage


@deconstructible
class SupportPrivateStorage(DurablePrivateStorage):
    maximum_bytes = 50 * 1024 * 1024
    root_setting = "SUPPORT_PRIVATE_MEDIA_ROOT"
    provider_setting = "SUPPORT_PRIVATE_STORAGE_PROVIDER"
    prefix_setting = "SUPPORT_CLOUDINARY_PREFIX"
    default_root = "private_support_media"
    default_prefix = "sokoun-support-private"
