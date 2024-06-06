from django.core.management.base import BaseCommand
from recipes.models import Recipe, Ingredient, Process, FoodCategory
from accounts.models import Users
import csv
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Load recipes from CSV file'

    def handle(self, *args, **kwargs):
        csv_file_path = os.path.join(settings.BASE_DIR, 'data/recipes.csv')  

        added_recipes = []

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                if row['recipe_name']:
                    try:
                        user = Users.objects.get(pk=row['user_id'])
                    except Users.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"User with id {row['user_id']} does not exist. Skipping row: {row}"))
                        continue

                    # 新しいレシピのみ保存
                    if not Recipe.objects.filter(user=user, recipe_name=row['recipe_name']).exists():
                        # image_urlが空の場合、Noneに設定
                        image_url = row['image_url'] if row['image_url'] else None

                        # レシピを作成
                        recipe = Recipe.objects.create(
                            user=user,
                            recipe_name=row['recipe_name'],
                            menu_category=row['menu_category'],
                            cooking_time_min=row['cooking_time_min'],
                            cooking_method=row['cooking_method'],
                            image_url=image_url,
                            serving=row['serving'],
                            share=row['share'],
                            is_avoid_main_dish=row['is_avoid_main_dish']
                        )

                        added_recipes.append(row['recipe_name'])

                        # フードカテゴリーを処理
                        food_category_ids = [row['food_category_id_1'], row['food_category_id_2'], row['food_category_id_3'], row['food_category_id_4'], row['food_category_id_5']]
                        food_categories = []
                        for food_category_id in food_category_ids:
                            if food_category_id:
                                try:
                                    food_category = FoodCategory.objects.get(pk=int(food_category_id))
                                    food_categories.append(food_category)
                                except FoodCategory.DoesNotExist:
                                    self.stdout.write(self.style.WARNING(f"FoodCategory with id {food_category_id} does not exist. Skipping id: {food_category_id}"))

                        if food_categories:
                            recipe.food_categories.set(food_categories)

                        # 材料とプロセスを追加
                        if row.get('ingredient_name') and row.get('quantity_unit'):
                            Ingredient.objects.create(
                                recipe=recipe,
                                ingredient_name=row['ingredient_name'],
                                quantity_unit=row['quantity_unit']
                            )

                        if row.get('process_number') and row.get('process_description'):
                            Process.objects.create(
                                recipe=recipe,
                                process_number=row['process_number'],
                                description=row['process_description']
                            )

        if added_recipes:
            self.stdout.write(self.style.SUCCESS(f'Added {len(added_recipes)} new recipes:'))
            for recipe_name in added_recipes:
                self.stdout.write(self.style.SUCCESS(recipe_name))
