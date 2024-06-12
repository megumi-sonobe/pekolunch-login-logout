from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.urls import reverse_lazy
from .forms import RecipeForm, ProcessForm, IngredientForm
from django.views import View
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from .models import Recipe, UserEvaluation, Process, Ingredient, FoodCategory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.contrib.messages.views import SuccessMessageMixin
from fractions import Fraction
import re
import json

User = get_user_model()

class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/my_recipe.html'

    def form_valid(self, form):
        try:
            self.object = form.save(commit=False)  # commit=Falseで保存を遅延
            self.object.user = self.request.user
            self.object.save()  # ここでオブジェクトをデータベースに保存してIDを取得
            self.save_related_instances()
            self.save_user_evaluation()
            messages.success(self.request, f"レシピに「{self.object.recipe_name}」が登録されました。")
            return redirect('recipes:my_recipe_list')  # リダイレクト先をマイレシピ一覧に変更
        except Exception as e:
            print(f"Exception occurred during form submission: {e}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        # フォームのエラーをログに出力
        print(form.errors)
     
        storage = messages.get_messages(self.request)
        if not any(message.message == "レシピの登録に失敗しました。入力内容を確認してください。" for message in storage):
            messages.error(self.request, "レシピの登録に失敗しました。入力内容を確認してください。")
        return self.render_to_response(self.get_context_data(form=form))

    def save_related_instances(self):
        ingredient_names = self.request.POST.getlist('ingredient_name', [])
        quantity_units = self.request.POST.getlist('quantity_unit', []) 

        for name, unit in zip(ingredient_names, quantity_units):
            if name:
                Ingredient.objects.create(recipe=self.object, ingredient_name=name, quantity_unit=unit)

        descriptions = self.request.POST.getlist('description', [])
        for description in descriptions:
            if description:
                last_process = Process.objects.filter(recipe=self.object).order_by('-process_number').first()
                process_number = 1 if not last_process else last_process.process_number + 1
                Process.objects.create(recipe=self.object, description=description, process_number=process_number)

        food_categories = self.request.POST.getlist('food_categories', [])
        self.object.food_categories.set(food_categories)  

    def save_user_evaluation(self):
        rating_value = self.request.POST.get('rating-value')
        if rating_value is not None and rating_value.isdigit():
            evaluation = int(rating_value)
            UserEvaluation.objects.create(user=self.request.user, recipe=self.object, evaluation=evaluation)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'process_form' not in context:
            context['process_form'] = ProcessForm(None)
        context['food_categories'] = FoodCategory.objects.all()  # フードカテゴリーをデータベースから取得
        return context

class MyRecipeListView(LoginRequiredMixin, ListView):
    model = Recipe
    template_name = 'recipes/my_recipe_list.html'
    context_object_name = 'recipes'

    def get_queryset(self):
        return Recipe.objects.filter(user=self.request.user)

class RecipeUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/my_recipe_update.html'
    
    def get_success_url(self):
        return reverse_lazy('recipes:recipe_detail', kwargs={'pk': self.object.pk})
    
    def get_initial(self):
        initial = super().get_initial()
        initial['share'] = bool(self.object.share)
        initial['is_avoid_main_dish'] = bool(self.object.is_avoid_main_dish)
        initial['serving'] = self.object.serving
        initial['food_categories'] = self.object.food_categories.all()
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        user = self.request.user
        user_evaluation = UserEvaluation.objects.filter(user=user, recipe=recipe).first()
        context['user_evaluation'] = user_evaluation
        context['food_categories'] = FoodCategory.objects.all()  # フードカテゴリーをデータベースから取得
        return context
    
    def form_valid(self, form):
        try:
            self.object = form.save(commit=False)  
            self.object.save() 
            self.save_related_instances()
            self.save_user_evaluation()
            messages.success(self.request, "レシピを更新しました。")
            return super().form_valid(form)
        except Exception as e:
            print(f"Exception occurred during form submission: {e}")
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        process_form = ProcessForm(self.request.POST)
        print(form.errors)  
        return self.render_to_response(self.get_context_data(form=form))
    
    def save_related_instances(self):
        ingredient_names = self.request.POST.getlist('ingredient_name', [])
        quantity_units = self.request.POST.getlist('quantity_unit', [])  

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
        if rating_value is not None and rating_value.isdigit():
            evaluation = int(rating_value)
            UserEvaluation.objects.update_or_create(
                user=self.request.user, 
                recipe=self.object,
                defaults={'evaluation': evaluation}
            )
            self.object.update_average_rating()  # 平均評価を更新
            
                        
class RecipeDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Recipe
    template_name = 'recipes/recipe_delete.html'
    success_url = reverse_lazy('recipes:my_recipe_list')
    success_message = "レシピが削除されました。"

    def get_queryset(self):
        # ユーザーが自分のレシピのみ削除できるようにする
        return super().get_queryset().filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recipe'] = self.object
        return context

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
                    return JsonResponse({'success': True})
                except Recipe.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Recipe not found'})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid request'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class RecipeListView(LoginRequiredMixin, ListView):
    model = Recipe
    template_name = 'recipe/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 10  # 1ページあたりのアイテム数

    def get_queryset(self):
        user = self.request.user
        # shareフィールドが1であるか、現在のユーザーが作成したレシピを表示
        return Recipe.objects.filter(models.Q(share=1) | models.Q(user=user)).order_by('-average_evaluation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context.get('page_obj')
        if page_obj:
            print(f"Current page: {page_obj.number}")
            print(f"Total pages: {page_obj.paginator.num_pages}")
        return context

def search(request):
    query = request.GET.get('q', '')
    filters = request.GET.getlist('filter', [])
    user = request.user

    from_edit_meal_plan = request.GET.get('from_edit_meal_plan', False)
    date = request.GET.get('date', '')
    meal_type = request.GET.get('meal_type', '')

    recipes = Recipe.objects.filter(models.Q(share=1) | models.Q(user=user))

    if query:
        recipes = recipes.filter(recipe_name__icontains=query)

    if 'my_recipe' in filters:
        recipes = recipes.filter(user=user)
    if 'three_star' in filters:
        recipes = recipes.filter(average_evaluation__gte=3)
    if 'staple' in filters:
        recipes = recipes.filter(menu_category=1)
    if 'main_dish' in filters:
        recipes = recipes.filter(menu_category=2)
    if 'side_dish' in filters:
        recipes = recipes.filter(menu_category=3)
    if 'soup' in filters:
        recipes = recipes.filter(menu_category=4)

    recipes = recipes.order_by('-average_evaluation')

    paginator = Paginator(recipes, 10)
    page = request.GET.get('page')

    try:
        recipes = paginator.page(page)
    except PageNotAnInteger:
        recipes = paginator.page(1)
    except EmptyPage:
        recipes = paginator.page(paginator.num_pages)

    context = {
        'recipes': recipes,
        'page_obj': recipes,
        'from_edit_meal_plan': from_edit_meal_plan,
        'date': date,
        'meal_type': meal_type,
        'request': request,
    }

    return render(request, 'recipes/recipe_list.html', context)

class RecipeDetailView(LoginRequiredMixin, DetailView):
    model = Recipe
    template_name = 'recipes/recipe_detail.html'
    context_object_name = 'recipe'
    
    def get_object(self, queryset=None):
        recipe = super().get_object(queryset)
        if not recipe.can_view(self.request.user):
            raise Http404("You do not have permission to view this recipe.")
        return recipe
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        user = self.request.user
        user_evaluation = UserEvaluation.objects.filter(user=self.request.user, recipe=recipe).first()
        
        adult_count = self.request.session.get('adult_count', user.adult_count)
        children_count = self.request.session.get('children_count', user.children_count)
        
        total_serving = adult_count + (children_count * 0.5)
        serving_ratio = total_serving / recipe.serving
        
        adjusted_ingredients = []
        for ingredient in recipe.ingredient_set.all():
            adjusted_quantity = adjust_quantity(ingredient.quantity_unit, serving_ratio)
            adjusted_ingredients.append({
                'name': ingredient.ingredient_name,
                'quantity': adjusted_quantity
            })
        
        context.update({
            'user_evaluation': user_evaluation,
            'adjusted_ingredients': adjusted_ingredients,
            'adult_count': adult_count,
            'children_count': children_count,
            'is_owner': recipe.user == user
        })
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

def adjust_quantity(quantity, ratio):
    def replace_quantity(match):
        original_quantity_str = match.group(0)
        try:
            if '/' in original_quantity_str:
                original_quantity = Fraction(original_quantity_str)
            else:
                original_quantity = float(original_quantity_str)
            adjusted_quantity = original_quantity * ratio
            rounded_quantity = round(adjusted_quantity, 1)  # 1桁まで丸める
            return f'{rounded_quantity:.1f}'
        except ValueError:
            return original_quantity_str

    pattern = r'(\d+/\d+|\d+\.\d+|\d+)'
    adjusted_quantity = re.sub(pattern, replace_quantity, quantity)
    return adjusted_quantity


