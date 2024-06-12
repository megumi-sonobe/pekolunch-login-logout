import random
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .models import MealPlan
from recipes.models import Recipe, FoodCategory 
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.generic import ListView
from django.shortcuts import get_object_or_404


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

        no_recipes_found = False

        for date in date_list:
            print(f"Processing date: {date}")
            if not self.save_meal_plan(date, user):
                no_recipes_found = True

        if no_recipes_found:
            messages.error(request, "ルールに当てはまるレシピが見つかりませんでした。マイレシピを登録してみましょう！")
        else:
            messages.success(request, "献立が正常に作成されました。")

        url = reverse('meal_planner:edit_meal_plan', kwargs={'start_date': start_date, 'end_date': end_date})
        return redirect(f"{url}?view_mode=custom")

    def get(self, request):
        return HttpResponse("不正なリクエストメソッドです", status=405)

    def save_meal_plan(self, date, user):
        print(f"Saving meal plan for date: {date}")

        if MealPlan.objects.filter(user=user, meal_date=date).exists():
            print(f"Meal plan already exists for date: {date}")
            return True

        max_cooking_time = user.cooking_time_min

        staple_recipes = list(Recipe.objects.filter(
            menu_category=1, cooking_time_min__lte=max_cooking_time
        ).filter(models.Q(share=1) | models.Q(user=user)).annotate(
            user_rating=models.Case(
                models.When(user_evaluations__user=user, user_evaluations__evaluation=3, then=3),
                default=0,
                output_field=models.IntegerField(),
            )
        ).order_by('-user_rating', '-average_evaluation'))

        main_recipes = list(Recipe.objects.filter(
            menu_category=2, cooking_time_min__lte=max_cooking_time
        ).filter(models.Q(share=1) | models.Q(user=user)).annotate(
            user_rating=models.Case(
                models.When(user_evaluations__user=user, user_evaluations__evaluation=3, then=3),
                default=0,
                output_field=models.IntegerField(),
            )
        ).order_by('-user_rating', '-average_evaluation'))

        side_recipes = list(Recipe.objects.filter(
            menu_category=3, cooking_time_min__lte=max_cooking_time
        ).filter(models.Q(share=1) | models.Q(user=user)).annotate(
            user_rating=models.Case(
                models.When(user_evaluations__user=user, user_evaluations__evaluation=3, then=3),
                default=0,
                output_field=models.IntegerField(),
            )
        ).order_by('-user_rating', '-average_evaluation'))

        staple_recipes.extend(Recipe.objects.filter(
            menu_category=1, cooking_time_min__lte=max_cooking_time
        ).filter(models.Q(share=1) | models.Q(user=user)).filter(user_evaluations__isnull=True))

        main_recipes.extend(Recipe.objects.filter(
            menu_category=2, cooking_time_min__lte=max_cooking_time
        ).filter(models.Q(share=1) | models.Q(user=user)).filter(user_evaluations__isnull=True))

        side_recipes.extend(Recipe.objects.filter(
            menu_category=3, cooking_time_min__lte=max_cooking_time
        ).filter(models.Q(share=1) | models.Q(user=user)).filter(user_evaluations__isnull=True))

        # ご飯の出現率を高める
        rice_recipe = Recipe.objects.get(id=144)
        staple_recipes += [rice_recipe] * 40  # ご飯のレシピを40回追加することで出現率を高める

        recent_meal_plans = MealPlan.objects.filter(user=user, meal_date__gte=date - datetime.timedelta(days=14))

        if staple_recipes and side_recipes:
            random.shuffle(staple_recipes)
            random.shuffle(main_recipes)
            random.shuffle(side_recipes)

            for staple_recipe in staple_recipes:
                if self.is_recently_used(recent_meal_plans, staple_recipe):
                    continue

                staple_categories = set(staple_recipe.food_categories.values_list('id', flat=True))
                if staple_recipe.is_avoid_main_dish == 1:
                    for side_recipe in side_recipes:
                        if self.is_recently_used(recent_meal_plans, side_recipe):
                            continue

                        side_categories = set(side_recipe.food_categories.values_list('id', flat=True))
                        if (side_recipe.cooking_method != staple_recipe.cooking_method and
                                self.check_exclusion_rules(date, user, staple_categories, side_categories) and
                                self.check_same_day_categories(date, user, staple_categories, side_categories)):
                            MealPlan.objects.create(
                                user=user,
                                staple_recipe=staple_recipe,
                                main_recipe=None,
                                side_recipe=side_recipe,
                                meal_date=date
                            )
                            print(f"Meal plan created with staple {staple_recipe.recipe_name}, side {side_recipe.recipe_name} for date: {date}")
                            print(f"Categories for date {date}: staple {staple_categories}, side {side_categories}")
                            self.print_food_category_names(staple_recipe, side_recipe)
                            return True
                else:
                    for main_recipe in main_recipes:
                        if self.is_recently_used(recent_meal_plans, main_recipe):
                            continue

                        main_categories = set(main_recipe.food_categories.values_list('id', flat=True))
                        if (main_recipe.cooking_method != staple_recipe.cooking_method and
                                self.check_exclusion_rules(date, user, staple_categories, main_categories) and
                                self.check_same_day_categories(date, user, staple_categories, main_categories)):
                            for side_recipe in side_recipes:
                                if self.is_recently_used(recent_meal_plans, side_recipe):
                                    continue

                                side_categories = set(side_recipe.food_categories.values_list('id', flat=True))
                                if (side_recipe.cooking_method != staple_recipe.cooking_method and
                                        side_recipe.cooking_method != main_recipe.cooking_method and
                                        self.check_exclusion_rules(date, user, staple_categories, side_categories, main_categories) and
                                        self.check_same_day_categories(date, user, staple_categories, main_categories, side_categories)):
                                    MealPlan.objects.create(
                                        user=user,
                                        staple_recipe=staple_recipe,
                                        main_recipe=main_recipe,
                                        side_recipe=side_recipe,
                                        meal_date=date
                                    )
                                    print(f"Meal plan created with staple {staple_recipe.recipe_name}, main {main_recipe.recipe_name}, side {side_recipe.recipe_name} for date: {date}")
                                    print(f"Categories for date {date}: staple {staple_categories}, main {main_categories}, side {side_categories}")
                                    self.print_food_category_names(staple_recipe, main_recipe, side_recipe)
                                    return True
        print(f"No meal plan created for date: {date}")
        return False

    def print_food_category_names(self, staple_recipe, main_recipe=None, side_recipe=None):
        def get_category_names(recipe):
            return [category.food_category_name for category in recipe.food_categories.all()]

        print(f"Staple categories: {get_category_names(staple_recipe)}")
        if main_recipe:
            print(f"Main categories: {get_category_names(main_recipe)}")
        if side_recipe:
            print(f"Side categories: {get_category_names(side_recipe)}")

    def check_exclusion_rules(self, date, user, *category_sets):
        for categories in category_sets:
            for category_id in categories:
                try:
                    category = FoodCategory.objects.get(id=category_id)
                    if self.is_excluded(date, user, category):
                        print(f"Excluding category: {category.food_category_name}")
                        return False
                except FoodCategory.DoesNotExist:
                    continue
        return True

    def get_last_used_date(self, user, category_id):
        last_used_dates = MealPlan.objects.filter(
            user=user
        ).filter(
            models.Q(staple_recipe__food_categories__id=category_id) |
            models.Q(main_recipe__food_categories__id=category_id) |
            models.Q(side_recipe__food_categories__id=category_id)
        ).values_list('meal_date', flat=True).order_by('-meal_date')

        return last_used_dates.first() if last_used_dates.exists() else None
    
    def is_excluded(self, date, user, category):
        next_day = date + datetime.timedelta(days=1)
        three_days_ago = date - datetime.timedelta(days=3)

        # 翌日を除外するカテゴリーが前日に使用されている場合
        if category.is_next_day_excluded and self.is_category_used(date - datetime.timedelta(days=1), user, category.id):
            return True

        # 3日間を除外するカテゴリーが最後に使用された日から3日以内に使用されている場合
        if category.is_next_3_day_excluded:
            for day in range(1, 4):
                check_date = date - datetime.timedelta(days=day)
                if self.is_category_used(check_date, user, category.id):
                    return True

        return False

    def is_category_used(self, date, user, category_id):
        meal_plans = MealPlan.objects.filter(user=user, meal_date=date)
        for meal_plan in meal_plans:
            if meal_plan.staple_recipe and category_id in meal_plan.staple_recipe.food_categories.values_list('id', flat=True):
                return True
            if meal_plan.main_recipe and category_id in meal_plan.main_recipe.food_categories.values_list('id', flat=True):
                return True
            if meal_plan.side_recipe and category_id in meal_plan.side_recipe.food_categories.values_list('id', flat=True):
                return True
        return False

    def check_same_day_categories(self, date, user, *category_sets):
        all_new_categories = set()
        for categories in category_sets:
            all_new_categories.update(categories)

        print(f"New categories for {date}: {all_new_categories}")

        # 新しいカテゴリ同士で重複がないことを確認する
        new_categories_combined = set()
        for categories in category_sets:
            if not new_categories_combined.isdisjoint(categories):
                print(f"Duplicate found within new categories on {date}")
                return False
            new_categories_combined.update(categories)

        return True

    def is_recently_used(self, recent_meal_plans, recipe):
        if recipe.id == 144:  # ご飯のレシピIDを特別扱い
            return False
        for meal_plan in recent_meal_plans:
            if (meal_plan.staple_recipe and meal_plan.staple_recipe.id == recipe.id) or \
               (meal_plan.main_recipe and meal_plan.main_recipe.id == recipe.id) or \
               (meal_plan.side_recipe and meal_plan.side_recipe.id == recipe.id):
                print(f"Recently used recipe: {recipe.recipe_name}")
                return True
        return False


    
    
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

        previous_week_start = start_date - datetime.timedelta(days=7)
        previous_week_end = end_date - datetime.timedelta(days=7)
        next_week_start = start_date + datetime.timedelta(days=7)
        next_week_end = end_date + datetime.timedelta(days=7)

        context = {
            'meal_plans': formatted_meal_plans,
            'date_range': formatted_date_range,
            'view_mode': view_mode,
            'previous_week_start': previous_week_start,
            'previous_week_end': previous_week_end,
            'next_week_start': next_week_start,
            'next_week_end': next_week_end,
        }
        return render(request, 'meal_planner/edit_meal_plan.html', context)

    def format_plan(self, plan, date):
        def get_evaluation(recipe):
            if not recipe or recipe.average_evaluation == 0.0:
                return '評価なし'
            return recipe.average_evaluation

        if plan:
            return {
                'date': date,
                'staple_recipe': plan.staple_recipe.recipe_name if plan.staple_recipe else '献立なし',
                'main_recipe': plan.main_recipe.recipe_name if plan.main_recipe else '献立なし',
                'side_recipe': plan.side_recipe.recipe_name if plan.side_recipe else '献立なし',
                'soup_recipe': plan.soup_recipe.recipe_name if plan.soup_recipe else '献立なし',  #
                'staple_recipe_id': plan.staple_recipe.id if plan.staple_recipe else None,
                'main_recipe_id': plan.main_recipe.id if plan.main_recipe else None,
                'side_recipe_id': plan.side_recipe.id if plan.side_recipe else None,
                'soup_recipe_id': plan.soup_recipe.id if plan.soup_recipe else None,  
                'staple_recipe_image': plan.staple_recipe.image_url.url if plan.staple_recipe and plan.staple_recipe.image_url else None,
                'main_recipe_image': plan.main_recipe.image_url.url if plan.main_recipe and plan.main_recipe.image_url else None,
                'side_recipe_image': plan.side_recipe.image_url.url if plan.side_recipe and plan.side_recipe.image_url else None,
                'soup_recipe_image': plan.soup_recipe.image_url.url if plan.soup_recipe and plan.soup_recipe.image_url else None,  
                'staple_recipe_evaluation': get_evaluation(plan.staple_recipe),
                'main_recipe_evaluation': get_evaluation(plan.main_recipe),
                'side_recipe_evaluation': get_evaluation(plan.side_recipe),
                'soup_recipe_evaluation': get_evaluation(plan.soup_recipe)  
            }
        else:
            return {
                'date': date,
                'staple_recipe': '献立なし',
                'main_recipe': '献立なし',
                'side_recipe': '献立なし',
                'soup_recipe': '献立なし', 
                'staple_recipe_id': None,
                'main_recipe_id': None,
                'side_recipe_id': None,
                'soup_recipe_id': None,  
                'staple_recipe_image': None,
                'main_recipe_image': None,
                'side_recipe_image': None,
                'soup_recipe_image': None,  
                'staple_recipe_evaluation': None,
                'main_recipe_evaluation': None,
                'side_recipe_evaluation': None,
                'soup_recipe_evaluation': None 
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
        elif meal_type == 'soup': 
            return Recipe.objects.filter(menu_category=4).order_by('-average_evaluation')
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

def update_recipe(request):
    # レシピの更新処理
    # ...
    return redirect(reverse('meal_planner:weekly_meal_plan', kwargs={'date': request.GET.get('date')}))

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
        elif meal_type == 'soup':  # 新しい汁物のフィールド
            meal_plan.soup_recipe = recipe

        meal_plan.save()
        messages.success(request, "献立が更新されました。")
    except Recipe.DoesNotExist:
        messages.error(request, "指定されたレシピが存在しません。")

    # 更新後に週間献立ページにリダイレクト
    start_date = (meal_date - datetime.timedelta(days=meal_date.weekday())).strftime('%Y-%m-%d')
    end_date = (meal_date + datetime.timedelta(days=6 - meal_date.weekday())).strftime('%Y-%m-%d')

    return redirect('meal_planner:edit_meal_plan', start_date=start_date, end_date=end_date)

@login_required
def remove_recipe(request):
    if request.method == 'POST':
        meal_date_str = request.POST.get('meal_date')
        meal_type = request.POST.get('meal_type')

        if not meal_date_str or not meal_type:
            messages.error(request, "無効なリクエストです。")
            return redirect('meal_planner:weekly_meal_plan')

        try:
            meal_date = datetime.datetime.strptime(meal_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "無効な日付形式です。")
            return redirect('meal_planner:weekly_meal_plan')

        try:
            meal_plan = MealPlan.objects.get(user=request.user, meal_date=meal_date)
            if meal_type == 'staple':
                meal_plan.staple_recipe = None
            elif meal_type == 'main':
                meal_plan.main_recipe = None
            elif meal_type == 'side':
                meal_plan.side_recipe = None
            elif meal_type == 'soup':
                meal_plan.soup_recipe = None
            meal_plan.save()
            messages.success(request, "料理が削除されました。")
        except MealPlan.DoesNotExist:
            messages.error(request, "指定された献立が存在しません。")

        start_date = (meal_date - datetime.timedelta(days=meal_date.weekday())).strftime('%Y-%m-%d')
        end_date = (meal_date + datetime.timedelta(days=6 - meal_date.weekday())).strftime('%Y-%m-%d')

        return redirect('meal_planner:edit_meal_plan', start_date=start_date, end_date=end_date)
    else:
        messages.error(request, "無効なリクエストです。")
        return redirect('meal_planner:weekly_meal_plan')

@login_required
def meal_plan_events(request):
    user = request.user
    meal_plans = MealPlan.objects.filter(user=user)
    events = []

    for plan in meal_plans:
        title = []
        if plan.staple_recipe:
            title.append(plan.staple_recipe.recipe_name)
        if plan.main_recipe:
            title.append(plan.main_recipe.recipe_name)
        if plan.side_recipe:
            title.append(plan.side_recipe.recipe_name)
        if plan.soup_recipe:
            title.append(plan.soup_recipe.recipe_name)

        events.append({
            'title': ' | '.join(title) if title else '献立なし',
            'start': plan.meal_date.isoformat(),
            'allDay': True
        })

    return JsonResponse(events, safe=False)