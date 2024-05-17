from django.urls import path
from .views import create_meal_plans, edit_meal_plan

app_name = 'meal_planner'

urlpatterns = [
    path('create_meal_plans/', create_meal_plans, name='create_meal_plans'),
    path('edit_meal_plan/<str:start_date>/<str:end_date>/', edit_meal_plan, name='edit_meal_plan'),
]
