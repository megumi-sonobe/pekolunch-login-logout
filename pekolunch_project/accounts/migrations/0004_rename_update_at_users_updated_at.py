# Generated by Django 5.0.3 on 2024-05-07 01:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_users_adult_count_users_children_count_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='users',
            old_name='update_at',
            new_name='updated_at',
        ),
    ]