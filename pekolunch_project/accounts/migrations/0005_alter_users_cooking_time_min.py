# Generated by Django 5.0.3 on 2024-06-03 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_rename_update_at_users_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='users',
            name='cooking_time_min',
            field=models.IntegerField(choices=[(10, '10分以内'), (20, '20分以内'), (30, '30分以内')], default=30),
        ),
    ]
