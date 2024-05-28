from django.urls import path
from .views import CreateMealPlansView, EditMealPlanView, MealPlanDatesView, WeeklyMealPlanView, select_recipe, MealPlannerRecipeListView

app_name = 'meal_planner'

urlpatterns = [
    path('create_meal_plans/', CreateMealPlansView.as_view(), name='create_meal_plans'),
    path('edit_meal_plan/<str:start_date>/<str:end_date>/', EditMealPlanView.as_view(), name='edit_meal_plan'),
    path('meal-plan-dates/', MealPlanDatesView.as_view(), name='meal_plan_dates'),
    path('weekly_meal_plan/', WeeklyMealPlanView.as_view(), name='weekly_meal_plan'),
    path('select_recipe/', select_recipe, name='select_recipe'),
    path('recipe_list/', MealPlannerRecipeListView.as_view(), name='recipe_list'),
]
