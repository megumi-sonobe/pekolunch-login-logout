import random
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .models import Recipe, MealPlan
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.generic import ListView

class CreateMealPlansView(LoginRequiredMixin, View):
    def post(self, request):
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if not start_date or not end_date:
            messages.error(request, "日付が選択されていません。")
            return redirect('accounts:home')

        start_date = datetime.date.fromisoformat(start_date)
        end_date = datetime.date.fromisoformat(end_date)
        user = request.user

        days = (end_date - start_date).days + 1
        date_list = [start_date + datetime.timedelta(days=x) for x in range(days)]

        for date in date_list:
            self.save_meal_plan(date, user)

        url = reverse('meal_planner:edit_meal_plan', kwargs={'start_date': start_date, 'end_date': end_date})
        return redirect(f"{url}?view_mode=custom")
    
    def get(self, request):
        return HttpResponse("不正なリクエストメソッドです", status=405)
    
    def save_meal_plan(self, date, user):
        if MealPlan.objects.filter(user=user, meal_date=date).exists():
            return
        
        staple_recipes = Recipe.objects.filter(
            models.Q(menu_category=1) & (models.Q(share=1) | models.Q(user=user))
        )
        main_recipes = Recipe.objects.filter(
            models.Q(menu_category=2) & (models.Q(share=1) | models.Q(user=user))
        )
        side_recipes = Recipe.objects.filter(
            models.Q(menu_category=3) & (models.Q(share=1) | models.Q(user=user))
        )

        if staple_recipes.exists() and main_recipes.exists() and side_recipes.exists():
            staple_recipe = random.choice(staple_recipes)
            main_recipe = random.choice(main_recipes)
            side_recipe = random.choice(side_recipes)
            
            MealPlan.objects.create(
                user=user,
                staple_recipe=staple_recipe,
                main_recipe=main_recipe,
                side_recipe=side_recipe,
                meal_date=date
            )

class EditMealPlanView(LoginRequiredMixin, View):
    def get(self, request, start_date, end_date):
        start_date = datetime.date.fromisoformat(start_date)
        end_date = datetime.date.fromisoformat(end_date)
        view_mode = request.GET.get('view_mode', 'weekly')

        user = request.user
        date_list = [start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        
        meal_plans = MealPlan.objects.filter(user=user, meal_date__range=[start_date, end_date]).order_by('meal_date')
        meal_plan_dict = {plan.meal_date: plan for plan in meal_plans}

        formatted_meal_plans = [self.format_plan(meal_plan_dict.get(date), date) for date in date_list]
        formatted_date_range = self.format_date_range(start_date, end_date)

        context = {
            'meal_plans': formatted_meal_plans,
            'date_range': formatted_date_range,
            'view_mode': view_mode
        }
        return render(request, 'meal_planner/edit_meal_plan.html', context)

    def format_plan(self, plan, date):
        def get_evaluation(recipe):
            if not recipe or recipe.average_evaluation == 0.0:
                return '評価なし'
            return recipe.average_evaluation

        if plan:
            return {
                'date': date,  # 日付を直接渡す
                'staple_recipe': plan.staple_recipe.recipe_name if plan.staple_recipe else '献立なし',
                'main_recipe': plan.main_recipe.recipe_name if plan.main_recipe else '献立なし',
                'side_recipe': plan.side_recipe.recipe_name if plan.side_recipe else '献立なし',
                'staple_recipe_id': plan.staple_recipe.id if plan.staple_recipe else None,
                'main_recipe_id': plan.main_recipe.id if plan.main_recipe else None,
                'side_recipe_id': plan.side_recipe.id if plan.side_recipe else None,
                'staple_recipe_image': plan.staple_recipe.image_url.url if plan.staple_recipe and plan.staple_recipe.image_url else None,
                'main_recipe_image': plan.main_recipe.image_url.url if plan.main_recipe and plan.main_recipe.image_url else None,
                'side_recipe_image': plan.side_recipe.image_url.url if plan.side_recipe and plan.side_recipe.image_url else None,
                'staple_recipe_evaluation': get_evaluation(plan.staple_recipe),
                'main_recipe_evaluation': get_evaluation(plan.main_recipe),
                'side_recipe_evaluation': get_evaluation(plan.side_recipe)
            }
        else:
            return {
                'date': date,  # 日付を直接渡す
                'staple_recipe': '献立なし',
                'main_recipe': '献立なし',
                'side_recipe': '献立なし',
                'staple_recipe_id': None,
                'main_recipe_id': None,
                'side_recipe_id': None,
                'staple_recipe_image': None,
                'main_recipe_image': None,
                'side_recipe_image': None,
                'staple_recipe_evaluation': None,
                'main_recipe_evaluation': None,
                'side_recipe_evaluation': None
            }

    def format_date_range(self, start_date, end_date):
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        start_formatted = f"{start_date.month}/{start_date.day}（{weekdays[start_date.weekday()]}）"
        end_formatted = f"{end_date.month}/{end_date.day}（{weekdays[end_date.weekday()]}）"
        if start_date == end_date:
            return start_formatted
        return f"{start_formatted} 〜 {end_formatted}"


class MealPlanDatesView(LoginRequiredMixin, View):
    def get(self, request):
        meal_plans = MealPlan.objects.filter(user=request.user).values('meal_date')
        dates = [meal_plan['meal_date'] for meal_plan in meal_plans]
        return JsonResponse(dates, safe=False)

class WeeklyMealPlanView(LoginRequiredMixin, View):
    def get(self, request):
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(days=6)  # 今日から1週間の範囲
        return redirect(f'/meal_planner/edit_meal_plan/{start_date}/{end_date}/?view_mode=weekly')

class MealPlannerRecipeListView(LoginRequiredMixin, ListView):
    model = Recipe
    template_name = 'meal_planner/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 10  # 1ページあたりのアイテム数

    def get_queryset(self):
        meal_type = self.request.GET.get('meal_type')
        if meal_type == 'staple':
            return Recipe.objects.filter(menu_category=1).order_by('-average_evaluation')
        elif meal_type == 'main':
            return Recipe.objects.filter(menu_category=2).order_by('-average_evaluation')
        elif meal_type == 'side':
            return Recipe.objects.filter(menu_category=3).order_by('-average_evaluation')
        else:
            return Recipe.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date'] = self.request.GET.get('date')
        context['meal_type'] = self.request.GET.get('meal_type')
        context['from_edit_meal_plan'] = self.request.GET.get('from_edit_meal_plan')
        page_obj = context.get('page_obj')
        if page_obj:
            print(f"Current page: {page_obj.number}")
            print(f"Total pages: {page_obj.paginator.num_pages}")
        return context
    
@login_required
@require_POST
def select_recipe(request):
    recipe_id = request.POST.get('recipe_id')
    date_str = request.POST.get('date')
    meal_type = request.POST.get('meal_type')

    try:
        meal_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "無効な日付形式です。")
        return redirect('meal_planner:edit_meal_plan', start_date=date_str, end_date=date_str)

    try:
        recipe = Recipe.objects.get(id=recipe_id)
        meal_plan, created = MealPlan.objects.get_or_create(user=request.user, meal_date=meal_date)

        if meal_type == 'staple':
            meal_plan.staple_recipe = recipe
        elif meal_type == 'main':
            meal_plan.main_recipe = recipe
        elif meal_type == 'side':
            meal_plan.side_recipe = recipe

        meal_plan.save()
        messages.success(request, "レシピが更新されました。")
    except Recipe.DoesNotExist:
        messages.error(request, "指定されたレシピが存在しません。")

    start_date = meal_date.strftime('%Y-%m-%d')
    end_date = meal_date.strftime('%Y-%m-%d')
    
    return redirect('meal_planner:edit_meal_plan', start_date=start_date, end_date=end_date)
