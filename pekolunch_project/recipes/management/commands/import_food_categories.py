import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import FoodCategory  # 適切なアプリ名とモデル名を使用

class Command(BaseCommand):
    help = 'Import food categories from a CSV file into the database'

    def handle(self, *args, **kwargs):
        csv_file_path = os.path.join(settings.BASE_DIR, 'data/food_categories.csv')
        self.import_food_categories(csv_file_path)
        self.stdout.write(self.style.SUCCESS('Food categories have been imported successfully.'))

    def import_food_categories(self, csv_file_path):
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:  # 空の行を除外
                    food_category_name = row[0]
                    is_next_day_excluded = row[1].lower() == 'true'
                    is_next_3_day_excluded = row[2].lower() == 'true'
                    FoodCategory.objects.get_or_create(
                        food_category_name=food_category_name,
                        defaults={
                            'is_next_day_excluded': is_next_day_excluded,
                            'is_next_3_day_excluded': is_next_3_day_excluded
                        }
                    )
