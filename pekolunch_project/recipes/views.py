from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.views.generic import CreateView,UpdateView
from django.urls import reverse_lazy
from .models import Recipe
from .forms import RecipeForm


class RecipeCreateView(CreateView):
    model = Recipe
    form_class = RecipeForm 
    template_name = 'recipes/my_recipe.html'
    success_url = reverse_lazy('my_recipe_create')
    
    
class RecipeUpdateView(UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_update.html'
    success_url = reverse_lazy('my_recipe_create')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        
        return obj
