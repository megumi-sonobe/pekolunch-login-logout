# Generated by Django 5.0.3 on 2024-05-10 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_foodcategory_is_next_3_day_excluded_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foodcategory',
            name='food_category_name',
            field=models.CharField(max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name='process',
            name='process_number',
            field=models.IntegerField(default=1),
        ),
    ]
