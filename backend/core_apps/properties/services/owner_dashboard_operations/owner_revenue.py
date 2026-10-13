"""Confirmed owner payout projection for the legacy revenue entry point."""

from ..owner_revenues import owner_revenues


class OwnerRevenueMixin:
    @classmethod
    def get_revenues(cls, owner, language="ar"):
        return owner_revenues(owner, language)
