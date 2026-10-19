from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("features", "0058_canonical_company_review_party")]

    operations = [
        migrations.AddField(
            model_name="policydecision",
            name="presentation",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name="PolicyDecisionHead",
            fields=[
                (
                    "code",
                    models.CharField(max_length=4, primary_key=True, serialize=False),
                ),
                ("revision", models.PositiveIntegerField(default=0)),
                (
                    "current",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="publication_heads",
                        to="features.policydecision",
                    ),
                ),
            ],
        ),
    ]
