# Generated by Django 5.0.3 on 2024-06-11 05:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0013_alter_recipe_recipe_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_method',
            field=models.IntegerField(choices=[(None, '選択してください'), (1, '焼く'), (2, '炒める'), (3, '煮る'), (4, '蒸す'), (5, '揚げる'), (6, '和える'), (7, 'なし')]),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time_min',
            field=models.IntegerField(choices=[(None, '選択してください'), (10, '10分以内'), (20, '20分以内'), (30, '30分以内')]),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='menu_category',
            field=models.IntegerField(choices=[(None, '選択してください'), (1, '主食'), (2, '主菜'), (3, '副菜'), (4, '汁物')]),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='recipe_name',
            field=models.CharField(max_length=32),
        ),
    ]
