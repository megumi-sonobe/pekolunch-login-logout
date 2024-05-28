from django .urls import path
from .views import RecipeCreateView,RecipeUpdateView,RecipeDeleteView,SaveRatingView,RecipeDetailView,RecipeListView
from . import views

app_name = 'recipes'

urlpatterns = [
    path('my_recipe/create/',RecipeCreateView.as_view(),name='my_recipe_create'),
    path('my_recipe/<int:pk>/update/',RecipeUpdateView.as_view(),name='my_recipe_update'),
    path('recipe/<int:pk>/delete/', RecipeDeleteView.as_view(), name='recipe_delete'),
    path('save_rating/',SaveRatingView.as_view(),name='save_rating'),
    path('recipe/<int:pk>/',RecipeDetailView.as_view(),name='recipe_detail'),
    path('recipes/',RecipeListView.as_view(),name='recipe_list'),
    path('search/',views.search,name='search'),
]