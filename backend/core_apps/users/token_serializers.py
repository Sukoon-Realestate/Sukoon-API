from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .journey import canonical_user


class CanonicalTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = canonical_user(self.user)
        return data
