"""Djoser social adapters share the same revocable issuer as native login."""

from .sessions import issue_token_pair


class BoundTokenStrategy:
    @classmethod
    def obtain(cls, user):
        return {**issue_token_pair(user), "user": user}
