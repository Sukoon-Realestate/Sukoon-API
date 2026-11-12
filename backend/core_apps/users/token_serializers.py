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
        from .services.sessions import refresh_bound_session

        return refresh_bound_session(attrs, self.token_class)
