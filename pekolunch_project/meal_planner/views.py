from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .forms import MealPlanForm
from datetime import timedelta
from .models import MealPlan


@login_required
def create_meal_plans(request):
    if request.method == 'POST':
        form  = MealPlanForm(request.POST)
        if form.is_valid():
            meal_date = form.cleaned_data['meal_date']
            
            for _ in range(7):
                
                if not MealPlan.objects.filter(user=request.user,meal_date=meal_date).exists():
                    meal_plan = form.save(commit=False)
                    meal_plan.user = request.user
                    meal_plan.save()
                    
                meal_date += timedelta(days=1)
                selected_date = form.cleaned_data['meal_date']
                    
            return redirect('meal_planner_edit', meal_date=(meal_date - timedelta(days=1)).strftime('%Y-%m-%d'))

    else:
        form = MealPlanForm()
        
    return render(request,'home.html',{'form':form})

            
            