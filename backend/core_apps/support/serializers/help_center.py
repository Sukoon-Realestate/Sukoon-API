from rest_framework import serializers


class FAQSerializer(serializers.Serializer):
    revision = serializers.IntegerField(read_only=True)
    id = serializers.CharField(read_only=True)
    question = serializers.CharField(read_only=True)
    answer = serializers.CharField(read_only=True)


class HelpCenterSerializer(serializers.Serializer):
    revision = serializers.IntegerField(read_only=True)
    phone = serializers.CharField(read_only=True, allow_blank=True)
    email = serializers.CharField(read_only=True, allow_blank=True)
    hours = serializers.CharField(read_only=True, allow_blank=True)
    faqs = FAQSerializer(many=True, read_only=True)
