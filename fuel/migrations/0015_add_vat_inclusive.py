# Generated on 2026-08-25
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('fuel', '0014_add_pcv_rer'),
    ]

    operations = [
        migrations.AddField(
            model_name='liquidationreportentry',
            name='vat_inclusive',
            field=models.BooleanField(default=True, help_text='VAT inclusive - checked: amount includes 12% VAT (WHT = amount/1.12*rate). Unchecked: Non-VAT (WHT = amount*rate)'),
        ),
    ]
