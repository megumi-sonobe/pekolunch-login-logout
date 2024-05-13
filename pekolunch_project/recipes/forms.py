from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import Recipe,RecipeFoodCategory,Process,Ingredient,FoodCategory
from choices import COOKING_TIME_CHOICES,COOKING_METHOD_CHOICES,MENU_CHOICES
from meal_planner.service import load_food_categories_from_csv
from typing import Tuple
import csv


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='CSVファイル')

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        # CSVファイルのバリデーションを追加する場合はここに記述
        return csv_file
    
    def load_food_categories(self):
        csv_file_path = self.cleaned_data['csv_file'].temporary_file_path()
        return load_food_categories_from_csv(csv_file_path)

class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ['description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].label = ''  # ステップの説明フィールドのラベルを空にする

    def save(self, commit=True):
        process = super().save(commit=False)
        if not process.pk:  # 新しいプロセスの場合のみ
            recipe = self.instance.recipe
            last_process = Process.objects.filter(recipe=recipe).order_by('-process_number').first()
            if last_process:
                process.process_number = last_process.process_number + 1
        if commit:
            process.save()
        return process

    
class IngredientForm(forms.ModelForm):
    serving = forms.IntegerField(label='',min_value=1)
    
    class Meta:
        model = Ingredient
        fields = ['ingredient_name','quantity_unit']
        
    def save(self,commit=True):
        ingredient = super().save(commit=False)
        if commit:
            ingredient.save()
            
            serving = self.cleaned_data.get('serving',1)
            ingredient.adjust_quantity_for_serving(serving)
            
        return ingredient        

class RecipeForm(forms.ModelForm):
    csv_file_path = None
    recipe_name = forms.CharField(label='レシピ名', max_length=32)
    menu_category = forms.ChoiceField(choices=MENU_CHOICES, label='カテゴリー')
    cooking_time_min = forms.ChoiceField(choices=COOKING_TIME_CHOICES, label='調理時間')
    cooking_method = forms.ChoiceField(choices=COOKING_METHOD_CHOICES, label='調理法')
    image_url = forms.ImageField(label='画像', required=False)
    serving = forms.IntegerField(label='人分', min_value=1)
    share = forms.BooleanField(label='全体にシェアする')
    is_avoid_main_dish = forms.BooleanField(label='主菜不要')
    process_description = forms.CharField(label='作り方', widget=forms.Textarea)
    ingredient_name = forms.CharField(label='材料', max_length=64)
    
    class Meta:
        model = Recipe
        fields = ['recipe_name','menu_category', 'cooking_time_min', 
                  'cooking_method', 'image_url', 'serving', 'share',
                  'is_avoid_main_dish', 'average_evaluation']
    
    def __init__(self, *args, csv_file_path=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['average_evaluation'].widget = forms.HiddenInput()
        self.fields['share'].initial = True
        self.fields['is_avoid_main_dish'].initial = False
        
        if csv_file_path:
            food_categories = self.load_food_categories(csv_file_path)
            if food_categories:
                self.fields['food_categories'] = forms.ModelMultipleChoiceField(
                    queryset=food_categories,
                    label='主な使用食材（5つまで選択）:',
                    required=False,
                    initial=[],
                    widget=forms.CheckboxSelectMultiple,
                )

    def save(self, commit=True):
        recipe = super().save(commit=False)
        process = None
        ingredient = None
    
        if commit:
            serving = self.cleaned_data.get('serving', 1)
            recipe.adjust_ingredient_quantity_for_serving(serving)
            
            process_description = self.cleaned_data.get('process_description', '')
            ingredient_name = self.cleaned_data.get('ingredient_name', '')
            
            process = Process.objects.create(recipe=recipe, description=process_description)
            ingredient = Ingredient.objects.create(recipe=recipe, ingredient_name=ingredient_name)
            
            food_categories = self.load_food_categories(self.csv_file_path)
            recipe.food_categories.set(food_categories)
            
            recipe.save()
               
            process.save()
            ingredient.save()
            
            recipe.adjust_ingredient_quantity_for_serving(serving)
    
        return recipe, process, ingredient

    def load_food_categories(self, csv_file_path):
        food_categories = FoodCategory.objects.none()
        if csv_file_path:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                for row in reader:
                    category_name = row[0].strip()
                    if category_name:
                        food_category, created = FoodCategory.objects.get_or_create(food_category_name=category_name)
                        food_categories = FoodCategory.objects.all()
        return food_categories
