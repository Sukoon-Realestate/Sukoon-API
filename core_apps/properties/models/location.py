from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel


ARABIC_TRANSLITERATION = str.maketrans(
    {
        "ا": "a",
        "أ": "a",
        "إ": "i",
        "آ": "aa",
        "ب": "b",
        "ت": "t",
        "ث": "th",
        "ج": "j",
        "ح": "h",
        "خ": "kh",
        "د": "d",
        "ذ": "dh",
        "ر": "r",
        "ز": "z",
        "س": "s",
        "ش": "sh",
        "ص": "s",
        "ض": "d",
        "ط": "t",
        "ظ": "z",
        "ع": "a",
        "غ": "gh",
        "ف": "f",
        "ق": "q",
        "ك": "k",
        "ل": "l",
        "م": "m",
        "ن": "n",
        "ه": "h",
        "ة": "a",
        "و": "w",
        "ؤ": "w",
        "ي": "y",
        "ى": "a",
        "ئ": "y",
        "ء": "",
        "ـ": "",
        "پ": "p",
        "چ": "ch",
        "ژ": "zh",
        "گ": "g",
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
    }
)


def slugify_location_name(name):
    """Create an ASCII slug, transliterating Arabic characters first."""
    return slugify(name.translate(ARABIC_TRANSLITERATION))


def get_unique_slug(model, base_slug, exclude_pkid=None, **filters):
    """Return a slug unique within the supplied model queryset."""
    slug = base_slug or "location"
    candidate = slug
    suffix = 2
    queryset = model.objects.filter(**filters)
    if exclude_pkid:
        queryset = queryset.exclude(pkid=exclude_pkid)

    while queryset.filter(slug=candidate).exists():
        candidate = f"{slug}-{suffix}"
        suffix += 1
    return candidate


class Governorate(TimeStampedModel):
    name = models.CharField(_("Name"), max_length=100, unique=True)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = _("Governorate")
        verbose_name_plural = _("Governorates")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = get_unique_slug(
            Governorate, slugify_location_name(self.name), exclude_pkid=self.pkid
        )
        super().save(*args, **kwargs)


class City(TimeStampedModel):
    governorate = models.ForeignKey(
        Governorate,
        on_delete=models.PROTECT,
        related_name="cities",
        verbose_name=_("Governorate"),
    )
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["governorate", "name"], name="unique_city_name_per_governorate"
            ),
            models.UniqueConstraint(
                fields=["governorate", "slug"], name="unique_city_slug_per_governorate"
            ),
        ]

    def __str__(self):
        return f"{self.name}, {self.governorate.name}"

    def save(self, *args, **kwargs):
        self.slug = get_unique_slug(
            City,
            slugify_location_name(self.name),
            exclude_pkid=self.pkid,
            governorate=self.governorate,
        )
        super().save(*args, **kwargs)
