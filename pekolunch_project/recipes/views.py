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
from django.contrib.auth import get_user_model
import csv
import os
import json
from django.conf import settings
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from accounts.models import Users

User = get_user_model

class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = Recipe
    form_class = RecipeForm 
    template_name = 'recipes/my_recipe.html'
    # success_url = reverse_lazy('accounts:home')
    
    def form_valid(self, form):
        try:
            self.object = form.save(commit=False)# commit=Falseで保存を遅延
            self.object.user = self.request.user
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
    template_name = 'recipes/my_recipe_update.html'
    
    def get_success_url(self):
        return reverse_lazy('recipes:recipe_detail', kwargs={'pk': self.object.pk})
    
    
    
    def get_initial(self):
        initial = super().get_initial()
        initial['food_categories'] = self.object.food_categories.all()
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['csv_file_path'] = 'meal_planner/data/food_categories.csv'
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        user = self.request.user
        user_evaluation = UserEvaluation.objects.filter(user=user, recipe=recipe).first()
        context['user_evaluation'] = user_evaluation
        # context['adult_count'] = user.adult_count
        # context['children_count'] = user.children_count
        # context['is_owner'] = recipe.user == user
        return context
    
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

        # 既存の材料を削除
        self.object.ingredient_set.all().delete()
        for name, unit in zip(ingredient_names, quantity_units):
            if name:
                Ingredient.objects.create(recipe=self.object, ingredient_name=name, quantity_unit=unit)

        descriptions = self.request.POST.getlist('description', [])
        
        # 既存の作り方を削除
        self.object.process_set.all().delete()
        for process_number, description in enumerate(descriptions, start=1):
            if description:
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
            self.object.update_average_rating()  # 平均評価を更新

class SaveRatingView(LoginRequiredMixin, View):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            rating_value = data.get('rating')
            recipe_id = data.get('recipe-id')
            print(f"Received rating: {rating_value}, recipe_id: {recipe_id}")  # デバッグ用

            if rating_value and recipe_id and str(rating_value).isdigit():
                try:
                    recipe = Recipe.objects.get(pk=recipe_id)
                    user = request.user
                    evaluation = int(rating_value)
                    UserEvaluation.objects.update_or_create(
                        user=user, 
                        recipe=recipe,
                        defaults={'evaluation': evaluation}
                    )
                    print("Rating saved successfully")  # デバッグ用
                    return JsonResponse({'success': True})
                except Recipe.DoesNotExist:
                    print("Recipe not found")  # デバッグ用
                    return JsonResponse({'success': False, 'error': 'Recipe not found'})
            else:
                print("Invalid request parameters")  # デバッグ用
                return JsonResponse({'success': False, 'error': 'Invalid request'})
        except Exception as e:
            print(f"Exception: {e}")  # デバッグ用
            return JsonResponse({'success': False, 'error': str(e)})

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


class RecipeListView(LoginRequiredMixin,ListView):
    model = Recipe
    template_name = 'recipe/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 10 #1ページあたりのアイテム数
    
    def get_queryset(self):
        return Recipe.objects.order_by('-average_evaluation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context.get('page_obj')
        if page_obj:
            print(f"Current page: {page_obj.number}")
            print(f"Total pages: {page_obj.paginator.num_pages}")
        return context

def search(request):
    query = request.GET.get('q')
    filters = request.GET.getlist('filter')
    user = request.user
    
    recipes = Recipe.objects.all()
    
    if query:
        recipes = Recipe.objects.filter(recipe_name__icontains=query)
        
    if 'my_recipe' in filters:
        recipes = recipes.filter(user=user)
    if 'three_star' in filters:
        recipes = recipes.filter(average_evaluation__gte=3)
    if 'main_dish' in filters:
        recipes = recipes.filter(menu_category=1)
    if 'side_dish' in filters:
        recipes = recipes.filter(menu_category=2)
    if 'sub_dish' in filters:
        recipes = recipes.filter(menu_category=3)
    if 'soup' in filters:
        recipes = recipes.filter(menu_category=4) 
    
    recipes = recipes.order_by('-average_evaluation')
    
    paginator = Paginator(recipes,10)
    page = request.GET.get('page')
    
    try:
        recipes = paginator.page(page)
    except PageNotAnInteger:
        recipes = paginator.page(1)
    except EmptyPage:
        recipes = paginator.page(paginator.num_pages)
        
        
    context = {
            'recipes':recipes,
            'page_obj':recipes,
    }
    return render(request,'recipes/recipe_list.html',context)
        
    
    

class RecipeDetailView(LoginRequiredMixin, DetailView):
    model = Recipe
    template_name = 'recipes/recipe_detail.html'
    context_object_name = 'recipe'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        user = self.request.user
        user_evaluation = UserEvaluation.objects.filter(user=self.request.user, recipe=recipe).first()
        context['user_evaluation'] = user_evaluation
        context['adult_count'] = user.adult_count
        context['children_count'] = user.children_count
        context['is_owner'] = recipe.user == user
        return context
    
    def post(self, request, *args, **kwargs):
        recipe = self.get_object()
        user_evaluation = UserEvaluation.objects.filter(user=request.user, recipe=recipe).first()
        evaluation = int(request.POST.get('rating-value'))

        if user_evaluation:
            user_evaluation.evaluation = evaluation
            user_evaluation.save()
        else:
            UserEvaluation.objects.create(user=request.user, recipe=recipe, evaluation=evaluation)

        # 平均評価を更新
        recipe.update_average_rating()

        return redirect('recipes:recipe_detail', pk=recipe.pk)
            