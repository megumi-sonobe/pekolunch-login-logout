import csv
from datetime import timedelta
from django.utils import timezone
from recipes.models import Recipe,FoodCategory
from meal_planner.models import MealPlan
from random import choice


#CSVで食材データを読み込んでルールに当てはめる
RULES = {}

def load_food_categories_from_csv(file_path):
    rules = {}
    with open(file_path, 'r',encoding='utf-8')as file:
        reader = csv.DictReader(file)
        for row in reader:
            food_category_name = row['食材名']
            rules[food_category_name] = {
                'exclude_next_day':row.get('翌日除外',False),
                'exclude_next_3_days':row.get('翌3日除外',False),
                }
        return rules
    
def apply_rules(recipes,today,user):
    rules = load_food_categories_from_csv('path_to_your_file.csv')
    
    exclude_food_categories = []
    
    for category_name,rule in rules.items():
        if rule['exclude_next_day']:
            exclude_food_categories.append(category_name)
        elif rule['exclude_next_3_days']:
            exclude_food_categories.append(category_name)
            
    return recipes.exclude(food_categories__food_category_name__in=exclude_food_categories)


def get_eligible_recipes(cls, user):
    cooking_time_setting = user.cooking_time_min
    
    if cooking_time_setting == 30:
        return Recipe.objects.all()
    elif cooking_time_setting == 20:
        return Recipe.objects.filter(cooking_time_min__lte=20)
    
    return Recipe.objects.filter(cooking_time_min__lte=cooking_time_setting)
