from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import MealPlanForm
from datetime import timedelta
from .models import MealPlan
from .service import get_eligible_recipes, apply_rules

@login_required
def create_meal_plans(request):
    if request.method == 'POST':
        form = MealPlanForm(request.POST)
        if form.is_valid():
            meal_date = form.cleaned_data['meal_date']
            
            # 適切なレシピを取得
            previous_meal_plans = MealPlan.objects.filter(user=request.user, meal_date__lt=meal_date)
            eligible_recipes = get_eligible_recipes(request.user, previous_meal_plans)
            eligible_recipes = apply_rules(eligible_recipes, meal_date, request.user)
            
            # レシピをMealPlanに保存
            for recipe in eligible_recipes:
                if not MealPlan.objects.filter(user=request.user, meal_date=meal_date, recipe=recipe).exists():
                    meal_plan = MealPlan.objects.create(user=request.user, meal_date=meal_date, recipe=recipe)
                    
            # 7日後の日付にリダイレクト
            return redirect('meal_planner_edit', meal_date=(meal_date + timedelta(days=7)).strftime('%Y-%m-%d'))

    else:
        form = MealPlanForm()
        
    return render(request, 'home.html', {'form': form})
