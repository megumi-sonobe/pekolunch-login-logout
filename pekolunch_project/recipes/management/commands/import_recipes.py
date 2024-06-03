from django.core.management.base import BaseCommand
from recipes.models import Recipe, Ingredient, Process, FoodCategory
from accounts.models import Users
import csv
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Load recipes from CSV file'

    def handle(self, *args, **kwargs):
        csv_file_path = os.path.join(settings.BASE_DIR, 'data/recipes.csv')  # 適切なパスに変更してください

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                if row['recipe_name']:
                    try:
                        user = Users.objects.get(pk=row['user_id'])
                    except Users.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"User with id {row['user_id']} does not exist. Skipping row: {row}"))
                        continue

                    # image_urlが空の場合、Noneに設定
                    image_url = row['image_url'] if row['image_url'] else None

                    recipe, created = Recipe.objects.update_or_create(
                        user=user,
                        recipe_name=row['recipe_name'],
                        menu_category=row['menu_category'],
                        cooking_time_min=row['cooking_time_min'],
                        cooking_method=row['cooking_method'],
                        defaults={
                            'image_url': image_url,
                            'serving': row['serving'],
                            'share': row['share'],
                            'is_avoid_main_dish': row['is_avoid_main_dish'],
                        }
                    )

                    if row.get('food_category_id'):
                        try:
                            food_category = FoodCategory.objects.get(pk=row['food_category_id'])
                            recipe.food_categories.set([food_category])
                        except FoodCategory.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f"FoodCategory with id {row['food_category_id']} does not exist. Skipping row: {row}"))

                    if row.get('ingredient_name') and row.get('quantity_unit'):
                        Ingredient.objects.update_or_create(
                            recipe=recipe,
                            ingredient_name=row['ingredient_name'],
                            defaults={'quantity_unit': row['quantity_unit']}
                        )

                    if row.get('process_number') and row.get('process_description'):
                        Process.objects.update_or_create(
                            recipe=recipe,
                            process_number=row['process_number'],
                            defaults={'description': row['process_description']}
                        )

        self.stdout.write(self.style.SUCCESS('Successfully loaded recipes from CSV'))
