# Generated by Django 5.0.3 on 2024-05-13 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_alter_foodcategory_food_category_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='process',
            name='process_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
