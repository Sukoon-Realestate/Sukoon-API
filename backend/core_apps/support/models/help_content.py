from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from core_apps.common.content_models import ManagedContent, CONTENT_WORKSPACES


class HelpContact(ManagedContent):
    workspace = models.CharField(
        primary_key=True,
        max_length=10,
        choices=CONTENT_WORKSPACES[:4],
    )
    phone = models.CharField(
        max_length=25, blank=True, validators=[RegexValidator(r"^\+?[0-9 ()-]{7,25}$")]
    )
    email = models.EmailField(blank=True)
    hours_en = models.CharField(max_length=200, blank=True)
    hours_ar = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.workspace


class HelpArticle(ManagedContent):
    slug = models.SlugField(primary_key=True)
    workspace = models.CharField(
        max_length=10,
        choices=CONTENT_WORKSPACES,
    )
    question_en = models.CharField(max_length=250)
    question_ar = models.CharField(max_length=250)
    answer_en = models.TextField()
    answer_ar = models.TextField()
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "slug"]

    def clean(self):
        for field in ("question_en", "question_ar", "answer_en", "answer_ar"):
            if not getattr(self, field).strip():
                raise ValidationError({field: "Localized text is required."})

    def __str__(self):
        return self.question_en
