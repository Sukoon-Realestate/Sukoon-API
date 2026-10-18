from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from .journey import canonical_user


class CanonicalTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        from .services.sessions import issue_refresh

        return issue_refresh(user)

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = canonical_user(self.user)
        return data


class CanonicalTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        from django.db import transaction
        from django.utils import timezone
        from datetime import datetime, timezone as dt_timezone
        from rest_framework_simplejwt.exceptions import AuthenticationFailed
        from .models import User, AuthSession
        from .services.sessions import validate_session

        with transaction.atomic():
            token = self.token_class(attrs["refresh"])
            user = (
                User.objects.select_for_update().filter(id=token.get("user_id")).first()
            )
            if user is None:
                raise AuthenticationFailed("Session unavailable.")
            validate_session(user, token)
            result = super().validate(attrs)
            rotated = self.token_class(result.get("refresh", attrs["refresh"]))
            if rotated.get("session_id"):
                AuthSession.objects.filter(
                    id=rotated["session_id"], user=user, revoked_at__isnull=True
                ).update(
                    expires_at=datetime.fromtimestamp(
                        rotated["exp"], tz=dt_timezone.utc
                    )
                )
            return result
