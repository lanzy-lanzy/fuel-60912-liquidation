# Generated on 2026-08-25 for multi-image RER support
import django.db.models.deletion
import fuel.models
from django.db import migrations, models


def migrate_legacy_images(apps, schema_editor):
    RER = apps.get_model('fuel', 'ReimbursementExpenseReceipt')
    RERImage = apps.get_model('fuel', 'ReimbursementExpenseReceiptImage')
    for rer in RER.objects.exclude(attached_image='').exclude(attached_image__isnull=True):
        if rer.attached_image and not RERImage.objects.filter(rer_id=rer.pk).exists():
            # Copy legacy single image into new gallery table (keep file reference)
            RERImage.objects.create(rer_id=rer.pk, image=rer.attached_image, order=0)


def reverse_migrate(apps, schema_editor):
    RERImage = apps.get_model('fuel', 'ReimbursementExpenseReceiptImage')
    RERImage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('fuel', '0015_add_vat_inclusive'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReimbursementExpenseReceiptImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=fuel.models.rer_gallery_image_path)),
                ('caption', models.CharField(blank=True, max_length=255)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('rer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='fuel.reimbursementexpensereceipt')),
            ],
            options={
                'verbose_name': 'RER Image',
                'verbose_name_plural': 'RER Images',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.RunPython(migrate_legacy_images, reverse_migrate),
    ]
