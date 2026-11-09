"""Recheck the caller's original authenticated session after taking locks.

Authentication validates the session when the request starts. A command that
then waits for a domain lock must not complete for a session revoked in the
meantime (``revoke_all`` bumps the account's ``security_epoch``). This reads
the current account row after the caller's locks are held and compares it with
the original token claims, preserving them across validation, locked writes,
replay and upload completion.
"""


def recheck_session(request):
    claims = getattr(request, "auth", None)
    if not claims or not hasattr(claims, "get"):
        # Session-less test clients and non-JWT authentication have no claims.
        return
    from core_apps.users.models import User
    from core_apps.users.services.sessions import validate_session

    validate_session(User.objects.get(pk=request.user.pk), claims)
