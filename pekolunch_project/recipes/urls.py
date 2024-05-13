from django .urls import path
from .views import RecipeCreateView,RecipeUpdateView,SaveRatingView,LoadFoodCategoriesView

app_name = 'recipes'

urlpatterns = [
    path('my_recipe/create/',RecipeCreateView.as_view(),name='my_recipe_create'),
    path('my_recipe/<int:pk>/update/',RecipeUpdateView.as_view(),name='my_recipe_update'),
    path('save_rating/',SaveRatingView.as_view(),name='save_rating'),
    path('load_food_categories/',LoadFoodCategoriesView.as_view(),name='load_food_categories'),
]