from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from .forms import RecipeForm, ProcessForm, IngredientForm
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Recipe, UserEvaluation, Process, Ingredient
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
import csv
import os
from django.conf import settings
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView


class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = Recipe
    form_class = RecipeForm 
    template_name = 'recipes/my_recipe.html'
    # success_url = reverse_lazy('accounts:home')
    
    def form_valid(self, form):
        try:
            self.object = form.save(commit=False)  # commit=Falseで保存を遅延
            self.object.save()  # ここでオブジェクトをデータベースに保存してIDを取得
            self.save_related_instances()
            self.save_user_evaluation()
            messages.success(self.request, f"レシピに「{self.object.recipe_name}」が登録されました。")
            return redirect('recipes:my_recipe_create')  # 遷移先を再びマイレシピ登録ページに設定
        except Exception as e:
            print(f"Exception occurred during form submission: {e}")
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        # フォームのエラーをログに出力
        print(form.errors)
        return super().form_invalid(form)
    
    def save_related_instances(self):
        ingredient_names = self.request.POST.getlist('ingredient_name', [])
        quantity_units = self.request.POST.getlist('quantity_unit', [])  # 量の単位を取得

        for name, unit in zip(ingredient_names, quantity_units):
            if name:
                Ingredient.objects.create(recipe=self.object, ingredient_name=name, quantity_unit=unit)

        descriptions = self.request.POST.getlist('description', [])
        for description in descriptions:
            if description:
                last_process = Process.objects.filter(recipe=self.object).order_by('-process_number').first()
                process_number = 1 if not last_process else last_process.process_number + 1
                Process.objects.create(recipe=self.object, description=description, process_number=process_number)
                
    def save_user_evaluation(self):
        rating_value = self.request.POST.get('rating-value')
        print(f'Rating value: {rating_value}')  # デバッグ用
        if rating_value is not None and rating_value.isdigit():
            evaluation = int(rating_value)
            UserEvaluation.objects.create(user=self.request.user, recipe=self.object, evaluation=evaluation)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['csv_file_path'] = 'meal_planner/data/food_categories.csv'
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'process_form' not in context:
            context['process_form'] = ProcessForm(None)
        return context

class RecipeUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_update.html'
    success_url = reverse_lazy('accounts:home')
    
    def form_valid(self, form):
        try:
            self.object = form.save(commit=False)  # commit=Falseで保存を遅延
            self.object.save()  # ここでオブジェクトをデータベースに保存してIDを取得
            self.save_related_instances()
            self.save_user_evaluation()
            return super().form_valid(form)
        except Exception as e:
            print(f"Exception occurred during form submission: {e}")
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        process_form = ProcessForm(self.request.POST)
        print(form.errors)  # フォームのエラーをログに出力
        return self.render_to_response(self.get_context_data(form=form))
    
    def save_related_instances(self):
        ingredient_names = self.request.POST.getlist('ingredient_name', [])
        quantity_units = self.request.POST.getlist('quantity_unit', [])  # 量の単位を取得

        for name, unit in zip(ingredient_names, quantity_units):
            if name:
                Ingredient.objects.create(recipe=self.object, ingredient_name=name, quantity_unit=unit)

        descriptions = self.request.POST.getlist('description', [])
        for description in descriptions:
            if description:
                last_process = Process.objects.filter(recipe=self.object).order_by('-process_number').first()
                process_number = 1 if not last_process else last_process.process_number + 1
                Process.objects.create(recipe=self.object, description=description, process_number=process_number)
                
    def save_user_evaluation(self):
        rating_value = self.request.POST.get('rating-value')
        print(f'Rating value: {rating_value}')  # デバッグ用
        if rating_value is not None and rating_value.isdigit():
            evaluation = int(rating_value)
            UserEvaluation.objects.update_or_create(
                user=self.request.user, 
                recipe=self.object,
                defaults={'evaluation': evaluation}
            )

class SaveRatingView(LoginRequiredMixin, View):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        rating_value = request.POST.get('rating')
        recipe_id = request.POST.get('recipe-id')
        if rating_value and rating_value.isdigit() and recipe_id:
            try:
                recipe = Recipe.objects.get(pk=recipe_id)
                user = request.user
                evaluation = int(rating_value)
                UserEvaluation.objects.update_or_create(
                    user=user, 
                    recipe=recipe,
                    defaults={'evaluation': evaluation}
                )
                return JsonResponse({'success': True})
            except Recipe.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Recipe not found'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid request'})

class LoadFoodCategoriesView(View):
    def get(self, request):
        csv_file_path = os.path.join(settings.BASE_DIR, 'meal_planner/data/food_categories.csv')  # CSVファイルのパスを指定

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                food_categories = [row[0] for row in reader]  # CSVファイルから食材カテゴリを読み込む
                
            if food_categories:
                return JsonResponse({'food_categories': food_categories})
            else:
                return JsonResponse({'error': 'CSVファイルが見つかりませんでした'}, status=404)
        
        except FileNotFoundError:
            return JsonResponse({'error': 'CSVファイルが見つかりませんでした'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class RecipeListView(ListView):
    model = Recipe
    template_name = 'recipe/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 10 #1ページあたりのアイテム数
    
    def get_queryset(self):
        return Recipe.objects.order_by('-average_evaluation')

class RecipeDetailView(DetailView):
    model = Recipe
    template_name = 'recipes/recipe_detail.html'
    context_object_name = 'recipe'
    
    