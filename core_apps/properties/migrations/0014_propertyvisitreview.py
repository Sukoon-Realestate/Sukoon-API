import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("properties", "0013_remove_property_country")]

    operations = [
        migrations.CreateModel(
            name="PropertyVisitReview",
            fields=[
                (
                    "pkid",
                    models.BigAutoField(
                        editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "overall_rating",
                    models.PositiveSmallIntegerField(
                        verbose_name="Overall Rating",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                (
                    "cleanliness_rating",
                    models.PositiveSmallIntegerField(
                        verbose_name="Cleanliness Rating",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                (
                    "listing_accuracy_rating",
                    models.PositiveSmallIntegerField(
                        verbose_name="Listing Accuracy Rating",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                (
                    "owner_interaction_rating",
                    models.PositiveSmallIntegerField(
                        verbose_name="Owner Interaction Rating",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                (
                    "comment",
                    models.TextField(blank=True, default="", verbose_name="Comment"),
                ),
                (
                    "visit",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="review",
                        to="properties.propertyvisit",
                        verbose_name="Visit",
                    ),
                ),
            ],
            options={
                "verbose_name": "Property Visit Review",
                "verbose_name_plural": "Property Visit Reviews",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="propertyvisitreview",
            constraint=models.CheckConstraint(
                check=models.Q(("overall_rating__range", (1, 5))),
                name="visit_review_overall_between_1_and_5",
            ),
        ),
        migrations.AddConstraint(
            model_name="propertyvisitreview",
            constraint=models.CheckConstraint(
                check=models.Q(("cleanliness_rating__range", (1, 5))),
                name="visit_review_cleanliness_between_1_and_5",
            ),
        ),
        migrations.AddConstraint(
            model_name="propertyvisitreview",
            constraint=models.CheckConstraint(
                check=models.Q(("listing_accuracy_rating__range", (1, 5))),
                name="visit_review_accuracy_between_1_and_5",
            ),
        ),
        migrations.AddConstraint(
            model_name="propertyvisitreview",
            constraint=models.CheckConstraint(
                check=models.Q(("owner_interaction_rating__range", (1, 5))),
                name="visit_review_owner_between_1_and_5",
            ),
        ),
    ]
