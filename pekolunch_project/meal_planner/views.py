import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Recipe
from django.http import HttpResponse
from django.contrib import messages
import datetime

@login_required
def home(request):
    print("Home view accessed")  # ビューにアクセスしたことを確認するメッセージ
    if request.user.is_authenticated:
        print(f"Logged in as: {request.user.username}")  # ユーザー名を出力
    else:
        print("User is not authenticated")
    return render(request, 'home.html', {'username': request.user.username})


@login_required
def create_meal_plans(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if not start_date or not end_date:
            messages.error(request,"日付が選択されていません。")
            return redirect('accounts:home')
        
        # デバッグ用のログを追加
        print(f"Received start_date: {start_date}, end_date: {end_date}")

        return redirect('meal_planner:edit_meal_plan', start_date=start_date, end_date=end_date)
    else:
        return HttpResponse("不正なリクエストメソッドです", status=405)

@login_required
def edit_meal_plan(request, start_date, end_date):
    start_date = datetime.date.fromisoformat(start_date)
    end_date = datetime.date.fromisoformat(end_date)

    # デバッグ用のログを追加
    print(f"Start Date: {start_date}, End Date: {end_date}")

    start_date_formatted = format_date_with_weekday(start_date)
    end_date_formatted = format_date_with_weekday(end_date)
    
    selected_recipes = get_selected_recipes(start_date, end_date)

    context = {
        'start_date': start_date_formatted,
        'end_date': end_date_formatted,
        'selected_recipes': selected_recipes
    }
    return render(request, 'meal_planner/edit_meal_plan.html', context)

def format_date_with_weekday(date):
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    return f"{date.month}/{date.day}（{weekdays[date.weekday()]}）"

def get_selected_recipes(start_date, end_date):
    # 各カテゴリのレシピを取得
    staple_recipes = Recipe.objects.filter(menu_category=1)  # 主食
    main_recipes = Recipe.objects.filter(menu_category=2)    # 主菜
    side_recipes = Recipe.objects.filter(menu_category=3)    # 副菜
    soup_recipes = Recipe.objects.filter(menu_category=4)    # 汁物

    # 各カテゴリのレシピが存在することを確認
    if not (staple_recipes.exists() and main_recipes.exists() and side_recipes.exists() and soup_recipes.exists()):
        return []

    # 各カテゴリからランダムに1つずつ選択
    selected_recipes = {
        'staple_recipe': random.choice(staple_recipes),
        'main_recipe': random.choice(main_recipes),
        'side_recipe': random.choice(side_recipes),
        'soup_recipe': random.choice(soup_recipes)
    }
    return selected_recipes
