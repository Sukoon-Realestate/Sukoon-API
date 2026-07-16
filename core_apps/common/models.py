from django.db import IntegrityError, models
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    pkid = models.BigAutoField(primary_key=True, editable=False)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at", "-updated_at"]


class ContentView(TimeStampedModel):
    content_type = models.ForeignKey(
        ContentType, verbose_name=_("Content type"), on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField(_("Object ID"))
    content_object = GenericForeignKey("content_type", "object_id")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Content Views"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    viewer_ip = models.GenericIPAddressField(_("Viewer IP"), null=True, blank=True)

    last_viewed = models.DateTimeField()

    class Meta:
        verbose_name = _("Content View")
        verbose_name_plural = _("Content Views")
        unique_together = (
            "content_type",
            "object_id",
            "user",
            "viewer_ip",
        )

    def __str__(self):
        viewer = self.user.get_full_name if self.user else "Anonymous"
        return f"{self.content_type} viewed by {viewer} from ip {self.viewer_ip}"

    @classmethod
    def record_view(cls, content_object, user: "User", viewer_ip: str) -> None:
        content_type = ContentType.objects.get_for_model(content_object)

        try:
            view, created = cls.objects.get_or_create(
                content_type=content_type,
                object_id=content_type.pkid,
                defaults={user: user, viewer_ip: viewer_ip},
            )
            if not created:
                pass
        except IntegrityError:
            pass
