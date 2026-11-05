from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('support', '0013_evidence_requirement_versions')]
    operations = [migrations.AlterModelOptions(
        name='ticketmessage', options={
            'ordering': ['created_at', 'pk'],
            'verbose_name': 'Ticket Message', 'verbose_name_plural': 'Ticket Messages',
        },
    )]
