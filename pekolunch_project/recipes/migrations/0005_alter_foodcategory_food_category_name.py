# Generated by Django 5.0.3 on 2024-05-10 01:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_alter_foodcategory_food_category_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foodcategory',
            name='food_category_name',
            field=models.CharField(max_length=32),
        ),
    ]