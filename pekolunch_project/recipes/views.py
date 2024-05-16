from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.shortcuts import render,redirect
from django.views.generic import CreateView,UpdateView
from django.urls import reverse_lazy
from .forms import RecipeForm,ProcessForm,IngredientForm
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Recipe,UserEvaluation,Process,Ingredient
from django.contrib.auth.mixins import LoginRequiredMixin
import csv
import os
from django.conf import settings


class RecipeCreateView(CreateView):
    model = Recipe
    form_class = RecipeForm 
    template_name = 'recipes/my_recipe.html'
    success_url = reverse_lazy('accounts:home')
    
    
    def form_valid(self,form):
        try:
            # Save the recipe instance first to get the ID
            self.object = form.save(commit=False)  # commit=Falseで保存を遅延
            self.object.save()  # ここでオブジェクトをデータベースに保存してIDを取得

            # Save related instances after the recipe is saved
            self.save_related_instances(form, self.object)

            return super().form_valid(form)
        except Exception as e:
            print("Exception occurred during form submission:", e)
            return self.form_invalid(form) 
        
    def form_invalid(self, form):
        # フォームのエラーをログに出力
        print(form.errors)  
        return super().form_invalid(form)
    

    def save_related_instances(self, form, recipe):

        # 材料の保存
        ingredient_names = self.request.POST.getlist('ingredient_name', [])
        quantity_units = self.request.POST.getlist('quantity_unit', [])  # 量の単位を取得

        # ingredient_name = form.cleaned_data.get('ingredient_name')
        # quantity_unit = form.cleaned_data.get('quantity_unit')  # 量の単位を取得
        
        for name, unit in zip(ingredient_names, quantity_units):
            if name:
                Ingredient.objects.create(recipe=recipe, ingredient_name=name, quantity_unit=unit)


        # if ingredient_name:
        #     Ingredient.objects.create(recipe=recipe, ingredient_name=ingredient_name, quantity_unit=quantity_unit)

        # ProcessFormを使用してプロセスの詳細を保存
        descriptions = self.request.POST.getlist('description', [])
        for description in descriptions:
            if description:
                last_process = Process.objects.filter(recipe=recipe).order_by('-process_number').first()
                process_number = 1 if not last_process else last_process.process_number + 1
                Process.objects.create(recipe=recipe, description=description, process_number=process_number)

        # process_form = ProcessForm(self.request.POST)
        # if process_form.is_valid():
        #     process = process_form.save(commit=False)
        #     process.recipe = recipe
        #     last_process = Process.objects.filter(recipe=recipe).order_by('-process_number').first()
        #     process.process_number = 1 if not last_process else last_process.process_number + 1
        #     process.save()
    
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['csv_file_path'] = 'meal_planner/data/food_categories.csv'
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'process_form' not in context:
            context['process_form'] = ProcessForm(None)
        return context
    
class RecipeUpdateView(UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_update.html'
    success_url = reverse_lazy('my_recipe_create')
    
    def form_valid(self,form):
        try:
            # Save the recipe instance first to get the ID
            recipe = form.save(commit=False)
            recipe.save()  # Save to obtain the primary key (ID)
            
            # Save related instances after the recipe is saved
            self.save_related_instances(form, recipe)
            
            return super().form_valid(form)
        except Exception as e:
            print("Exception occurred during form submission:", e)
            raise
        
    def form_invalid(self, form):
        process_form = ProcessForm(self.request.POST)
        print(form.errors)  # フォームのエラーをログに出力
        return self.render

    def save_related_instances(self, form, recipe):
        # Process serving
        # serving = form.cleaned_data.get('serving', 1)
        
    
        # 材料の保存
        ingredient_name = form.cleaned_data.get('ingredient_name')
        quantity_unit = form.cleaned_data.get('quantity_unit')  # 量の単位を取得

        if ingredient_name:
            Ingredient.objects.create(recipe=recipe, ingredient_name=ingredient_name, quantity_unit=quantity_unit)

        # ProcessFormを使用してプロセスの詳細を保存
        process_form = ProcessForm(self.request.POST)
        if process_form.is_valid():
            process = process_form.save(commit=False)
            process.recipe = recipe
            last_process = Process.objects.filter(recipe=recipe).order_by('-process_number').first()
            process.process_number = 1 if not last_process else last_process.process_number + 1
            process.save()
            
    
            

    
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