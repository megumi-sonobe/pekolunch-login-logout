import csv
from django.utils import timezone
from recipes.models import Recipe,FoodCategory
from meal_planner.models import MealPlan


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
    
csv_file_path = 'meal_planner/data/food_categories.csv'

RULES = load_food_categories_from_csv(csv_file_path)

    
def apply_rules(recipes,today,user):
    # グローバル変数のRULESを使用する
    exclude_food_categories = [category for category, rule in RULES.items() if rule['exclude_next_day'] or rule['exclude_next_3_days']]    
    return recipes.exclude(food_categories__food_category_name__in=exclude_food_categories)


def get_eligible_recipes(user,previous_meal_plans):
    cooking_time_setting = user.cooking_time_min
#ユーザーが指定した調理時間に基づく
    if cooking_time_setting == 30:
        base_queryset =  Recipe.objects.all()
    elif cooking_time_setting == 20:
        base_queryset = Recipe.objects.filter(cooking_time_min__lte=20)
    
    else:
        base_queryset = Recipe.objects.filter(cooking_time_min__lte=cooking_time_setting)
        
# #評価が高い順に選ばれる
#     base_queryset = base_queryset.order_by('-average_evaluation')


#主食、主菜、副菜から１品ずつ選択
    staple_recipe = base_queryset.filter(menu_category=1).order_by('-average_evaluation').first()
    main_recipe = base_queryset.filter(menu_category=2).order_by('-average_evaluation').first()
    side_recipe = base_queryset.filter(menu_category=3).order_by('-average_evaluation').first()
   
#20日間は同じレシピを使用しない
    if previous_meal_plans:
        last_used_staple = [plan.staple_recipe.id for plan in previous_meal_plans[-20:]]
        last_used_main = [plan.main_recipe.id for plan in previous_meal_plans[-20:]]
        last_used_side = [plan.side_recipe.id for plan in previous_meal_plans[-20:]]
        
        last_used_recipes = last_used_staple + last_used_main + last_used_side
        base_queryset = base_queryset.exclude(id__in=last_used_recipes)

#同じ調理法のレシピを使用しない   
    today = timezone.now().date()
    today_used_methods = []
    
    for plan in previous_meal_plans:
        if plan.meal_date == today:
            today_used_methods.append(plan.staple_recipe.cooking.method)
            today_used_methods.append(plan.main_recipe.cooking.method)
            today_used_methods.append(plan.side_recipe.cooking.method)
            
    base_queryset = base_queryset.exclude(cooking_method__in=today_used_methods)
    
    return [staple_recipe, main_recipe, side_recipe]
       
