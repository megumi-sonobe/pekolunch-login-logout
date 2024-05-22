from django.contrib import admin
from .models import FoodCategory, Recipe, RecipeFoodCategory, Process, Ingredient, UserEvaluation

class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ('food_category_name', 'is_next_day_excluded', 'is_next_3_day_excluded')

class RecipeFoodCategoryInline(admin.TabularInline):
    model = RecipeFoodCategory
    extra = 1

class ProcessInline(admin.TabularInline):
    model = Process
    extra = 1

class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 1

class RecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe_name', 'user', 'menu_category', 'cooking_time_min', 'cooking_method', 'serving', 'average_evaluation')
    inlines = [RecipeFoodCategoryInline, ProcessInline, IngredientInline]

class UserEvaluationAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'evaluation', 'created_at')

admin.site.register(FoodCategory, FoodCategoryAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(UserEvaluation, UserEvaluationAdmin)
