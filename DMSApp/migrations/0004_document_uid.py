# Generated by Django 4.2.16 on 2024-11-23 23:38

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('DMSApp', '0003_alter_entity_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='uid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
