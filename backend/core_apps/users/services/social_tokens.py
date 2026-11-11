"""Djoser social adapters share the same revocable issuer as native login."""

from .sessions import issue_refresh


class BoundTokenStrategy:
    @classmethod
    def obtain(cls, user):
        refresh = issue_refresh(user)
        return {"access": str(refresh.access_token), "refresh": str(refresh), "user": user}
