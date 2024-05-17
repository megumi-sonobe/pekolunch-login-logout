from django.urls import path
from . import views

app_name = 'meal_planner'

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_meal_plans, name='create_meal_plans'),
    path('edit/<str:start_date>/<str:end_date>/', views.edit_meal_plan, name='edit_meal_plan'),
]
