# Generated by Django 5.1.3 on 2024-11-20 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DMSApp', '0002_alter_document_process_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entity',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]