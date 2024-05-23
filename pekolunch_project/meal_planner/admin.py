from django.contrib import admin
from .models import MealPlan

class MealPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'meal_date', 'staple_recipe', 'main_recipe', 'side_recipe', 'soup_recipe', 'created_at', 'updated_at')
    list_filter = ('meal_date', 'user')
    search_fields = ('user__username', 'staple_recipe__recipe_name', 'main_recipe__recipe_name', 'side_recipe__recipe_name', 'soup_recipe__recipe_name')
    date_hierarchy = 'meal_date'
    ordering = ('-meal_date',)
    actions = ['delete_selected']

admin.site.register(MealPlan, MealPlanAdmin)
