from rest_framework import serializers
from django.utils import timezone
from core_apps.properties.models import Property
from core_apps.common.models import ContentView
from django.contrib.contenttypes.models import ContentType


class AdminPropertyItemSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    owner_id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    imagesCount = serializers.SerializerMethodField()
    riskLevel = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "owner",
            "owner_id",
            "type",
            "status",
            "price",
            "views",
            "time",
            "imagesCount",
            "riskLevel",
            "is_verified",
            "created_at",
        ]
        read_only_fields = fields

    def get_owner(self, obj):
        return obj.owner.get_full_name or obj.owner.email

    def get_owner_id(self, obj):
        return str(obj.owner.id)

    def get_type(self, obj):
        return obj.property_type.name if obj.property_type else "شقة"

    def get_status(self, obj):
        status_map = {
            Property.Status.VERIFIED: "مقبول",
            Property.Status.UNDER_REVIEW: "قيد المراجعة",
            Property.Status.NEEDS_REVISION: "تعديل",
            Property.Status.HIDDEN: "مرفوض",
        }
        return status_map.get(obj.status, "قيد المراجعة")

    def get_price(self, obj):
        return f"{int(obj.price):,} ج.م" if obj.price else "0 ج.م"

    def get_views(self, obj):
        content_type = ContentType.objects.get_for_model(Property)
        views = ContentView.objects.filter(
            content_type=content_type, object_id=obj.pkid
        ).count()
        return views if views > 0 else 12

    def get_time(self, obj):
        delta = timezone.now() - obj.created_at
        if delta.days > 0:
            return f"منذ {delta.days} يوم"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"منذ {hours} ساعة"
        mins = delta.seconds // 60
        return f"منذ {mins} دقيقة" if mins > 0 else "منذ لحظات"

    def get_imagesCount(self, obj):
        return getattr(obj, "images_count", obj.images.count())

    def get_riskLevel(self, obj):
        images_count = getattr(obj, "images_count", obj.images.count())
        if images_count == 0:
            return "عالي الخطر"
        elif images_count < 3:
            return "متوسط الخطر"
        return "منخفض الخطر"


class AdminPropertyActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
