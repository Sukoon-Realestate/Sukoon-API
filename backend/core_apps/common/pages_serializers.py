from rest_framework import serializers


class PageContentSerializer(serializers.Serializer):
    slug = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    content_format = serializers.CharField(read_only=True, default="plain_text")
    language = serializers.CharField(read_only=True, default="en")
    updated_at = serializers.DateTimeField(read_only=True)
