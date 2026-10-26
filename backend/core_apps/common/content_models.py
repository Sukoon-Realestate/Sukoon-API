from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


CONTENT_WORKSPACES = [
    ("tenant", "Individual"),
    ("owner", "Owner"),
    ("student", "Student"),
    ("company", "Company"),
    ("both", "Individual and owner"),
    ("all", "All workspaces"),
]


class ManagedContent(models.Model):
    revision = models.PositiveIntegerField(default=1, editable=False)
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PublicContentPage(ManagedContent):
    slug = models.SlugField(
        primary_key=True,
        choices=[
            ("about-us", "About us"),
            ("privacy-policy", "Privacy policy"),
            ("terms", "Terms"),
        ],
    )
    title_en = models.CharField(max_length=150)
    title_ar = models.CharField(max_length=150)
    content_en = models.TextField()
    content_ar = models.TextField()

    def clean(self):
        for field in ("title_en", "title_ar", "content_en", "content_ar"):
            if not getattr(self, field).strip():
                raise ValidationError({field: "Localized text is required."})

    def __str__(self):
        return self.title_en


class ReleaseNote(ManagedContent):
    version = models.CharField(max_length=40)
    workspace = models.CharField(
        max_length=10,
        default="both",
        choices=CONTENT_WORKSPACES,
    )
    items_en = models.TextField(
        help_text="One plain-text release note per line; at most 20."
    )
    items_ar = models.TextField(
        help_text="One plain-text release note per line; at most 20."
    )
    publish_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["version", "workspace"], name="release_note_version_workspace"
            )
        ]

    def clean(self):
        import re

        if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?", self.version):
            raise ValidationError({"version": "Use the installed application version."})
        for field in ("items_en", "items_ar"):
            items = [
                line.strip()
                for line in getattr(self, field).splitlines()
                if line.strip()
            ]
            if not 1 <= len(items) <= 20 or any(len(line) > 500 for line in items):
                raise ValidationError(
                    {field: "Supply 1 to 20 lines, each at most 500 characters."}
                )

    def __str__(self):
        return f"{self.version} / {self.workspace}"


class ContentEditAudit(models.Model):
    """Snapshots of public application copy, never commercial policy grants."""

    kind = models.CharField(max_length=40)
    object_id = models.CharField(max_length=150)
    revision = models.PositiveIntegerField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.CharField(max_length=500)
    before = models.JSONField(default=dict)
    after = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "object_id", "revision"],
                name="unique_content_edit_revision",
            )
        ]
