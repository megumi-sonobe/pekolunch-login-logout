from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.shortcuts import render,redirect
from django.views.generic import CreateView,UpdateView
from django.urls import reverse_lazy
from .models import Recipe
from .forms import RecipeForm,ProcessForm
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Recipe,UserEvaluation,Process,Ingredient
from django.contrib.auth.mixins import LoginRequiredMixin
import csv
import os
from django.conf import settings
from django.forms import formset_factory


class RecipeCreateView(CreateView):
    model = Recipe
    form_class = RecipeForm 
    template_name = 'recipes/my_recipe.html'
    success_url = reverse_lazy('my_recipe_create')
    
    @csrf_exempt
    def post(self,request,*args,**kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.save_related_instances(form)
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        return JsonResponse({'success': False, 'errors': form.errors, 'form': self.render_to_string('recipes/my_recipe.html', {'form': form})})
    
        
    
    def save_related_instances(self, form):
        recipe = self.object
        serving = form.cleaned_data.get('serving', 1)
        recipe.adjust_ingredient_quantity_for_serving(serving)

        process_description = form.cleaned_data.get('process_description')
        ingredient_name = form.cleaned_data.get('ingredient_name')

        # 最後のプロセス番号を取得し、それに1を加えて新しいプロセス番号を設定する
        last_process = Process.objects.filter(recipe=recipe).order_by('-process_number').first()
        process_number = 1 if not last_process else last_process.process_number + 1

        # プロセスとイングレディエントを保存
        process = Process.objects.create(recipe=recipe, process_number=process_number, description=process_description)
        Ingredient.objects.create(recipe=recipe, ingredient_name=ingredient_name)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ProcessFormSet = formset_factory(ProcessForm,extra=1)
        context['process_forms'] = ProcessFormSet()
        return context

    
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
            form.save_related_instances()
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
        

class LoadFoodCategoriesView(View):
    def get(self, request):
        BASE_DIR = settings
        csv_file_path = os.path.join(str(settings.BASE_DIR),'meal_planner/data/food_categories.csv')  # CSVファイルのパスを指定

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                food_categories = [row[0] for row in reader]  # CSVファイルから食材カテゴリを読み込む
                
            if food_categories:
                return JsonResponse({'food_categories':food_categories})
            else:
                return JsonResponse({'error': 'CSVファイルが見つかりませんでした'}, status=404)
        
        except FileNotFoundError:
            return JsonResponse({'error': 'CSVファイルが見つかりませんでした'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)