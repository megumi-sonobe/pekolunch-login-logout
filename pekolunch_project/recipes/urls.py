from django .urls import path
from .views import RecipeCreateView,RecipeUpdateView

app_name = 'recipes'

urlpatterns = [
    path('my_recipe/create/',RecipeCreateView.as_view(),name='my_recipe_create'),
    path('my_recipe/<int:pk>/update/',RecipeUpdateView.as_view(),name='my_recipe_update'),
]