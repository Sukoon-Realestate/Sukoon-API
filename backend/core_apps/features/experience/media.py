"""Delivery-only variants. Originals and access types are never rewritten."""
from .access import enabled


def variants(asset):
    if not enabled('media') or not asset or not getattr(asset, 'public_id', None):
        return {}
    # Private/signed evidence needs its existing authorized delivery service.
    if getattr(asset, 'type', 'upload') not in {None, 'upload'}:
        return {}
    return {name: asset.build_url(secure=True, crop='limit', width=size, height=size,
        quality=quality, fetch_format='auto') for name, size, quality in [
            ('small', 480, 'auto:eco'), ('medium', 1080, 'auto:good')
        ]}
