from django.urls import path
from .views import create_meal_plans


app_name = 'meal_planner'


urlpatterns = [
    path('create_meal_plans/',create_meal_plans,name='create_meal_plans'),
]