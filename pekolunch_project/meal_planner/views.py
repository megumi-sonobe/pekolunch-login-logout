import random
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views import View
from django.http import HttpResponse,JsonResponse
from django.contrib import messages
from .models import Recipe,MealPlan

# class MealPlannerHomeView(LoginRequiredMixin, View):
#     def get(self, request):
#         print("Home view accessed")  # ビューにアクセスしたことを確認するメッセージ
#         if request.user.is_authenticated:
#             print(f"Logged in as: {request.user.username}")  # ユーザー名を出力
#         else:
#             print("User is not authenticated")
#         return render(request, 'home.html', {'username': request.user.username})

class CreateMealPlansView(LoginRequiredMixin, View):
    def post(self, request):
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if not start_date or not end_date:
            messages.error(request, "日付が選択されていません。")
            return redirect('accounts:home')
        
        print(f"Received start_date: {start_date}, end_date: {end_date}")

        start_date = datetime.date.fromisoformat(start_date)
        end_date = datetime.date.fromisoformat(end_date)
        user = request.user

        days = (end_date - start_date).days + 1
        date_list = [start_date + datetime.timedelta(days=x) for x in range(days)]

        for date in date_list:
            self.save_meal_plan(date, user)

        return redirect('meal_planner:edit_meal_plan', start_date=start_date, end_date=end_date)
    
    def get(self, request):
        return HttpResponse("不正なリクエストメソッドです", status=405)
    
    def save_meal_plan(self, date, user):
        if MealPlan.objects.filter(user=user, meal_date=date).exists():
            print(f"Meal Plan for {date} already exists")
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
            
            meal_plan = MealPlan.objects.create(
                user=user,
                staple_recipe=staple_recipe,
                main_recipe=main_recipe,
                side_recipe=side_recipe,
                meal_date=date
            )
            print(f"Saved Meal Plan: {meal_plan}")
            
class EditMealPlanView(LoginRequiredMixin, View):
    def get(self, request, start_date, end_date):
        start_date = datetime.date.fromisoformat(start_date)
        end_date = datetime.date.fromisoformat(end_date)

        print(f"Start Date: {start_date}, End Date: {end_date}")

        # デバッグ用にデータベースの内容を確認する
        for plan in MealPlan.objects.all():
            print(plan)

        meal_plans = MealPlan.objects.filter(user=request.user, meal_date__range=[start_date, end_date])
        print(f"Retrieved Meal Plans: {meal_plans}")

        formatted_meal_plans = []

        for plan in meal_plans:
            formatted_plan = {
                'date': self.format_date_with_weekday(plan.meal_date),
                'staple_recipe': plan.staple_recipe.recipe_name if plan.staple_recipe else '主食レシピが不足しています',
                'main_recipe': plan.main_recipe.recipe_name if plan.main_recipe else '主菜レシピが不足しています',
                'side_recipe': plan.side_recipe.recipe_name if plan.side_recipe else '副菜レシピが不足しています',
                'staple_recipe_id': plan.staple_recipe.id if plan.staple_recipe else None,
                'main_recipe_id': plan.main_recipe.id if plan.main_recipe else None,
                'side_recipe_id': plan.side_recipe.id if plan.side_recipe else None,
                'staple_recipe_image': plan.staple_recipe.image_url.url if plan.staple_recipe and plan.staple_recipe.image_url else None,
                'main_recipe_image': plan.main_recipe.image_url.url if plan.main_recipe and plan.main_recipe.image_url else None,
                'side_recipe_image': plan.side_recipe.image_url.url if plan.side_recipe and plan.side_recipe.image_url else None,
                'staple_recipe_evaluation': plan.staple_recipe.average_evaluation if plan.staple_recipe else None,
                'main_recipe_evaluation': plan.main_recipe.average_evaluation if plan.main_recipe else None,
                'side_recipe_evaluation': plan.side_recipe.average_evaluation if plan.side_recipe else None
            }
            formatted_meal_plans.append(formatted_plan)
            print(f"Formatted Meal Plan: {formatted_plan}")

        formatted_date_range = self.format_date_range(start_date, end_date)

        context = {
            'meal_plans': formatted_meal_plans,
            'date_range': formatted_date_range
        }
        return render(request, 'meal_planner/edit_meal_plan.html', context)

    def format_date_range(self, start_date, end_date):
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        start_formatted = f"{start_date.month}/{start_date.day}（{weekdays[start_date.weekday()]}）"
        end_formatted = f"{end_date.month}/{end_date.day}（{weekdays[end_date.weekday()]}）"
        if start_date == end_date:
            return start_formatted
        return f"{start_formatted} 〜 {end_formatted}"
    
    
    def format_date_with_weekday(self, date):
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        formatted_date = f"{date.month}/{date.day}（{weekdays[date.weekday()]}）"
        # デバッグ: フォーマットされた日付を出力
        print(f"Formatted Date: {formatted_date}")
        return formatted_date

    def get_selected_recipes(self, date, user):
        staple_recipes = Recipe.objects.filter(
            models.Q(menu_category=1) & (models.Q(share=1) | models.Q(user=user))
        )
        main_recipes = Recipe.objects.filter(
            models.Q(menu_category=2) & (models.Q(share=1) | models.Q(user=user))
        )
        side_recipes = Recipe.objects.filter(
            models.Q(menu_category=3) & (models.Q(share=1) | models.Q(user=user))
        )
        
        # デバッグ: 各カテゴリのレシピ数を出力
        print(f"Staple recipes count: {staple_recipes.count()}")
        print(f"Main recipes count: {main_recipes.count()}")
        print(f"Side recipes count: {side_recipes.count()}")

        if not (staple_recipes.exists() and main_recipes.exists() and side_recipes.exists()):
            return {
                'date': self.format_date_with_weekday(date), 
                'staple_recipe': '主食レシピが不足しています',
                'main_recipe': '主菜レシピが不足しています',
                'side_recipe': '副菜レシピが不足しています'
            }

        selected_recipes = {
            'date': self.format_date_with_weekday(date), 
            'staple_recipe': random.choice(staple_recipes),
            'main_recipe': random.choice(main_recipes),
            'side_recipe': random.choice(side_recipes)
        }
        
        # デバッグ: 選択されたレシピの内容を出力
        print(f"Selected Recipes on {date}: {selected_recipes}")
    
        return selected_recipes
    
class MealPlanDatesView(LoginRequiredMixin, View):
    def get(self, request):
        meal_plans = MealPlan.objects.filter(user=request.user).values('meal_date')
        dates = [meal_plan['meal_date'] for meal_plan in meal_plans]
        return JsonResponse(dates, safe=False)