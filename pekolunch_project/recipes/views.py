from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.views.generic import CreateView,UpdateView
from django.urls import reverse_lazy
from .models import Recipe
from .forms import RecipeForm
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Recipe,UserEvaluation
from django.contrib.auth.mixins import LoginRequiredMixin


class RecipeCreateView(CreateView):
    model = Recipe
    form_class = RecipeForm 
    template_name = 'recipes/my_recipe.html'
    success_url = reverse_lazy('my_recipe_create')
    
    @csrf_exempt
    def post(self,request,*args,**kwargs):
        form = self.get_form()
        if form.is_valid():
            self.object = form.save()
            return JsonResponse({'success':True})
        else:
            return JsonResponse({'success':False,'errors':form.errors})
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['csv_file_path'] = 'meal_planner/data/food_categories.csv'
        return kwargs
    
class RecipeUpdateView(UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_update.html'
    success_url = reverse_lazy('my_recipe_create')
    
    @csrf_exempt
    def post(self,request,*args,**kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            self.object = form.save()
            return JsonResponse({'success':True})
        else:
            return JsonResponse({'success':False,'errors':form.errors})

    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['csv_file_path'] = 'meal_planner/data/food_categories.csv'
        return kwargs
    
class SaveRatingView(LoginRequiredMixin,View):
    @csrf_exempt
    def post(self,request,*args,**kwargs):
        rating_value = request.POST.get('rating')
        recipe_id = request.POST.get('recipe-id')
        if rating_value and recipe_id:
            try:
                recipe = Recipe.objects.get(pk=recipe_id)
                user = request.user
                evaluation = int(rating_value)
                user_evaluation = UserEvaluation.objects.create(user=user,recipe=recipe,evaluation=evaluation)
                user_evaluation.save()
                return JsonResponse({'success':True})
            
            except Recipe.DoesNotExist:
                return JsonResponse({'success':False,'error':'Recipe not found'})
            
        else:   
            return JsonResponse({'success':False,'error':'Invalid request'})