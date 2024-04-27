# Generated by Django 5.0.3 on 2024-04-26 07:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FoodCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('food_category_name', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe_name', models.CharField(max_length=32)),
                ('menu_category', models.IntegerField(choices=[(1, '主食'), (2, '主菜'), (3, '副菜'), (4, '汁物')])),
                ('cooking_time_min', models.IntegerField(choices=[(10, '10分以内'), (20, '20分以内'), (30, '30分以内')])),
                ('cooking_method', models.IntegerField(choices=[(1, '焼く'), (2, '炒める'), (3, '煮る'), (4, '蒸す'), (5, '揚げる'), (6, '和える'), (7, 'なし')])),
                ('image_url', models.ImageField(blank=True, null=True, upload_to='recipes/images/')),
                ('share', models.IntegerField(default=1)),
                ('is_avoid_main_dish', models.IntegerField(default=0)),
                ('average_evaluation', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('process_number', models.IntegerField(unique=True)),
                ('description', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.recipe')),
            ],
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ingredient_name', models.CharField(max_length=64)),
                ('quantity_unit', models.CharField(max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.recipe')),
            ],
        ),
        migrations.CreateModel(
            name='RecipeFoodCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('food_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.foodcategory')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.recipe')),
            ],
            options={
                'unique_together': {('food_category', 'recipe')},
            },
        ),
        migrations.AddField(
            model_name='recipe',
            name='food_categories',
            field=models.ManyToManyField(through='recipes.RecipeFoodCategory', to='recipes.foodcategory'),
        ),
        migrations.CreateModel(
            name='UserEvaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evaluation', models.IntegerField(choices=[(0, '1 star'), (1, '2 star'), (2, '3 star')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.recipe')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
