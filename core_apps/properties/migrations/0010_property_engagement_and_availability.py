# Generated manually for mobile property-detail and visit-availability support.

import uuid

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


def timestamped_fields():
    return [
        (
            "pkid",
            models.BigAutoField(editable=False, primary_key=True, serialize=False),
        ),
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("updated_at", models.DateTimeField(auto_now=True)),
    ]


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("properties", "0009_property_type_dynamic"),
    ]

    operations = [
        migrations.CreateModel(
            name="OwnerAvailabilitySlot",
            fields=timestamped_fields()
            + [
                ("date", models.DateField(verbose_name="Date")),
                ("time", models.TimeField(verbose_name="Time")),
                (
                    "is_enabled",
                    models.BooleanField(default=True, verbose_name="Is Enabled"),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="availability_slots",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Owner",
                    ),
                ),
            ],
            options={
                "verbose_name": "Owner Availability Slot",
                "verbose_name_plural": "Owner Availability Slots",
                "ordering": ["date", "time"],
            },
        ),
        migrations.CreateModel(
            name="PropertyFavorite",
            fields=timestamped_fields()
            + [
                (
                    "property",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="favorites",
                        to="properties.property",
                        verbose_name="Property",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="property_favorites",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Property Favorite",
                "verbose_name_plural": "Property Favorites",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SavedProperty",
            fields=timestamped_fields()
            + [
                (
                    "property",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saves",
                        to="properties.property",
                        verbose_name="Property",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saved_properties",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Saved Property",
                "verbose_name_plural": "Saved Properties",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PropertyRating",
            fields=timestamped_fields()
            + [
                (
                    "rating",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                        verbose_name="Rating",
                    ),
                ),
                (
                    "property",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ratings",
                        to="properties.property",
                        verbose_name="Property",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="property_ratings",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Property Rating",
                "verbose_name_plural": "Property Ratings",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="owneravailabilityslot",
            constraint=models.UniqueConstraint(
                fields=("owner", "date", "time"), name="unique_owner_availability_slot"
            ),
        ),
        migrations.AddConstraint(
            model_name="propertyfavorite",
            constraint=models.UniqueConstraint(
                fields=("user", "property"), name="unique_property_favorite"
            ),
        ),
        migrations.AddConstraint(
            model_name="savedproperty",
            constraint=models.UniqueConstraint(
                fields=("user", "property"), name="unique_saved_property"
            ),
        ),
        migrations.AddConstraint(
            model_name="propertyrating",
            constraint=models.UniqueConstraint(
                fields=("user", "property"), name="unique_property_rating"
            ),
        ),
        migrations.AddConstraint(
            model_name="propertyrating",
            constraint=models.CheckConstraint(
                check=models.Q(rating__gte=1, rating__lte=5),
                name="property_rating_between_1_and_5",
            ),
        ),
    ]
