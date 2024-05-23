from django.urls import path
from .views import MealPlannerHomeView, CreateMealPlansView, EditMealPlanView, MealPlanDatesView

app_name = 'meal_planner'

urlpatterns = [
    path('home/',MealPlannerHomeView.as_view(), name='home'),
    path('create_meal_plans/', CreateMealPlansView.as_view(), name='create_meal_plans'),
    path('edit_meal_plan/<str:start_date>/<str:end_date>/', EditMealPlanView.as_view(), name='edit_meal_plan'),
    path('meal-plan-dates/', MealPlanDatesView.as_view(), name='meal_plan_dates'),
]
